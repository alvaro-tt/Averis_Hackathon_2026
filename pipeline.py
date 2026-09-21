"""
pipeline.py — runs the whole thing: classify -> read documents -> extract -> compare.

  python pipeline.py data_v2                     # full run (AI on, OCR for scans)
  python pipeline.py data_v2 --no-ai             # rules + OCR only, no AI calls
  python pipeline.py data_v2 --retry             # re-run ONLY emails that failed
                                                 #   retryably (AI quota, network...)
  python pipeline.py http://localhost:8080 --submit

Outputs (in --out, default "."):
  submission.json        the system's answer, exactly the sample_submission shape
  review_queue.json      every case a human should look at, with reason + evidence
  results.json           full per-email records (for the frontend / debugging)
  final_submission.json  submission + human decisions (see review.py)
  report.md              readable discrepancy report

For the frontend: process_one(email, inbox) handles one email and returns the
same record that goes into results.json.

Environment:
  SDOC_EXTRACTION_MODE  ai (default) | auto | rules     see document_reader.py
  SDOC_OCR_POLICY       review (default) | trust        see extraction.py
  SDOC_DISABLE_AI=1     no AI calls at all
  SDOC_CACHE_DIR        OCR/AI cache folder (default .sdoc_cache)
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from loader import Inbox
import classify
import compare
import review
from extraction import process_email

NON_COMPARISON_ENTRY = {"status": "OK", "review_reason": None,
                        "defect_fields": [], "has_defect": False}
_RETRYABLE_CLASSIFY = {"ai_rate_limited", "ai_call_failed", "ai_unexpected_response", "ai_unavailable"}


def process_one(email, inbox):
    """Classify one email and, if it's a comparison request, read + compare.
    Never raises. Returns a JSON-serialisable dict."""
    email_id = email.get("email_id") if isinstance(email, dict) else None
    record = {"email_id": email_id,
              "subject": email.get("subject") if isinstance(email, dict) else None,
              "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        meta = classify.classify_email_with_meta(email)
        record["classification"] = meta
        category = meta["category"]
        retryable = meta.get("review_reason") in _RETRYABLE_CLASSIFY

        if category == "BL_COMPARISON":
            extraction = process_email(email, inbox)
            report = compare.build_report(extraction)
            record["report"] = report
            record["summary"] = compare.render_summary(report)
            record["submission"] = compare.build_submission_entry(report)
            retryable = retryable or bool(extraction.get("retryable"))
        else:
            record["submission"] = {"category": category, **NON_COMPARISON_ENTRY}
            record["summary"] = f"{email_id}: {category}"

        record["retryable"] = retryable
        record["needs_review"] = (meta["needs_review"]
                                  or record["submission"]["status"] == "NEEDS_REVIEW")
    except Exception as e:  # one bad email must never stop the batch
        record["error"] = f"{type(e).__name__}: {e}"
        record["submission"] = {"category": "GENERAL", **NON_COMPARISON_ENTRY}
        record["summary"] = f"{email_id}: pipeline error ({type(e).__name__}) - retry"
        record["needs_review"] = True
        record["retryable"] = True
    return record


def _review_entry(rec):
    sub = rec["submission"]
    report = rec.get("report") or {}
    cls = rec.get("classification") or {}
    reasons = []
    if cls.get("needs_review"):
        reasons.append(f"classification: {cls.get('review_reason')}")
    if sub["status"] == "NEEDS_REVIEW":
        reasons.append(f"comparison: {sub['review_reason']}")
    if rec.get("error"):
        reasons.append(f"processing error: {rec['error']}")
    return {
        "email_id": rec["email_id"],
        "subject": rec.get("subject"),
        "category": sub["category"],
        "status": sub["status"],
        "reasons": reasons,
        "detail": report.get("note"),
        "retryable": rec.get("retryable", False),
        "si_file": report.get("si_file"),
        "bl_file": report.get("bl_file"),
        "proposed_result": report.get("proposed_result"),
        "field_report": report.get("field_report") or None,
    }


def validate_submission(submission, sample):
    """Every sample email_id present, same keys per entry, valid values."""
    problems = []
    missing = set(sample) - set(submission)
    extra = set(submission) - set(sample)
    if missing:
        problems.append(f"{len(missing)} email_ids missing, e.g. {sorted(missing)[:3]}")
    if extra:
        problems.append(f"{len(extra)} unexpected email_ids, e.g. {sorted(extra)[:3]}")
    for eid, entry in submission.items():
        if eid in sample and set(entry) != set(sample[eid]):
            problems.append(f"{eid}: keys {sorted(entry)} != {sorted(sample[eid])}")
            break
        if entry["category"] not in classify.CATEGORIES:
            problems.append(f"{eid}: bad category {entry['category']!r}")
            break
    return problems


def _write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)


def run(source, out_dir=".", limit=None, retry=False):
    inbox = Inbox(source)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    previous = {}
    if retry:
        try:
            previous = {r["email_id"]: r for r in json.loads((out / "results.json").read_text(encoding="utf-8"))}
        except FileNotFoundError:
            print("No previous results.json - doing a full run instead")

    emails = inbox.emails()
    if limit:
        emails = emails[:limit]
    if previous:
        todo = {eid for eid, r in previous.items() if r.get("retryable")}
        print(f"Retrying {len(todo)} email(s) that failed retryably")
    else:
        todo = None

    records, started = [], time.time()
    for i, email in enumerate(emails, 1):
        eid = email.get("email_id")
        if todo is not None and eid not in todo and eid in previous:
            records.append(previous[eid])
        else:
            records.append(process_one(email, inbox))
        if i % 50 == 0 or i == len(emails):
            print(f"  ...{i}/{len(emails)} ({time.time() - started:.0f}s)")

    submission = {r["email_id"]: r["submission"] for r in records if r.get("email_id")}
    review_items = [_review_entry(r) for r in records if r.get("needs_review")]
    _write_json(out / "submission.json", submission)
    _write_json(out / "review_queue.json", review_items)
    _write_json(out / "results.json", records)
    review.refresh_outputs(out)           # final_submission.json + report.md

    try:
        sample = inbox.sample_submission()
        if limit:
            sample = {k: v for k, v in sample.items() if k in submission}
        problems = validate_submission(submission, sample)
        print("submission shape: OK" if not problems else "submission shape PROBLEMS:\n  "
              + "\n  ".join(problems))
    except Exception as e:
        print(f"(could not load sample_submission.json to validate: {e})")

    cats = Counter(s["category"] for s in submission.values())
    stats = Counter(s["status"] for s in submission.values())
    failed = [r["email_id"] for r in records if r.get("retryable")]
    print(f"{len(submission)} emails | {dict(cats)} | {dict(stats)} | review queue: {len(review_items)}")
    if failed:
        print(f"{len(failed)} email(s) hit a retryable failure (AI/OCR/network), e.g. {failed[:5]}"
              f" -> fix the cause, then: python pipeline.py {source} --retry")
    return submission, records


def main(argv=None):
    ap = argparse.ArgumentParser(description="SDOC pipeline: classify -> extract -> compare")
    ap.add_argument("source", nargs="?", default="data", help="data folder or server URL")
    ap.add_argument("--out", default=".", help="output folder (default: current)")
    ap.add_argument("--no-ai", action="store_true", help="no AI calls (rules + OCR only)")
    ap.add_argument("--retry", action="store_true", help="re-run only emails that failed retryably")
    ap.add_argument("--limit", type=int, default=None, help="only the first N emails")
    ap.add_argument("--submit", action="store_true", help="POST to the server's /submit")
    args = ap.parse_args(argv)

    if args.no_ai:
        os.environ["SDOC_DISABLE_AI"] = "1"
    submission, _ = run(args.source, args.out, args.limit, retry=args.retry)
    if args.submit:
        print(json.dumps(Inbox(args.source).submit(submission), indent=2))


if __name__ == "__main__":
    sys.exit(main())
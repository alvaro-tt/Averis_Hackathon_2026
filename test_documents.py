"""
Tests for document reading, AI analysis, OCR/vision, retries and human review.
No API key needed: Groq is replaced by a fake that answers in the real format.

  python test_documents.py data_v2
"""
import json
import os
import shutil
import sys
import tempfile
import types

DATA = sys.argv[1] if len(sys.argv) > 1 else "data_v2"
TMP = tempfile.mkdtemp(prefix="sdoc_test_")
os.environ["SDOC_CACHE_DIR"] = os.path.join(TMP, "cache")

import label_matching as L  # noqa: E402


# ---------------------------------------------------------------- fake Groq
class Fake:
    mode = "good"
    text_calls = 0
    vision_calls = 0
    last_content = None

    def __init__(self, *a, **k):
        self.chat = self
        self.completions = self

    def create(self, model, messages, **kw):
        content = messages[0]["content"]
        Fake.last_content = content
        if isinstance(content, list):                      # vision request
            Fake.vision_calls += 1
            fields = {f: {"value": v, "status": "found"} for f, v in {
                "shipper": "VISION SHIPPER", "consignee": "C", "notify_party": "C",
                "port_of_loading": "NANTONG, CHINA", "port_of_discharge": "KARACHI, PAKISTAN",
                "container_count": 6, "gross_weight_kg": 131058}.items()}
            return _resp(json.dumps({"document_type": "BILL_OF_LADING", "fields": fields}))
        Fake.text_calls += 1
        if Fake.mode == "fail":
            raise RuntimeError("429 rate_limit exceeded")
        if "<<<EMAIL_START>>>" in content:
            return _resp("BL_COMPARISON")
        doc = content.split("<<<DOCUMENT_START>>>")[1].split("<<<DOCUMENT_END>>>")[0]
        fields, blanks = L.extract_all_fields_detailed(doc)
        if Fake.mode == "hallucinate":
            fields["shipper"] = "TOTALLY MADE UP TRADING LLC"
        if Fake.mode == "disagree" and fields["gross_weight_kg"]:
            # realistic slip: reads a per-container weight (present in the table) as the total
            import re
            per = re.search(r"\b(\d{2},\d{3})\s*$", doc, re.M)
            fields["gross_weight_kg"] = int(per.group(1).replace(",", "")) if per else 1
        out = {f: {"value": v, "status": "blank" if f in blanks else "found"} for f, v in fields.items()}
        return _resp("```json\n" + json.dumps({"document_type": "OTHER", "fields": out}) + "\n```")


def _resp(text):
    msg = type("M", (), {"content": text})()
    return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()


groq = types.ModuleType("groq")
groq.Groq = Fake
sys.modules["groq"] = groq

import ai_extraction  # noqa: E402
import document_reader as R  # noqa: E402
import extraction  # noqa: E402
import ocr  # noqa: E402
import pipeline  # noqa: E402
import review  # noqa: E402
from loader import Inbox  # noqa: E402

ai_extraction.time.sleep = lambda *a, **k: None
inbox = Inbox(DATA)
passed = 0


def check(name, got, expected):
    global passed
    assert got == expected, f"FAIL {name}: got {got!r}, expected {expected!r}"
    passed += 1
    print(f"ok  {name}")


def fresh_cache():
    shutil.rmtree(os.environ["SDOC_CACHE_DIR"], ignore_errors=True)


def ai_on(mode="good"):
    os.environ.pop("SDOC_DISABLE_AI", None)
    Fake.mode = mode
    ai_extraction._client = None
    fresh_cache()


# ---------------------------------------------------------------- readers
ai_on()
d = R.read_document("attachments/email_059_BL.pdf", inbox, "BL")
check("text PDF read from its text layer", d["read_method"], "pdf_text")
check("PDF fields: rules and AI agree", set(d["field_sources"].values()), {"rules+ai"})
check("PDF recognised as a BL", d["document_type"], "BILL_OF_LADING")

d = R.read_document("attachments/email_055_BL.docx", inbox, "BL")
check("DOCX (bilingual labels) fully read", None in d["fields"].values(), False)
d = R.read_document("attachments/email_055_SI.xlsx", inbox, "SI")
check("XLSX fully read", None in d["fields"].values(), False)

d = R.read_document("attachments/email_512_SI.pdf", inbox, "SI")
check("image-only PDF goes through OCR", d["read_method"], "ocr")
check("OCR confidence recorded", d["ocr"]["confidence"] > 0.9, True)

check("corrupt PDF -> corrupt_file",
      R.read_document("attachments/email_511_BL.pdf", inbox, "BL")["error_code"], "corrupt_file")
check("invoice in the BL slot detected",
      R.read_document("attachments/email_501_BL.txt", inbox, "BL")["document_type"], "COMMERCIAL_INVOICE")

# ---------------------------------------------------------------- AI trust rules
ai_on("hallucinate")
d = R.read_document("attachments/email_059_BL.pdf", inbox, "BL")
check("hallucinated AI value is rejected", d["fields"]["shipper"] != "TOTALLY MADE UP TRADING LLC", True)
check("...and the rejection is visible", any("not found in the document" in w for w in d["warnings"]), True)

ai_on("disagree")
d = R.read_document("attachments/email_059_BL.pdf", inbox, "BL")
check("rules vs AI disagreement recorded", "gross_weight_kg" in d["disagreements"], True)
check("labelled rules value wins on a text document", d["field_sources"]["gross_weight_kg"], "rules")

# ---------------------------------------------------------------- failures + retry
ai_on("fail")
out = os.path.join(TMP, "run")
sub, recs = pipeline.run(DATA, out)
flagged = [r["email_id"] for r in recs if r["retryable"]]
check("AI outage still produces a full submission", len(sub), len(inbox.emails()))
check("AI outage makes emails retryable (visible failure)", len(flagged) > 0, True)

ai_on("good")
before = Fake.text_calls
pipeline.run(DATA, out, retry=True)
recs = json.load(open(os.path.join(out, "results.json")))
check("--retry clears the retryable failures", [r["email_id"] for r in recs if r["retryable"]], [])
check("--retry only re-ran the failed emails", Fake.text_calls - before < len(flagged) * 4, True)

# ---------------------------------------------------------------- vision fallback
ai_on("good")
real_engine = ocr.available_engine
ocr.available_engine = lambda: None                  # simulate: no OCR installed
d = R.read_document("attachments/email_513_BL.pdf", inbox, "BL")
ocr.available_engine = real_engine
check("no OCR engine -> vision model reads the scan", d["read_method"], "vision")
check("vision request carries the page image",
      any(p.get("type") == "image_url" for p in Fake.last_content), True)

os.environ["SDOC_DISABLE_AI"] = "1"
ocr.available_engine = lambda: None
d = R.read_document("attachments/email_513_BL.pdf", inbox, "BL")
ocr.available_engine = real_engine
check("no OCR and no AI -> ocr_unavailable, retryable", (d["error_code"], d["retryable"]),
      ("ocr_unavailable", True))

# ---------------------------------------------------------------- scan policy
os.environ["SDOC_DISABLE_AI"] = "1"
r = extraction.process_email(inbox.get("email_512"), inbox)
check("scan -> escalated for confirmation (unreadable)", r["reason"].startswith("Could not read attachment"), True)
check("scan escalation carries the proposed values", r["si_fields"]["container_count"], 6)

# ---------------------------------------------------------------- human review loop
out = os.path.join(TMP, "review")
pipeline.run(DATA, out)
q = [i["email_id"] for i in review.queue(out)]
check("review queue has the 20 cases", len(q), 20)

case = review.get_case(out, "email_512")["record"]["report"]
if (case.get("proposed_result") or {}).get("status") in ("OK", "MISMATCH"):
    d = review.decide(out, "email_512", "confirm", reviewer="tester")
else:
    try:
        review.decide(out, "email_512", "correct", reviewer="tester")
        check("incomplete correction is refused", False, True)
    except review.ReviewError:
        check("incomplete correction is refused", True, True)
    # the reviewer reads the scan and types in what OCR could not read
    si, bl = case["si_fields"], case["bl_fields"]
    fill = {k: (si.get(k) if si.get(k) is not None else bl.get(k)) for k in si}
    fill.update({k: f"READ BY REVIEWER {k}" for k, v in fill.items() if v is None})
    d = review.decide(out, "email_512", "correct", reviewer="tester", si_fields=fill, bl_fields=fill)
check("reviewer decision resolves the case", d["final"]["status"] in ("OK", "MISMATCH"), True)

d = review.decide(out, "email_516", "correct", reviewer="tester", si_fields={"gross_weight_kg": 999999})
check("correcting a blank value re-runs the comparison", d["final"]["status"], "MISMATCH")
check("...and names the differing field", "gross_weight_kg" in d["final"]["defect_fields"], True)

final = json.load(open(os.path.join(out, "final_submission.json")))
system = json.load(open(os.path.join(out, "submission.json")))
check("final_submission reflects the human decision", final["email_516"]["status"], "MISMATCH")
check("submission.json keeps the system's own answer", system["email_516"]["status"], "NEEDS_REVIEW")
check("resolved cases leave the queue", "email_516" in [i["email_id"] for i in review.queue(out)], False)
check("report.md shows the reviewer", "reviewed by tester" in open(os.path.join(out, "report.md")).read(), True)
check("report says 'No mismatch detected.' for clean emails",
      "No mismatch detected." in open(os.path.join(out, "report.md")).read(), True)

review.decide(out, "email_516", "reopen")
check("reopen puts it back in the queue", "email_516" in [i["email_id"] for i in review.queue(out)], True)

try:
    review.decide(out, "email_511", "confirm")
    check("confirm without a proposal is refused", False, True)
except review.ReviewError:
    check("confirm without a proposal is refused", True, True)

print(f"\nALL {passed} CHECKS PASSED")
shutil.rmtree(TMP, ignore_errors=True)
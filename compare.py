"""
compare.py — Stage 3: Compare (Ali's part)

Input:  the dict that Alvaro's data_extraction.process_email() returns for
        one email — either
          {"email_id", "status": "ok", "si_fields": {...}, "bl_fields": {...}}
        or an escalation/skip:
          {"email_id", "status": "escalate" | "not_applicable", "reason": "..."}

Output: the per-email report shape described in README.md:
          {
            "category": "BL_COMPARISON",
            "status": "OK" | "MISMATCH" | "NEEDS_REVIEW",
            "review_reason": None | "wrong_doc_type" | "missing_attachment"
                              | "unreadable" | "missing_value",
            "has_defect": bool,
            "defect_fields": [...],
          }
        plus a "field_report" with the SI/BL value pair, match flag,
        matching method, and (for mismatched text) a similarity score for
        every field — diagnostic detail for a human reviewer, never used
        to decide match/mismatch itself.

Design principle carried over from the extraction-stage fixes: prefer a
false MISMATCH (costs a human one review click) over a false MATCH (hides
a real defect). Every "smarter" comparison rule below is either fully
deterministic (LOCODEs, container-quantity arithmetic) or purely
diagnostic (similarity scores) — nothing here loosens matching by
guessing at approximate textual similarity for names. See the bottom of
this file for what was deliberately left out and why.
"""

import re
import math
import unicodedata
from difflib import SequenceMatcher

FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
]

NUMERIC_FIELDS = {"container_count", "gross_weight_kg"}
PORT_FIELDS = {"port_of_loading", "port_of_discharge"}

# Map Alvaro's free-text escalate/not_applicable reasons onto README's
# fixed review_reason enum. Extend as his reason strings change.
_REASON_KEYWORDS = [
    ("no si/bl attachments", "missing_attachment"),
    ("missing attachment", "missing_attachment"),
    ("unsupported attachment format", "wrong_doc_type"),
    ("could not read attachment", "unreadable"),
    ("field extraction failed", "missing_value"),
]

# A LOCODE is only trustworthy where it's unambiguous: inside parentheses
# ("NANTONG, CHINA (CNNTG)"), or as the entire value on its own ("CNNTG").
# A bare \b[A-Z]{2}[A-Z0-9]{3}\b search over the whole string is too loose —
# it matches plain words like "CHINA" (5 letters) just as happily.
_LOCODE_PAREN_RE = re.compile(r"\(([A-Z]{2}[A-Z0-9]{3})\)")
_LOCODE_WHOLE_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}$")

_LEGAL_SUFFIX_RE = re.compile(
    r"[.,\-]"  # strip periods/commas/hyphens — "FZ-LLC" vs "FZ LLC"
)

_NUMBER_RE = re.compile(r"[\d,]+(?:\.\d+)?")

# Matches "<n> x" style container-quantity groups, e.g. the "3" and "4" in
# "3 x 20'GP + 4 x 40'HC", so mixed container-type shipments sum correctly
# instead of only counting the first group found.
_CONTAINER_QTY_RE = re.compile(r"(\d+)\s*[xX]\s*\d*'?")

# Two floats are "the same number" if they're this close — purely a
# float-precision safety net (e.g. 131058.0 vs 131057.9999999997), NOT a
# real-world tolerance. A genuine 1kg difference must still mismatch.
_FLOAT_REL_TOL = 1e-9


def _normalize_text(value):
    """Case/punctuation/whitespace-insensitive normalization. Handles
    pure formatting noise — "FZ-LLC" vs "FZ LLC", extra spaces, case —
    NOT semantic differences. A genuinely different company/name still
    correctly compares unequal after this.
    """
    if value is None:
        return None
    stripped = _LEGAL_SUFFIX_RE.sub(" ", str(value))
    return " ".join(stripped.split()).casefold()


def _normalize_number(value):
    """Generic numeric normalization (used for gross_weight_kg). Strips
    commas/units defensively in case a raw string like "131,058 KG" ever
    reaches here instead of a clean number. NFKC-normalizes first so
    full-width digits from OCR of CJK-sourced documents (e.g. "１３１，０５８",
    common on China-routed shipments in this dataset) read the same as
    their ASCII equivalents."""
    if value is None:
        return None
    if isinstance(value, str):
        value = unicodedata.normalize("NFKC", value)
        match = _NUMBER_RE.search(value.replace(",", ""))
        value = match.group() if match else value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_container_count(value):
    """container_count gets its own normalizer: if the raw value is a
    string describing multiple container groups ("3 x 20'GP + 4 x
    40'HC"), sum the quantities rather than only reading the first
    number found — a plain single count ("6", "6 CNTRS") still works via
    the same fallback _normalize_number already uses.

    Alvaro's rule-based extractor already reduces this to a single int
    before it reaches compare, so in today's pipeline this mostly acts
    as a safety net / forward-compatibility for messier inputs (e.g. the
    advanced PDF/DOCX stage) rather than fixing something broken today.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return _normalize_number(value)
    value = unicodedata.normalize("NFKC", value)
    quantities = _CONTAINER_QTY_RE.findall(value)
    if quantities:
        return float(sum(int(q) for q in quantities))
    return _normalize_number(value)


def _numbers_match(a, b):
    if a is None or b is None:
        return False
    return math.isclose(a, b, rel_tol=_FLOAT_REL_TOL, abs_tol=_FLOAT_REL_TOL)


def _extract_locode(value):
    """Pull a 5-char UN/LOCODE if one is present and unambiguous: inside
    parentheses ("NANTONG, CHINA (CNNTG)") or as the whole value ("CNNTG").
    Returns None otherwise — never guesses at a bare word in running text."""
    if not value:
        return None
    text = str(value).upper()
    paren = _LOCODE_PAREN_RE.search(text)
    if paren:
        return paren.group(1)
    stripped = text.strip()
    return stripped if _LOCODE_WHOLE_RE.match(stripped) else None


def _primary_place_name(value):
    """The leading place name before the first comma or parenthesis,
    normalized — "NANTONG, CHINA (CNNTG)" -> "nantong". Used only as a
    last-resort fallback when neither side has a LOCODE and the full
    normalized text doesn't match outright, so a bare city name on one
    side ("Nantong") can still match a fuller form on the other."""
    if not value:
        return None
    cut = re.split(r"[,(]", str(value), maxsplit=1)[0]
    normalized = _normalize_text(cut)
    return normalized or None


def _ports_match(si_value, bl_value):
    """Ports are the one field where the two documents most often use
    different representations of the *same* place. Three tiers, in
    order of trust:
      1. LOCODE vs LOCODE — highest confidence, standardized codes.
      2. Full normalized text match.
      3. Primary place-name match (leading city name before any comma/
         paren) — lower confidence, used only when the first two can't
         decide either way.
    Returns (matched: bool, method: str) so the caller can record HOW
    confidently this was decided, not just whether it passed.
    """
    si_code, bl_code = _extract_locode(si_value), _extract_locode(bl_value)
    if si_code and bl_code:
        return si_code == bl_code, "locode"
    if _normalize_text(si_value) == _normalize_text(bl_value):
        return True, "text"
    si_place, bl_place = _primary_place_name(si_value), _primary_place_name(bl_value)
    if si_place and bl_place and si_place == bl_place:
        return True, "place_name_fallback"
    return False, "text"


def _similarity(si_value, bl_value):
    """A 0-1 similarity score for two mismatched text values — purely
    diagnostic, to help a human reviewer see at a glance whether a
    mismatch is a near-miss worth a second look or wildly different.
    Never used to decide match/mismatch."""
    if si_value is None or bl_value is None:
        return 0.0
    a, b = _normalize_text(si_value), _normalize_text(bl_value)
    return round(SequenceMatcher(None, a, b).ratio(), 2)


def _is_blank(value):
    """None, "", and whitespace-only strings are all 'nothing was actually
    extracted here' — not distinct cases. Without this, two blank strings
    on both sides would normalize to "" == "" and report a false MATCH,
    the exact same failure class fixed in extract_field()."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def fields_match(field, si_value, bl_value):
    """A field with a missing value on either side is never a 'match' —
    that's a data-quality problem for extraction/escalation to flag,
    not silently reported as passing. Returns (matched, method)."""
    if _is_blank(si_value) or _is_blank(bl_value):
        return False, "missing_value"
    if field == "container_count":
        a = _normalize_container_count(si_value)
        b = _normalize_container_count(bl_value)
        def _looks_summed(v):
            if not isinstance(v, str):
                return False
            return "x" in unicodedata.normalize("NFKC", v).lower()
        summed = _looks_summed(si_value) or _looks_summed(bl_value)
        return _numbers_match(a, b), ("container_sum" if summed else "numeric")
    if field in NUMERIC_FIELDS:
        a, b = _normalize_number(si_value), _normalize_number(bl_value)
        return _numbers_match(a, b), "numeric"
    if field in PORT_FIELDS:
        return _ports_match(si_value, bl_value)
    return _normalize_text(si_value) == _normalize_text(bl_value), "exact_text"


def _is_implausible_numeric(field, si_value, bl_value):
    """A shipment with 0 (or negative) containers or gross weight is
    never genuinely real — that almost always means a document/
    extraction problem masquerading as a clean number, not an honest
    value. Flags which side(s) show it."""
    if field not in NUMERIC_FIELDS:
        return []
    flagged = []
    for side, value in (("si", si_value), ("bl", bl_value)):
        normalized = (
            _normalize_container_count(value) if field == "container_count"
            else _normalize_number(value)
        )
        if normalized is not None and normalized <= 0:
            flagged.append(side)
    return flagged


def compare_fields(si_fields, bl_fields):
    """Field-by-field comparison across the 7 tracked fields.

    Returns (defect_fields, field_report, implausible_zeros).
    field_report has an entry per field with the si/bl values, a match
    flag, the matching method used, and (for mismatched non-numeric
    fields) a similarity score. implausible_zeros lists (field, side)
    pairs where a numeric field was exactly 0 — a plausibility red flag
    independent of whether SI and BL happen to agree.
    """
    defect_fields = []
    field_report = {}
    implausible_zeros = []
    for field in FIELDS:
        si_value = si_fields.get(field)
        bl_value = bl_fields.get(field)
        match, method = fields_match(field, si_value, bl_value)
        entry = {"si": si_value, "bl": bl_value, "match": match, "method": method}
        if not match and field not in NUMERIC_FIELDS:
            entry["similarity"] = _similarity(si_value, bl_value)
        field_report[field] = entry
        if not match:
            defect_fields.append(field)
        implausible_zeros.extend(
            (field, side) for side in _is_implausible_numeric(field, si_value, bl_value)
        )
    return defect_fields, field_report, implausible_zeros


def _map_review_reason(reason_text):
    if not isinstance(reason_text, str) or not reason_text:
        return "unreadable"
    lowered = reason_text.lower()
    for keyword, mapped in _REASON_KEYWORDS:
        if keyword in lowered:
            return mapped
    return "unreadable"


def _malformed_report(email_id, note):
    """A malformed/unexpected extraction_result (wrong shape, wrong types,
    wrong schema entirely) is NOT the same thing as a genuine field
    mismatch — it means we can't trust the comparison at all, so it
    always routes to NEEDS_REVIEW rather than risk reporting a fake
    MISMATCH (or silently reporting OK)."""
    return {
        "email_id": email_id,
        "category": "BL_COMPARISON",
        "status": "NEEDS_REVIEW",
        "review_reason": "unreadable",
        "has_defect": False,
        "defect_fields": [],
        "field_report": {},
        "note": note,
    }


def build_report(extraction_result):
    """Turn Alvaro's process_email() output into the final report for
    one email. Never raises — a malformed/unexpected input (missing
    keys, wrong types, wrong schema) always degrades to a NEEDS_REVIEW
    report with a `note` explaining why, instead of crashing the batch
    or silently mis-scoring the email."""
    if not isinstance(extraction_result, dict):
        return _malformed_report(None, f"extraction_result is not a dict (got {type(extraction_result).__name__})")

    email_id = extraction_result.get("email_id")
    status = extraction_result.get("status")

    if status == "ok":
        si_fields = extraction_result.get("si_fields")
        bl_fields = extraction_result.get("bl_fields")
        if not isinstance(si_fields, dict) or not isinstance(bl_fields, dict):
            return _malformed_report(
                email_id,
                "status is 'ok' but si_fields/bl_fields is missing or not a dict",
            )
        if not any(f in si_fields for f in FIELDS) and not any(f in bl_fields for f in FIELDS):
            return _malformed_report(
                email_id,
                "si_fields/bl_fields contain none of the expected 7 field keys",
            )

        defect_fields, field_report, implausible_zeros = compare_fields(si_fields, bl_fields)

        if implausible_zeros:
            # A 0 in a numeric field is a stronger signal of a broken
            # extraction than a routine field mismatch — don't report a
            # confident MISMATCH/OK next to a value that's almost
            # certainly wrong; send the whole email to review instead.
            fields_desc = ", ".join(f"{f} ({side})" for f, side in implausible_zeros)
            return {
                "email_id": email_id,
                "category": "BL_COMPARISON",
                "status": "NEEDS_REVIEW",
                "review_reason": "missing_value",
                "has_defect": False,
                "defect_fields": [],
                "field_report": field_report,
                "note": f"Implausible numeric value(s) (zero or negative): {fields_desc}",
            }

        has_defect = bool(defect_fields)
        return {
            "email_id": email_id,
            "category": "BL_COMPARISON",
            "status": "MISMATCH" if has_defect else "OK",
            "review_reason": None,
            "has_defect": has_defect,
            "defect_fields": defect_fields,
            "field_report": field_report,
        }

    # escalate / not_applicable / anything else the extraction stage produced
    return {
        "email_id": email_id,
        "category": "BL_COMPARISON",
        "status": "NEEDS_REVIEW",
        "review_reason": _map_review_reason(extraction_result.get("reason")),
        "has_defect": False,
        "defect_fields": [],
        "field_report": {},
    }


def render_summary(report):
    """One-line human-readable summary for a review queue or log.
    Uses .get() throughout — a partial/malformed report shouldn't crash
    the whole review-queue render, just print less detail."""
    status = report.get("status", "NEEDS_REVIEW")
    email_id = report.get("email_id", "<unknown email>")
    if status == "OK":
        return f"{email_id}: No mismatch detected."
    if status == "MISMATCH":
        field_report = report.get("field_report", {})
        parts = []
        for field in report.get("defect_fields", []):
            fr = field_report.get(field, {})
            sim = f", similarity {fr['similarity']}" if "similarity" in fr else ""
            parts.append(f"{field} (SI: {fr.get('si')} / BL: {fr.get('bl')}{sim})")
        return f"{email_id}: MISMATCH — " + "; ".join(parts)
    reason = report.get("review_reason")
    note = report.get("note")
    suffix = f" — {note}" if note else ""
    return f"{email_id}: NEEDS_REVIEW ({reason}){suffix}"


def build_submission_entry(report):
    """Strip down to exactly the keys README.md / sample_submission.json
    expect (drops the extra field_report/note detail). Defaults fill in
    if given a partial report rather than raising."""
    return {
        "category": report.get("category", "BL_COMPARISON"),
        "status": report.get("status", "NEEDS_REVIEW"),
        "review_reason": report.get("review_reason"),
        "has_defect": report.get("has_defect", False),
        "defect_fields": report.get("defect_fields", []),
    }


# ---------------------------------------------------------------------------
# Deliberately NOT implemented, and why:
#
# Fuzzy/approximate matching of company names (e.g. edit-distance or
# legal-suffix synonym expansion like "LTD" <-> "LIMITED", "CO" <->
# "COMPANY"). It's tempting — it would catch more near-miss formatting
# differences — but the failure mode is worse than what it fixes: two
# genuinely different legal entities (a real, meaningful compliance
# difference in shipping/customs contexts) can share a similar-looking
# name. A false MATCH here hides a real defect completely; a false
# MISMATCH just costs a reviewer one extra click. Given that asymmetry,
# only pure formatting normalization (case/punctuation/whitespace) is
# applied to names — never approximate similarity.
# ---------------------------------------------------------------------------
import json
from pathlib import Path
from collections import Counter

#!/usr/bin/env python3
"""
classify.py — Stage 1 of the SDOC pipeline: sort every email into one of
5 categories: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM.
"""

CATEGORIES = ["BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"]

# Cheap, reliable signals we can check without any AI call.
SPAM_SENDER_HINTS = ["webmail-verify", "parcel-track", "free-iphone", "prize"]
SPAM_BODY_HINTS = ["congratulations", "guaranteed", "gift card", "claim your",
                   "won a", "bitcoin", "investment opportunity", "hot singles"]

COMPARISON_BODY_HINTS = ["check the details and confirm", "please check",
                        "review and confirm", "verify the attached"]
SI_REQUEST_SUBJECT_HINTS = ["request si", "shipping instruction"]
INVOICE_HINTS = ["invoice", "local charges", "billing", "charge breakdown"]


def _has_si_and_bl_attachments(email: dict) -> bool:
    atts = email.get("attachments") or []
    has_si = any("_SI" in a for a in atts)
    has_bl = any("_BL" in a for a in atts)
    return has_si and has_bl


def classify_email(email: dict) -> str:
    """
    Return one of CATEGORIES for a single email dict
    (shaped as loader.Inbox gives it: email_id, from, subject, body, attachments).
    """
    subject = (email.get("subject") or "").lower()
    body = (email.get("body") or "").lower()
    sender = (email.get("from") or "").lower()
    text = f"{subject} {body}"

    # 1. SPAM — check sender domain and obvious scam language first.
    if any(hint in sender for hint in SPAM_SENDER_HINTS):
        return "SPAM"
    if any(hint in text for hint in SPAM_BODY_HINTS):
        return "SPAM"

    # 2. BL_COMPARISON — has both SI and BL attachments AND the body
    #    actually asks for a check (don't trust attachments alone).
    if _has_si_and_bl_attachments(email) and any(h in text for h in COMPARISON_BODY_HINTS):
        return "BL_COMPARISON"

    # 3. SI_REQUEST — subject explicitly says so, and it's a NEW instruction
    #    (no comparison language, since that would make it BL_COMPARISON instead).
    if any(h in subject for h in SI_REQUEST_SUBJECT_HINTS) and \
            not any(h in text for h in COMPARISON_BODY_HINTS):
        return "SI_REQUEST"

    # 4. INVOICE_QUERY — billing/charges language.
    if any(h in text for h in INVOICE_HINTS):
        return "INVOICE_QUERY"

    return "GENERAL"

def classify_all(inbox) -> dict:
    """Loop over every email in the inbox, return {email_id: category}."""
    results = {}
    for email in inbox:
        results[email["email_id"]] = classify_email(email)
    return results


if __name__ == "__main__":
    from loader import Inbox

    inbox = Inbox("data")
    results = classify_all(inbox)

    out_path = Path("classification_results.json")
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Classified {len(results)} emails -> {out_path}")

    counts = Counter(results.values())
    for cat in CATEGORIES:
        print(f"  {cat}: {counts.get(cat, 0)}")
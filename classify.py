"""
classify.py — Stage 1 of the SDOC pipeline: sort every email into one of
5 categories: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM.
"""
import json
import time
from pathlib import Path
from collections import Counter
from groq import Groq

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(max_retries=0)
    return _client

CATEGORIES = ["BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"]

# Cheap, reliable signals we can check without any AI call.
SPAM_SENDER_HINTS = ["webmail-verify", "parcel-track", "free-iphone", "prize"]
SPAM_BODY_HINTS = ["congratulations", "guaranteed", "gift card", "claim your",
                   "won a", "bitcoin", "investment opportunity", "hot singles",
                   "bank officer", "business proposal", "bank details"]

COMPARISON_BODY_HINTS = [
    "check the details and confirm", "please check",
    "review and confirm", "verify the attached",
    "shipping instruction and the draft bill of lading",
    "check the draft bl against the si",
    "verify the bl matches the si",
    "kindly verify", "kindly confirm the bl",
    "for checking", "please compare the si and draft bl",
]
SI_REQUEST_BODY_HINTS = ["please find shipping instruction", "shipping instruction for"]
INVOICE_HINTS = ["query on invoice", "local charges", "charge breakdown", "cancel invoice"]


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

    # 3. SI_REQUEST — body explicitly presents a new shipping instruction
    #    (no comparison language, since that would make it BL_COMPARISON instead).
    if any(h in body for h in SI_REQUEST_BODY_HINTS) and \
            not any(h in text for h in COMPARISON_BODY_HINTS):
        return "SI_REQUEST"

    # 4. INVOICE_QUERY — billing/charges language.
    if any(h in text for h in INVOICE_HINTS):
        return "INVOICE_QUERY"

    # 5. Anything left that still has SI+BL attachments but didn't match the
    #    comparison-language check above — genuinely ambiguous, worth an AI call
    #    rather than a rule-based guess (e.g. wording we haven't seen yet).
    if _has_si_and_bl_attachments(email):
        return classify_email_ai(email)

    # 6. No SI+BL attachments and no rule matched -> safe default.
    #    BL_COMPARISON structurally requires both SI+BL attachments (already
    #    checked above), so this can't be one. Rather than spend an AI call
    #    on every leftover email, default to GENERAL — the safest bucket.
    return "GENERAL"


CLASSIFY_PROMPT_TEMPLATE = """You are classifying an email from a shipping operations inbox into exactly ONE of these 5 categories:

- BL_COMPARISON: someone attaches a Shipping Instruction (SI) and a draft Bill of Lading (BL), asking for them to be checked/compared/confirmed against each other.
- SI_REQUEST: someone is providing or requesting a NEW shipping instruction (shipment details like POL, POD, shipper, consignee) - not asking for a comparison.
- INVOICE_QUERY: a question about invoice amounts, charges, or billing breakdowns.
- GENERAL: status updates, automated notifications, reminders, or other operational messages that don't need a document check.
- SPAM: unrelated junk, scams, or suspicious offers.

Email details:
From: {sender}
Subject: {subject}
Body: {body}
Attachments: {attachments}

Respond with ONLY the category name, exactly as written above (e.g. "BL_COMPARISON"). No punctuation, no explanation, nothing else.
"""


def classify_email_ai(email: dict, max_retries: int = 3) -> str:
    """
    AI-based fallback classifier for emails the rule-based checks couldn't
    confidently place. Sends the email to Groq (gpt-oss-120b) and asks for
    exactly one of the 5 category labels back.
    """
    prompt = CLASSIFY_PROMPT_TEMPLATE.format(
        sender=email.get("from", ""),
        subject=email.get("subject", ""),
        body=email.get("body", ""),
        attachments=email.get("attachments", []),
    )

    for attempt in range(max_retries):
        time.sleep(1)  # small pause before each AI call to avoid tripping rate limits
        try:
            response = _get_client().chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip().upper()

            if answer in CATEGORIES:
                return answer

            print(f"Unexpected classify response for {email.get('email_id')}: {answer!r}")
            return "GENERAL"

        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                print(f"Rate limited on {email.get('email_id')}, attempt {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(10)  # longer pause specifically after a rate-limit hit
                    continue
                print("Still rate limited after retries, skip AI fallback for this email")
                return "GENERAL"
            if attempt < max_retries - 1:
                print(f"AI call failed (attempt {attempt+1}/{max_retries}): {e}. Retrying again...")
                time.sleep(5)
            else:
                print(f"AI call failed after {max_retries} attempts: {e}")
                return "GENERAL"

    return "GENERAL"


def classify_all(inbox) -> dict:
    """Loop over every email in the inbox, return {email_id: category}."""
    results = {}
    emails = list(inbox)
    total = len(emails)
    for i, email in enumerate(emails, 1):
        results[email["email_id"]] = classify_email(email)
        if i % 20 == 0 or i == total:
            print(f"  ...processed {i}/{total}")
            Path("classification_results.json").write_text(json.dumps(results, indent=2))
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
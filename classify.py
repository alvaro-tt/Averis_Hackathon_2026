#!/usr/bin/env python3
"""
classify.py — Stage 1 of the SDOC pipeline: sort every email into one of
5 categories: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM.
"""

CATEGORIES = ["BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"]


def classify_email(email: dict) -> str:
    """
    Return one of CATEGORIES for a single email dict
    (shaped as loader.Inbox gives it: email_id, from, subject, body, attachments).
    """
    # TODO: add real logic
    return "GENERAL"


def classify_all(inbox) -> dict:
    """Loop over every email in the inbox, return {email_id: category}."""
    results = {}
    for email in inbox:
        results[email["email_id"]] = classify_email(email)
    return results
from ai_extraction import extract_fields_with_ai
from label_matching import extract_all_fields
from file_types import get_file_type
from format_readers import read_pdf_text

SUPPORTED_TYPES = {"txt", "pdf", "xlxs", "docx"}

def extract_all_fields_hybrid(text):
    result = extract_all_fields(text)  # rule-based first

    # Fields that are None (not found or conflicting duplicates)
    # gets processed with AI: the AI reads the whole document and can use
    # surrounding context to disambiguate, like telling "Port of Discharge POD" 
    # apart from "Proof of Delivery POD" by the section they sit in.
    if any(v is None for v in result.values()):
        ai_result = extract_fields_with_ai(text)
        if ai_result:
            for k, v in result.items():
                if v is None:
                    result[k] = ai_result.get(k)
    return result

def read_attachment_text(path, file_type, inbox):
    if file_type == "txt":
        return inbox.read_text(path)
    if file_type == "pdf":
        file_bytes = inbox.read_bytes(path)
        return read_pdf_text(file_bytes)
    raise ValueError(f"No reader implemented for file type: {file_type}")

def process_email(email, inbox):
    """
    Extracts the SI and BL path files from converted json file
    Reads the SI and BL files

    Returns the seven fields needed for checking.
    """
    email_id = email["email_id"]
    
    # safeguards against wrongly categorized emails
    if not email.get("attachments"):
        return {
            "email_id": email_id,
            "status": "not_applicable",
            "reason": "No SI/BL attachments present — likely not a document-comparison request"
        }
    
    # iterate every attachment
    si_path, bl_path = None, None
    for path in email.get("attachments", []):
        if "_SI" in path:
            si_path = path
        elif "_BL" in path:
            bl_path = path
    
    # if safeguards if si or bl does not exist
    missing = []
    if si_path is None:
        missing.append("SI")
    if bl_path is None:
        missing.append("BL")
    if missing:
        return {"email_id": email_id, "status": "escalate", "reason": f"Missing attachment(s): {', '.join(missing)}"}

    si_type = get_file_type(si_path)
    bl_type = get_file_type(bl_path)

    if si_type not in SUPPORTED_TYPES or bl_type not in SUPPORTED_TYPES:
        return {"email_id": email_id, "status": "escalate",
                "reason": f"Unsupported attachment format(s) — SI: {si_type}, BL: {bl_type}"}

    try:
        si_text = read_attachment_text(si_path, si_type, inbox)
        bl_text = read_attachment_text(bl_path, bl_type, inbox)
    except Exception as e:
        return {"email_id": email_id, 
                "status": "escalate", 
                "reason": f"Could not read attachment: {e}"}

        
    si_fields = extract_all_fields_hybrid(si_text)
    bl_fields = extract_all_fields_hybrid(bl_text)

    # if the field is still None after both hybrid extraction, escalate
    si_missing = [k for k, v in si_fields.items() if v is None]
    bl_missing = [k for k, v in bl_fields.items() if v is None]

    if si_missing or bl_missing:
        return {
            "email_id": email_id,
            "status": "escalate",
            "reason": f"Field extraction failed - SI missing:{si_missing}, BL missing: {bl_missing}"
        }
    
    return {
        "email_id": email_id,
        "status": "ok",
        "si_fields": si_fields,
        "bl_fields": bl_fields}
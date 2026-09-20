from ai_extraction import extract_fields_with_ai
from label_matching import extract_all_fields
from file_types import get_file_type

AMBIGUOUS = "AMBIGUOUS (need escalation)"

def extract_all_fields_hybrid(text):
    result = extract_all_fields(text)  # rule-based first

    # only continue with AI extraction if fields are None (which means unresolved or ambiguous)
    if any(v is None for v in result.values()):
        ai_result = extract_fields_with_ai(text)
        if ai_result:
            for k, v in result.items():
                if v is None:
                    result[k] = ai_result.get(k)
    return result

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

    if si_type == "txt" and bl_type == "txt":
        try:
            si_text = inbox.read_text(si_path)
            bl_text = inbox.read_text(bl_path)
        except (FileNotFoundError, UnicodeDecodeError) as e:
            return {"email_id": email_id, 
                    "status": "escalate", 
                    "reason": f"Could not read attachment: {e}"}

        
        si_fields = extract_all_fields_hybrid(si_text)
        bl_fields = extract_all_fields_hybrid(bl_text)

        si_missing = [k for k, v in si_fields.items() if v is None]
        bl_missing = [k for k, v in bl_fields.items() if v is None]
        si_ambiguous = [k for k, v in si_fields.items() if v == AMBIGUOUS]
        bl_ambiguous = [k for k, v in bl_fields.items() if v == AMBIGUOUS]

        if si_missing or bl_missing:
            return {
                "email_id": email_id,
                "status": "escalate",
                "reason": f"Field extraction failed - SI missing:{si_missing}, BL missing: {bl_missing}"
            }

        if si_ambiguous or bl_ambiguous:
            return {
                "email_id": email_id,
                "status": "escalate",
                "reason": f"Ambiguous field(s) found (duplicate labels, different values) — SI: {si_ambiguous}, BL: {bl_ambiguous}"
            }
        
        return {
            "email_id": email_id,
            "status": "ok",
            "si_fields": si_fields,
            "bl_fields": bl_fields}

    else: # for now, ignore the different file type problem. ill continue later - Alvaro
            return {
                "email_id": email_id,
                "status": "escalate",
                "reason": f"Unsupported attachment format(s) — SI: {si_type}, BL: {bl_type}"
            }
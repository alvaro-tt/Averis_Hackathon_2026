import json
import re
from google import genai
import time


client = genai.Client()

def get_file_type(path):
    if path.lower().endswith(".txt"):
        return "txt"
    elif path.lower().endswith(".pdf"):
        return "pdf"
    elif path.lower().endswith(".docx"):
        return "docx"
    elif path.lower().endswith(".xlsx"):
        return "xlsx"
    else:
        return "unknown"

def clean_json_response(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        # remove the first line (```json or ```) and the last line (```)
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    return text

def extract_fields_with_ai(text, max_retries = 3):
    prompt = f"""Read the following shipping document and extract these 7 fields:
shipper, consignee, notify_party, port_of_loading, port_of_discharge, container_count, gross_weight_kg

Rules:
- The document may use different wording for the same field (e.g. "Load Port" means port_of_loading, "Total Containers" means container_count).
- container_count should be just the number (e.g. 6, not "6 x 40'HC").
- gross_weight_kg should be just the number (e.g. 131058, not "131,058 KG").
- If a field cannot be found, use null.
- For shipper and consignee, return only the company name, not the address

Respond with ONLY a JSON object, no other text. Example format:
{{"shipper": "...", "consignee": "...", "notify_party": "...", "port_of_loading": "...", "port_of_discharge": "...", "container_count": 0, "gross_weight_kg": 0}}

Document:
{text}
"""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            cleaned = clean_json_response(response.text)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print("JSON parsing failed:", e)
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"AI call failed (attempt {attempt+1}/{max_retries}): {e}. Retrying again...")
                time.sleep(5)
            else:
                print(f"AI call failed after {max_retries} attempts: {e}")
                return None

FIELD_LABELS = {
    "shipper": ["shipper"],
    "consignee": ["consignee", "to the order of"],
    "notify_party": ["notify party", "notify"],
    "port_of_loading": ["port of loading"],
    "port_of_discharge": ["pod", "port of discharge"],
    "container_count": ["container count", "total containers"],
    "gross_weight_kg": ["gross weight", "gross wt"],
}

def extract_field(text, possible_labels):
    """
    Reads the 
    """
    for line in text.split("\n"):
        line = line.strip()

        # skip unnecessary lines
        if ":" not in line:
            continue

        # splits key and value
        label_part, value_part = line.split(":", 1)
        label_part = label_part.strip().lower()

        # check field label map for a match
        for label in possible_labels:
            if label in label_part:
                return value_part.strip()
    return None

def extract_number(raw_value):
    if raw_value is None:
        return None
    match = re.search(r"[\d,]+", raw_value)  # grabs digits and commas
    if match:
        return int(match.group().replace(",", ""))
    return None

def extract_all_fields(text):
    result = {}
    for field_name, labels in FIELD_LABELS.items():
        raw = extract_field(text, labels)
        if field_name in ("container_count", "gross_weight_kg"):
            result[field_name] = extract_number(raw)
        else:
            result[field_name] = raw
    return result

def extract_all_fields_hybrid(text):
    result = extract_all_fields(text)  # rule-based first
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

    # iterate every attachment
    si_path, bl_path = None, None
    for path in email.get("attachments", []):
        if "_SI" in path:
            si_path = path
        elif "_BL" in path:
            bl_path = path

        # safeguards against wrongly categorized emails
    if not email.get("attachments"):
        return {
            "email_id": email_id,
            "status": "not_applicable",
            "reason": "No SI/BL attachments present — likely not a document-comparison request"
        }
    
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

    else: # for now, ignore the different file type problem. ill continue later - Alvaro
            return {
                "email_id": email_id,
                "status": "escalate",
                "reason": f"Unsupported attachment format(s) — SI: {si_type}, BL: {bl_type}"
            }
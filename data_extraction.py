import json
import re

FIELD_LABELS = {
    "shipper": ["shipper"],
    "consignee": ["consignee", "to the order of"],
    "notify_party": ["notify party", "notify"],
    "port_of_loading": ["port of loading"],
    "port_of_discharge": ["pod", "port of discharge"],
    "container_count": ["container count", "total containers"],
    "gross_weight_kg": ["gross weight", "gross wt"],
}

def convert_to_list(file):
    """
    Extract json file and converts into native python data structure

    Returns the list/dictionary
    """
    with open(file, 'r') as f:
        data = json.load(f)
    return data

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

def process_email(email_json_path):
    """
    Extracts the SI and BL path files from converted json file
    Reads the SI and BL files

    Returns the seven fields needed for checking.
    """
    email = convert_to_list(email_json_path)
    
    si_path, bl_path = None, None
    for path in email["attachments"]:
        if "_SI" in path:
            si_path = path
        elif "_BL" in path:
            bl_path = path
    
    with open(si_path, "r") as f:
        si_text = f.read()
    with open(bl_path, "r") as f:
        bl_text = f.read()
    
    si_fields = extract_all_fields(si_text)
    bl_fields = extract_all_fields(bl_text)
    
    return email["email_id"], si_fields, bl_fields

if __name__ == '__main__':
    email_id, si_fields, bl_fields = process_email("email_004.json")

    print("Email ID:", email_id)
    print("\n--- SI fields ---")
    for k, v in si_fields.items():
        print(f"{k}: {v}")

    print("\n--- BL fields ---")
    for k, v in bl_fields.items():
        print(f"{k}: {v}")
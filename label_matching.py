from difflib import SequenceMatcher
import re

FIELD_LABELS = {
    "shipper": ["shipper"],
    "consignee": ["consignee", "to the order of"],
    "notify_party": ["notify party", "notify"],
    "port_of_loading": ["port of loading", "pol", "loaded from"],
    "port_of_discharge": ["pod", "port of discharge", "discharge port", "discharged from"],
    "container_count": ["container count", "total containers", "no. of containers"],
    "gross_weight_kg": ["gross weight", "gross wt"],
}

def normalize_label(label):
    """
    normalize strings by splitting into words and sorting them then compare
    """
    words = label.lower().replace("-", " ").replace("_", " ").split()
    return " ".join(sorted(words))

def label_similarity(a, b):
    """
    normalize typos
    """
    return SequenceMatcher(None, normalize_label(a), normalize_label(b)).ratio()

def extract_field(text, possible_labels, threshold = 0.85):
    """

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
            # fuzzy matching fallback to catch typos/formatting differences
            if label_similarity(label, label_part) >= threshold:
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

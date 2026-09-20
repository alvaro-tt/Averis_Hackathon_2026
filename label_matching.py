from difflib import SequenceMatcher
import re

FIELD_LABELS = {
    "shipper": [
        "shipper",
        "shipper name",
        "shipper/exporter",
        "exporter",
    ],
    "consignee": [
        "consignee",
        "consignee (non-negotiable)",
        "to the order of",
        "to order of",
        "consigned to",
    ],
    "notify_party": [
        "notify party",
        "notify",
        "also notify",
        "notify address",
    ],
    "port_of_loading": [
        "port of loading",
        "pol",
        "loading port",
        "loaded from",
        "port of loading (pol)",
        "place of receipt",
        "origin port",
    ],
    "port_of_discharge": [
        "port of discharge",
        "pod",
        "discharge port",
        "discharged from",
        "port of discharge (pod)",
        "destination port",
        "final destination",
    ],
    "container_count": [
        "container count",
        "total containers",
        "no. of containers",
        "number of containers",
        "no. of containers or packages",
        "qty of containers",
        "total no. of containers",
    ],
    "gross_weight_kg": [
        "gross weight",
        "gross wt",
        "gross weight (kg)",
        "gross wt (kgs)",
        "total gross weight",
        "g.w.",
    ],
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
    needs optimization: currently O(7NM)
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

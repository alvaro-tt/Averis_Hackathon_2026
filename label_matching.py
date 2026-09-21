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

def is_label_match(label, label_part):
    # when exact match
    label_part_clean = label_part.strip().lower()
    label_clean = label.strip().lower()

    if label_part_clean == label_clean:
        return True
    # for trailing qualifiers
    if label_part_clean.startswith(label_clean):
        remainder = label_part_clean[len(label_clean):].strip()
        return remainder == "" or remainder.startswith("(")
    return False

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

def extract_number(raw_value):
    if raw_value is None:
        return None
    match = re.search(r"[\d,]+", raw_value)  # grabs digits and commas
    if match:
        return int(match.group().replace(",", ""))
    return None

def extract_all_fields(text):
    """
    fix: scan the document once, check all 7 fields per line, instead of scanning the document 7 times
    and reduce order of growth: turn label lookup into a dictionary check to O(1). ill do this later -Alvaro
    """
    matches = {field: [] for field in FIELD_LABELS}
    lines = [l.strip() for l in text.split("\n")] # O(N)

    for i, line in enumerate(lines): # loop over N times
        # skip unnecessary lines
        if ":" not in line:
            continue

        # splits key and value
        label_part, value_part = line.split(":", 1)
        label_part = label_part.strip().lower()
        value = value_part.strip()

        for field, labels in FIELD_LABELS.items():
            for label in labels:
                matched = is_label_match(label, label_part) or label_similarity(label, label_part) >= 0.85
                if matched:
                    if value:
                        matches[field].append(value)
                    elif i + 1 < len(lines) and lines[i+1] and ":" not in lines[i+1]:
                        matches[field].append(lines[i+1].strip())
                    break

    result = {}
    for field, values in matches.items():
        unique_values = list(dict.fromkeys(values))  # de-dupe, preserve order
        if len(unique_values) == 0:
            result[field] = None
        elif len(unique_values) == 1:
            result[field] = unique_values[0]   # all mentions agree -> trusted
        else:
            result[field] = None               # genuine conflict -> let AI try, using full context

    for field in ("container_count", "gross_weight_kg"):
        result[field] = extract_number(result[field])
        
    return result
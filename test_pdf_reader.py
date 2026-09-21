from loader import Inbox
import json

DATA_PATH = "C:/Users/ASUS/Documents/Averis_Hackathon_2026/data"
inbox = Inbox(DATA_PATH)

with open("results_final.json", "r") as f:
    results = json.load(f)

# ------------------------------------------------------------
# Find a PDF/PDF escalation
# ------------------------------------------------------------

# pdf_escalations = [
#     r
#     for r in results
#     if r["status"] == "escalate"
#     and "SI: pdf, BL: pdf" in r.get("reason", "")
# ]

# print(f"Found {len(pdf_escalations)} PDF/PDF escalations")

# target_id = pdf_escalations[0]["email_id"]

# print(f"Testing with: {target_id}")


# ------------------------------------------------------------
# Load email
# ------------------------------------------------------------

# email = inbox.get(target_id)

# print(json.dumps(email, indent=2))

# ------------------------------------------------------------
# Find SI and BL attachments
# ------------------------------------------------------------

# from format_readers import read_pdf_text

# si_path, bl_path = None, None

# for path in email["attachments"]:
#     if "_SI" in path:
#         si_path = path
#     elif "_BL" in path:
#         bl_path = path

# ------------------------------------------------------------
# Read PDF files
# ------------------------------------------------------------

# si_bytes = inbox.read_bytes(si_path)
# bl_bytes = inbox.read_bytes(bl_path)

# si_text = read_pdf_text(si_bytes)
# bl_text = read_pdf_text(bl_bytes)

# print("=== SI TEXT ===")
# print(si_text)

# print("\n=== BL TEXT ===")
# print(bl_text)

# ------------------------------------------------------------
# Extract fields
# ------------------------------------------------------------

# from extraction import extract_all_fields_hybrid
# import json

# si_fields = extract_all_fields_hybrid(si_text)
# bl_fields = extract_all_fields_hybrid(bl_text)

# print("=== SI FIELDS ===")
# print(json.dumps(si_fields, indent=2))

# print("\n=== BL FIELDS ===")
# print(json.dumps(bl_fields, indent=2))


# ------------------------------------------------------------
# Test email_512
# ------------------------------------------------------------

# email = inbox.get("email_512")

# # find si_path, bl_path as before

# si_bytes = inbox.read_bytes(si_path)

# from format_readers import read_pdf_text

# print(repr(read_pdf_text(si_bytes)[:500]))

# ------------------------------------------------------------
# XLSX data testing
# ------------------------------------------------------------

# xlsx_escalations = [
#     r for r in results
#     if r["status"] == "escalate" and "SI: xlsx, BL: xlsx" in r.get("reason", "")
# ]
# target_id = xlsx_escalations[0]["email_id"]
# print(f"Testing with: {target_id}")

# email = inbox.get(target_id)
# si_path, bl_path = None, None
# for path in email["attachments"]:
#     if "_SI" in path:
#         si_path = path
#     elif "_BL" in path:
#         bl_path = path

# si_bytes = inbox.read_bytes(si_path)
# from format_readers import read_xlsx_text
# si_text = read_xlsx_text(si_bytes)
# print("=== SI TEXT ===")
# print(si_text)

# ------------------------------------------------------------
# docx data testing
# ------------------------------------------------------------

from format_readers import read_docx_text, read_xlsx_text

docx_escalations = [
    r for r in results
    if r["status"] == "escalate" and "docx" in r.get("reason", "").lower()
]
target_id = docx_escalations[0]["email_id"]
print(f"Testing with: {target_id}")

email = inbox.get(target_id)
si_path, bl_path = None, None

for path in email["attachments"]:
    if "_SI" in path:
        si_path = path
    elif "_BL" in path:
        bl_path = path

print(f"Found SI Path: {si_path}")
print(f"Found BL Path: {bl_path}")

if si_path:
    si_bytes = inbox.read_bytes(si_path)
    if si_path.lower().endswith(".docx"):
        si_text = read_docx_text(si_bytes)
    elif si_path.lower().endswith(".xlsx"):
        si_text = read_xlsx_text(si_bytes)
    else:
        si_text = "Unknown SI format"
    
    print("=== SI TEXT ===")
    print(si_text)

if bl_path:
    bl_bytes = inbox.read_bytes(bl_path)
    if bl_path.lower().endswith(".docx"):
        bl_text = read_docx_text(bl_bytes)
    elif bl_path.lower().endswith(".xlsx"):
        bl_text = read_xlsx_text(bl_bytes)
    else:
        bl_text = "Unknown BL format"
        
    print("=== BL TEXT ===")
    print(bl_text)
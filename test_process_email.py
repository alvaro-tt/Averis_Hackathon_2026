from loader import Inbox
from extraction import process_email
import random

DATA_PATH = "C:/Users/ASUS/Documents/Averis_Hackathon_2026/data"
inbox = Inbox(DATA_PATH)

emails = list(inbox)
sample = random.sample(emails,15)

ok_count = 0
escalate_count = 0
escalate_reasons = []

for email in sample:
    result = process_email(email, inbox)
    if result["status"] == "ok":
        ok_count += 1
    else:
        escalate_count += 1
        escalate_reasons.append((result["email_id"], result["reason"]))

print(f"Total: {ok_count + escalate_count} | OK: {ok_count} | Escalated: {escalate_count}")
for eid, reason in escalate_reasons:
    print(f"  {eid}: {reason}")

"""
errors found so far:
514 attachment is a pdf.
107 attachment: SI is xlsx whereas the BL is a docx
312 attachment is .txt
"""
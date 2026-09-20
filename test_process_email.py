from loader import Inbox
from extraction import process_email
import random

DATA_PATH = "C:/Users/ASUS/Documents/Averis_Hackathon_2026/data"
inbox = Inbox(DATA_PATH)

emails = list(inbox)
sample = random.sample(emails,15)

# ok_count = 0
# escalate_count = 0
# escalate_reasons = []

# for email in sample:
#     result = process_email(email, inbox)
#     if result["status"] == "ok":
#         ok_count += 1
#     else:
#         escalate_count += 1
#         escalate_reasons.append((result["email_id"], result["reason"]))

# print(f"Total: {ok_count + escalate_count} | OK: {ok_count} | Escalated: {escalate_count}")
# for eid, reason in escalate_reasons:
#     print(f"  {eid}: {reason}")

import time
start = time.time()

sample = emails[:50]  # first 50, or random.sample(emails, 50)
for email in sample:
    process_email(email, inbox)

elapsed = time.time() - start
print(f"50 emails took {elapsed:.1f} seconds ({elapsed/50:.2f}s per email)")
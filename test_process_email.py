from loader import Inbox
from extraction import process_email
import random
from label_matching import extract_all_fields
import json

DATA_PATH = "C:/Users/ASUS/Documents/Averis_Hackathon_2026/data"
inbox = Inbox(DATA_PATH)

emails = list(inbox)
sample = random.sample(emails,15)

"""
ok vs escalate count
"""
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

"""
time testing
"""
# import time
# start = time.time()

# sample = emails[:50]  # first 50, or random.sample(emails, 50)
# for email in sample:
#     process_email(email, inbox)

# elapsed = time.time() - start
# print(f"50 emails took {elapsed:.1f} seconds ({elapsed/50:.2f}s per email)")

""" 
correctness testing
"""
# # test #1
# print("=====================")
# print("Test #1: Expected email_004 input")
# print("=====================")

# email = inbox.get("email_004")
# result = process_email(email, inbox)
# print(json.dumps(result, indent=2))

# # test #2
# print("=====================")
# print("Test #2: decoy label")
# print("=====================")

# test_text = """Shipper: TEST COMPANY LTD
# Notify Party Contact Number: +971-4-4938298
# Consignee Reference No.: REF12345
# Notify Party: REAL NOTIFY COMPANY
# Consignee: REAL CONSIGNEE COMPANY
# """

# print(json.dumps(extract_all_fields(test_text), indent=2))

# # test #3
# print("=====================")
# print("Test #3: ambiguous test")
# print("=====================")

# test_text_ambiguous = """POD: KARACHI, PAKISTAN (PKKHI)
# Delivery Confirmation
# POD: Signature obtained, 14 Mar, warehouse gate 3
# """

# print(json.dumps(extract_all_fields(test_text_ambiguous), indent=2))

# # test #4
# print("=====================")
# print("Test #4: continuation line test")
# print("=====================")

# test_text_continuation = """Shipper:
# APRIL FAR EAST (M) SDN BHD
# Port of Loading: NANTONG, CHINA (CNNTG)
# """

# print(json.dumps(extract_all_fields(test_text_continuation), indent=2))

"""
full batch test
"""
# results = []
# for i, email in enumerate(inbox):
#     result = process_email(email, inbox)
#     results.append(result)
#     if i % 50 == 0:
#         with open("results_progress.json", "w") as f:
#             json.dump(results, f, indent=2)

# with open("results_final.json", "w") as f:
#     json.dump(results, f, indent=2)

# ok = sum(1 for r in results if r["status"] == "ok")
# escalated = sum(1 for r in results if r["status"] == "escalate")
# not_applicable = sum(1 for r in results if r["status"] == "not_applicable")

# print(f"Total: {len(results)}")
# print(f"OK: {ok}")
# print(f"Escalated: {escalated}")
# print(f"Not applicable: {not_applicable}")

# print("\n--- Escalation reasons ---")
# for r in results:
#     if r["status"] == "escalate":
#         print(f"  {r['email_id']}: {r['reason']}")


with open("results_final.json", "r") as f:
    results = json.load(f)

ok_results = [r for r in results if r["status"] == "ok"]
print(f"Found {len(ok_results)} OK results")

for r in ok_results[:10]:
    print(r["email_id"])
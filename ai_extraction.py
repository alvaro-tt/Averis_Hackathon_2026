from google import genai
import time
import json

client = genai.Client()

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

import os
from dotenv import load_dotenv
load_dotenv()

from tools.erpnext import create_lead, create_opportunity, create_quotation, fetch_pdf

name     = "Aman Test"
phone    = os.getenv("WHATSAPP_PHONE_NUMBER", "917739704188")
email    = "aman@gmail.com"
service  = "Website Design"
budget   = "10k"
timeline = "7 days"

print("Step 1: create_lead...")
try:
    lead = create_lead(name, phone, email, service, budget, timeline)
    lead_name = lead["name"]
    print(f"  OK → {lead_name}")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print(e.response.text)
    raise SystemExit

print("Step 2: create_opportunity...")
try:
    opp = create_opportunity(lead_name)
    print(f"  OK → {opp.get('name')}")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print(e.response.text)
    raise SystemExit

print("Step 3: create_quotation (item_code=Standard Service)...")
try:
    quote = create_quotation(lead_name, "Standard Service")
    quote_name = quote["name"]
    print(f"  OK → {quote_name}")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print(e.response.text)
    raise SystemExit

print("Step 4: fetch_pdf...")
try:
    pdf = fetch_pdf("Quotation", quote_name)
    print(f"  OK → {len(pdf)} bytes")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print(e.response.text)

print("\nAll steps done.")

"""
Test Agent 3 (Billing) pipeline step-by-step.
Run: python test_agent3_pipeline.py
Requires: ERPNext running, a Project already created in Phase 2.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")
print(f"\n--- Agent 3 Pipeline Test ---")

# We need a project name to test. You can hardcode a specific one or fetch the latest.
# Let's fetch the latest project for testing.
from tools.erpnext import _get
projects = _get("/api/resource/Project", {"limit": 1, "order_by": "creation desc"})
if not projects:
    print("  FAIL → No projects found. Run Phase 2 first to create a project.")
    raise SystemExit
project_name = projects[0]["name"]
print(f"Testing with Project: {project_name}\n")

# ── Step 1: get_tasks_for_project ──────────────────────────────────────────────
print("Step 1: check_all_tasks_complete...")
from tools.erpnext_billing import get_tasks_for_project
tasks = get_tasks_for_project(project_name)
if not tasks:
    print(f"  FAIL → No tasks found for project {project_name}.")
    raise SystemExit
    
all_done = all(t.get("status") in ["Completed", "Cancelled"] for t in tasks)
print(f"  Tasks found: {len(tasks)}. All Done? {all_done}")
# For testing purposes, we'll proceed even if they aren't all done.

# ── Step 2: get_project_details (finding the lead) ───────────────────────────
print("\nStep 2: fetch_linked_quotation (get lead)...")
from tools.erpnext_billing import get_project_details
details = get_project_details(project_name)
notes = details.get("notes", "")
lead_name = "Unknown"
if "Lead:" in notes:
    lead_name = notes.split("Lead:")[1].strip()
print(f"  OK → Found Lead: {lead_name}")

if lead_name == "Unknown":
    print("  FAIL → Could not determine lead from project notes. Ensure Phase 2 created the notes correctly.")
    raise SystemExit

# ── Step 3: create_sales_invoice ──────────────────────────────────────────────
print("\nStep 3: create_sales_invoice...")
from tools.erpnext_billing import create_sales_invoice, submit_sales_invoice
try:
    inv = create_sales_invoice(lead_name, project_name)
    invoice_name = inv.get("name")
    print(f"  OK → Created Invoice: {invoice_name}")
    
    print("Step 3b: submit_sales_invoice...")
    submit_sales_invoice(invoice_name)
    print(f"  OK → Submitted Invoice: {invoice_name}")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print("  Details:", e.response.text)
    raise SystemExit

# ── Step 4: fetch_pdf and send to WhatsApp ──────────────────────────────────
print("\nStep 4: fetch_pdf and send_document...")
from tools.erpnext import fetch_pdf
from tools.whatsapp import send_document

try:
    pdf_bytes = fetch_pdf("Sales Invoice", invoice_name)
    print(f"  OK → Fetched PDF, size: {len(pdf_bytes)} bytes")
    
    print(f"\nStep 5: Sending PDF to WhatsApp ({phone})...")
    msg = f"Your project {project_name} is fully completed! Here is your final invoice."
    send_document(phone, pdf_bytes, f"Invoice-{invoice_name}.pdf", msg)
    print("  OK → Message and PDF sent to WhatsApp successfully!")
except Exception as e:
    print(f"  FAIL → fetch/send PDF: {e}")
    if hasattr(e, "response"): print("  Details:", e.response.text)

print(f"\n✅ Agent 3 pipeline test complete!")
print(f"   Project: {project_name}")
print(f"   Invoice: {invoice_name}")
print(f"   Check ERPNext → Sales Invoice list to verify.")

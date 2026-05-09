"""
Test Agent 2 pipeline step-by-step.
Run: python test_agent2_pipeline.py
Requires: ERPNext running, a Lead + Quotation already created in Phase 1.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")
print(f"\n--- Agent 2 Pipeline Test ---")
print(f"Phone: {phone}\n")

# ── Step 1: get_lead_by_phone ─────────────────────────────────────────────────
print("Step 1: get_lead_by_phone...")
from tools.erpnext import get_lead_by_phone
lead = get_lead_by_phone(phone)
if not lead:
    print("  FAIL → No lead found. Run Phase 1 first to create a lead.")
    raise SystemExit
lead_name = lead["name"]
print(f"  OK → {lead_name}")

# ── Step 2: get_latest_quotation ──────────────────────────────────────────────
print("Step 2: get_latest_quotation...")
from tools.erpnext import get_latest_quotation
quote = get_latest_quotation(lead_name)
if not quote:
    print("  FAIL → No quotation found. Run Phase 1 first.")
    raise SystemExit
quote_name   = quote["name"]
items        = quote.get("items") or []
service_item = items[0].get("item_code", "Standard Service") if items else "Standard Service"
print(f"  OK → {quote_name} (service: {service_item})")

# ── Step 3: create_project ────────────────────────────────────────────────────
print("Step 3: create_project...")
from tools.erpnext import create_project
try:
    project = create_project(lead_name, quote_name)
    project_name = project.get("name") or project.get("project_name")
    print(f"  OK → {project_name}")
except Exception as e:
    print(f"  FAIL → {e}")
    if hasattr(e, "response"): print("  Details:", e.response.text)
    raise SystemExit

# ── Step 4: create_tasks ─────────────────────────────────────────────────────
print("Step 4: create_tasks...")
from tools.erpnext import create_task
from agents.agent2_project import TASK_TEMPLATES, DEFAULT_TASKS

tasks = TASK_TEMPLATES.get(service_item, DEFAULT_TASKS)
print(f"  Using task template for '{service_item}': {tasks}")
for subject in tasks:
    try:
        t = create_task(subject, project_name)
        print(f"  OK → Task: {t.get('name')}")
    except Exception as e:
        print(f"  FAIL → '{subject}': {e}")
        if hasattr(e, "response"): print("  Details:", e.response.text)

print(f"\n✅ Agent 2 pipeline test complete!")
print(f"   Lead: {lead_name}")
print(f"   Quotation: {quote_name}")
print(f"   Project: {project_name}")
print(f"   Check ERPNext → Project list to verify.")

import httpx
from config import ERPNEXT_BASE_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET

HEADERS = {
    "Authorization": f"token {ERPNEXT_API_KEY}:{ERPNEXT_API_SECRET}",
    "Content-Type": "application/json",
}


def _post(endpoint: str, data: dict) -> dict:
    r = httpx.post(f"{ERPNEXT_BASE_URL}{endpoint}", headers=HEADERS, json=data, timeout=15)
    r.raise_for_status()
    return r.json().get("data", {})


def _get(endpoint: str, params: dict = None) -> dict | list:
    r = httpx.get(f"{ERPNEXT_BASE_URL}{endpoint}", headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("data", {})


def _submit(doctype: str, name: str) -> dict:
    r = httpx.post(
        f"{ERPNEXT_BASE_URL}/api/resource/{doctype}/{name}/submit",
        headers=HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", {})


# ── Phase 1 ──────────────────────────────────────────────────────────────────

def create_lead(name: str, phone: str, email: str, service: str, budget: str, timeline: str) -> dict:
    return _post("/api/resource/Lead", {
        "lead_name":  name,
        "email_id":   email,
        "mobile_no":  phone,
        "status":     "Open",
        "notes":      [{"note": f"Service: {service} | Budget: {budget} | Timeline: {timeline}"}],
    })


def create_opportunity(lead_name: str) -> dict:
    return _post("/api/resource/Opportunity", {
        "opportunity_from": "Lead",
        "party_name":       lead_name,
        "opportunity_type": "Sales",
        "status":           "Open",
    })


def create_quotation(lead_name: str, item_code: str) -> dict:
    return _post("/api/resource/Quotation", {
        "quotation_to":      "Lead",
        "party_name":        lead_name,
        "items":             [{"item_code": item_code, "qty": 1}],
        "taxes_and_charges": "GST 18%",
    })


def fetch_pdf(doctype: str, name: str) -> bytes:
    r = httpx.get(
        f"{ERPNEXT_BASE_URL}/api/method/frappe.utils.print_format.download_pdf",
        headers=HEADERS,
        params={"doctype": doctype, "name": name, "format": "Standard"},
        timeout=20,
    )
    r.raise_for_status()
    return r.content


# ── Phase 2 ──────────────────────────────────────────────────────────────────

def get_latest_quotation(lead_name: str) -> dict:
    data = _get("/api/resource/Quotation", {
        "filters": f'[["party_name","=","{lead_name}"]]',
        "fields":  '["name","party_name","items"]',
        "limit":   1,
    })
    return data[0] if data else {}


def create_project(customer: str, quotation_name: str) -> dict:
    return _post("/api/resource/Project", {
        "project_name": f"Project – {customer}",
        "status":       "Open",
        "customer":     customer,
        "notes":        f"Quotation: {quotation_name}",
    })


def create_task(subject: str, project_name: str) -> dict:
    return _post("/api/resource/Task", {
        "subject":    subject,
        "project":    project_name,
        "status":     "Open",
    })


# ── Phase 3 ──────────────────────────────────────────────────────────────────

def get_tasks_for_project(project_name: str) -> list:
    return _get("/api/resource/Task", {
        "filters": f'[["project","=","{project_name}"]]',
        "fields":  '["name","status"]',
    })


def create_sales_invoice(customer: str, item_code: str, quotation_name: str) -> dict:
    return _post("/api/resource/Sales Invoice", {
        "customer":          customer,
        "items":             [{"item_code": item_code, "qty": 1}],
        "taxes_and_charges": "GST 18%",
        "remarks":           f"Against Quotation {quotation_name}",
    })


def submit_document(doctype: str, name: str) -> dict:
    return _submit(doctype, name)


# ── Phase 4 ──────────────────────────────────────────────────────────────────

def find_unpaid_invoices(amount: float) -> list:
    return _get("/api/resource/Sales Invoice", {
        "filters": f'[["outstanding_amount","=",{amount}],["status","=","Unpaid"]]',
        "fields":  '["name","customer","outstanding_amount"]',
    })


def get_invoice_customer(invoice_name: str) -> str:
    data = _get(f"/api/resource/Sales Invoice/{invoice_name}")
    return data.get("customer", "")


def create_payment_entry(customer: str, amount: float, txn_ref: str, txn_date: str, invoice_name: str) -> dict:
    return _post("/api/resource/Payment Entry", {
        "payment_type":     "Receive",
        "party_type":       "Customer",
        "party":            customer,
        "paid_amount":      amount,
        "received_amount":  amount,
        "reference_no":     txn_ref,
        "reference_date":   txn_date,
        "remarks":          "Verified via WhatsApp screenshot by AI Vision Agent",
        "references": [{
            "reference_doctype": "Sales Invoice",
            "reference_name":    invoice_name,
            "allocated_amount":  amount,
        }],
    })

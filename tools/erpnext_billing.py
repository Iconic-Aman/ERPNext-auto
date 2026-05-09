import httpx
import logging
from tools.erpnext import _post, _get, _submit

log = logging.getLogger(__name__)

# ── Phase 3: Billing ──────────────────────────────────────────────────────────

def get_tasks_for_project(project_name: str) -> list[dict]:
    """Fetch all tasks for a given project to check their status."""
    log.debug("[get_tasks_for_project] project=%s", project_name)
    data = _get("/api/resource/Task", {
        "filters": f'[["project","=","{project_name}"]]',
        "fields":  '["name","status","subject"]',
        "limit_page_length": 100,
    })
    return data if isinstance(data, list) else []


def get_project_details(project_name: str) -> dict:
    """Fetch project details to find the linked Lead/Customer."""
    log.debug("[get_project_details] project=%s", project_name)
    data = _get(f"/api/resource/Project/{project_name}")
    return data if isinstance(data, dict) else {}


def ensure_customer_exists(customer_name: str) -> str:
    """Ensure a Customer record exists for billing. Returns the customer name."""
    try:
        log.info("[ensure_customer] Checking/creating customer=%s", customer_name)
        _post("/api/resource/Customer", {
            "customer_name": customer_name,
            "customer_group": "Commercial",
            "customer_type": "Company"
        })
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 409:
            raise
        log.info("[ensure_customer] Customer %s already exists.", customer_name)
    return customer_name


def create_sales_invoice(lead_name: str, project_name: str, item_code: str = "Standard Service") -> dict:
    """Create a Sales Invoice for the Customer against the completed Project."""
    log.info("[create_sales_invoice] lead=%s project=%s", lead_name, project_name)
    
    # 1. Convert Lead to Customer (Required for invoicing)
    customer_name = ensure_customer_exists(lead_name)

    # 2. Create the Invoice
    return _post("/api/resource/Sales Invoice", {
        "customer": customer_name, 
        "project": project_name,
        "items": [{"item_code": item_code, "qty": 1}],
    })


def submit_sales_invoice(invoice_name: str) -> dict:
    """Submit the invoice to make it final and generate the PDF."""
    log.info("[submit_sales_invoice] invoice=%s", invoice_name)
    return _submit("Sales Invoice", invoice_name)

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("ERPNEXT_BASE_URL", "http://localhost:8080")
API_KEY = os.getenv("ERPNEXT_API_KEY", "")
API_SECRET = os.getenv("ERPNEXT_API_SECRET", "")

HEADERS = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def erpnext_find_unpaid_invoices(amount: float) -> list:
    url = f"{BASE_URL}/api/resource/Sales Invoice"
    params = {
        "filters": f'[["status","=","Unpaid"], ["outstanding_amount","=",{amount}]]',
        "fields": '["name", "customer"]'
    }
    r = httpx.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json().get("data", [])

def erpnext_create_payment(customer: str, amount: float, txn_ref: str, txn_date: str, invoice_name: str) -> dict:
    url = f"{BASE_URL}/api/resource/Payment Entry"
    payload = {
        "payment_type": "Receive",
        "party_type": "Customer",
        "party": customer,
        "paid_amount": amount,
        "received_amount": amount,
        "reference_no": txn_ref,
        "reference_date": txn_date,
        "references": [
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice_name,
                "allocated_amount": amount
            }
        ]
    }
    r = httpx.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json().get("data", {})

def erpnext_submit_document(doctype: str, docname: str):
    url = f"{BASE_URL}/api/resource/{doctype}/{docname}"
    payload = {"docstatus": 1}
    r = httpx.put(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

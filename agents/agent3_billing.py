from langgraph.graph import StateGraph, END
from state.schemas import Agent3State
from tools.erpnext_billing import get_tasks_for_project, get_project_details, create_sales_invoice, submit_sales_invoice
from tools.erpnext import fetch_pdf
from tools.whatsapp import send_document
import logging

log = logging.getLogger(__name__)

# ── Nodes ─────────────────────────────────────────────────────────────────────

def check_all_tasks_complete(state: Agent3State) -> Agent3State:
    project_name = state["project_name"]
    tasks = get_tasks_for_project(project_name)
    
    if not tasks:
        log.warning("[check_tasks] No tasks found for project %s", project_name)
        return {"all_done": False}

    all_done = all(t.get("status") in ["Completed", "Cancelled"] for t in tasks)
    log.info("[check_tasks] project=%s all_done=%s", project_name, all_done)
    return {"all_done": all_done}


def route_after_check(state: Agent3State) -> str:
    return "fetch_linked_quotation" if state.get("all_done") else END


def fetch_linked_quotation(state: Agent3State) -> Agent3State:
    # Get project details to find the lead/customer name and quotation reference
    details = get_project_details(state["project_name"])
    
    # We parse the notes to find Lead or Customer, fallback to standard
    notes = details.get("notes", "")
    lead_name = "Unknown"
    if "Lead:" in notes:
        lead_name = notes.split("Lead:")[1].strip()
    
    return {"quotation_name": lead_name} # We're passing lead_name via this field for invoice creation


def node_create_invoice(state: Agent3State) -> Agent3State:
    lead_name = state.get("quotation_name") # using this field to store lead name
    project_name = state["project_name"]
    
    try:
        inv = create_sales_invoice(lead_name, project_name)
        invoice_name = inv.get("name")
        log.info("[create_invoice] Created invoice %s", invoice_name)
        
        # Submit the invoice
        submit_sales_invoice(invoice_name)
        log.info("[submit_invoice] Submitted invoice %s", invoice_name)
        
        return {"invoice_name": invoice_name}
    except Exception as e:
        log.error("[create_invoice] Failed: %s", e)
        return {"invoice_name": None}


def send_invoice(state: Agent3State) -> Agent3State:
    phone = state.get("phone")
    invoice_name = state.get("invoice_name")
    
    if not phone or not invoice_name:
        return {}

    try:
        pdf_bytes = fetch_pdf("Sales Invoice", invoice_name)
        msg = f"Your project {state['project_name']} is fully completed! Here is your final invoice."
        send_document(phone, pdf_bytes, f"Invoice-{invoice_name}.pdf", msg)
        log.info("[send_invoice] Sent invoice %s to %s", invoice_name, phone)
    except Exception as e:
        log.error("[send_invoice] Failed to fetch/send PDF: %s", e)
        
    return {}


# ── Graph ─────────────────────────────────────────────────────────────────────

builder = StateGraph(Agent3State)
builder.add_node("check_all_tasks_complete", check_all_tasks_complete)
builder.add_node("fetch_linked_quotation",   fetch_linked_quotation)
builder.add_node("create_invoice",           node_create_invoice)
builder.add_node("send_invoice",             send_invoice)

builder.set_entry_point("check_all_tasks_complete")
builder.add_conditional_edges("check_all_tasks_complete", route_after_check, {
    "fetch_linked_quotation": "fetch_linked_quotation",
    END: END,
})
builder.add_edge("fetch_linked_quotation", "create_invoice")
builder.add_edge("create_invoice",         "send_invoice")
builder.add_edge("send_invoice",           END)

graph_agent3 = builder.compile()

def build_agent3_graph():
    return graph_agent3

from langgraph.graph import StateGraph, END
from state.schemas import Agent2State
from tools.erpnext import get_lead_by_phone, get_latest_quotation, create_project, create_task
from tools.whatsapp import send_text
import logging

log = logging.getLogger(__name__)

# Task templates keyed by item_code.
# "Standard Service" is the fallback used in Phase 1.
TASK_TEMPLATES: dict[str, list[str]] = {
    "Standard Service": [
        "Requirements Gathering",
        "Design & Wireframes",
        "Development",
        "Testing & QA",
        "Deployment & Handover",
    ],
    "WEB-DESIGN-BASIC": [
        "Requirements Gathering",
        "UI Wireframes",
        "Design Mockups",
        "Development",
        "Testing & QA",
        "Deployment & Handover",
    ],
    "SEO-PACKAGE": [
        "Site Audit",
        "Keyword Research",
        "On-Page Optimization",
        "Report Delivery",
    ],
}
DEFAULT_TASKS = ["Discovery", "Planning", "Execution", "Delivery"]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def fetch_quotation(state: Agent2State) -> Agent2State:
    phone = state["phone"]
    log.info("[fetch_quotation] phone=%s", phone)

    lead = get_lead_by_phone(phone)
    if not lead:
        log.warning("[fetch_quotation] No lead found for phone=%s", phone)
        send_text(phone, "Sorry, I couldn't find your details. Please start the conversation again.")
        return {"quotation_name": None, "customer_name": None, "service_item": None}

    lead_name = lead["name"]
    log.info("[fetch_quotation] lead=%s", lead_name)

    quote = get_latest_quotation(lead_name)
    if not quote:
        log.warning("[fetch_quotation] No quotation found for lead=%s", lead_name)
        send_text(phone, "Sorry, I couldn't find your quotation. Please contact support.")
        return {"quotation_name": None, "customer_name": lead_name, "service_item": None}

    items = quote.get("items") or []
    service_item = items[0].get("item_code", "Standard Service") if items else "Standard Service"

    log.info("[fetch_quotation] quotation=%s service=%s", quote["name"], service_item)
    return {
        "quotation_name": quote["name"],
        "customer_name":  lead_name,
        "service_item":   service_item,
    }


def route_after_fetch(state: Agent2State) -> str:
    return "create_project" if state.get("quotation_name") else END


def node_create_project(state: Agent2State) -> Agent2State:
    lead_name     = state["customer_name"]
    quotation_name = state["quotation_name"]
    log.info("[create_project] lead=%s quotation=%s", lead_name, quotation_name)

    try:
        project = create_project(lead_name, quotation_name)
        project_name = project.get("name") or project.get("project_name")
        log.info("[create_project] created=%s", project_name)
        return {"project_name": project_name}
    except Exception as e:
        log.error("[create_project] failed: %s", e)
        send_text(state["phone"], "Sorry, project creation failed. Our team will follow up.")
        return {"project_name": None}


def route_after_project(state: Agent2State) -> str:
    return "create_tasks" if state.get("project_name") else END


def node_create_tasks(state: Agent2State) -> Agent2State:
    service_item = state.get("service_item", "Standard Service")
    project_name = state["project_name"]
    tasks        = TASK_TEMPLATES.get(service_item, DEFAULT_TASKS)

    log.info("[create_tasks] project=%s tasks=%s", project_name, tasks)
    names = []
    for subject in tasks:
        try:
            t = create_task(subject, project_name)
            names.append(t.get("name", subject))
            log.info("[create_tasks] created task=%s", t.get("name"))
        except Exception as e:
            log.error("[create_tasks] failed for '%s': %s", subject, e)

    return {"task_names": names}


def notify_client(state: Agent2State) -> Agent2State:
    phone        = state["phone"]
    project_name = state.get("project_name", "your project")
    task_count   = len(state.get("task_names", []))

    msg = (
        f"✅ Great news! Your project *{project_name}* has been set up "
        f"with {task_count} tasks. Our team will begin work shortly. "
        "We'll keep you updated!"
    )
    send_text(phone, msg)
    log.info("[notify_client] notified phone=%s", phone)
    return {}


# ── Graph ─────────────────────────────────────────────────────────────────────

builder = StateGraph(Agent2State)
builder.add_node("fetch_quotation",  fetch_quotation)
builder.add_node("create_project",   node_create_project)
builder.add_node("create_tasks",     node_create_tasks)
builder.add_node("notify",           notify_client)

builder.set_entry_point("fetch_quotation")
builder.add_conditional_edges("fetch_quotation", route_after_fetch, {
    "create_project": "create_project",
    END: END,
})
builder.add_conditional_edges("create_project", route_after_project, {
    "create_tasks": "create_tasks",
    END: END,
})
builder.add_edge("create_tasks", "notify")
builder.add_edge("notify", END)

graph_agent2 = builder.compile()


def build_agent2_graph():
    return graph_agent2

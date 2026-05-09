from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from langchain_core.messages import HumanMessage
from checkpointer import init_checkpointer, close_checkpointer
from agents.agent1_crm import build_agent1_graph
from agents.agent2_project import build_agent2_graph
from agents.agent3_billing import build_agent3_graph
from config import WA_VERIFY
import logging

log = logging.getLogger(__name__)

# ── Lifespan: init MongoDB on startup, close on shutdown ───────────────────────
graph_agent1 = None
graph_agent2 = None
graph_agent3 = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph_agent1, graph_agent2, graph_agent3
    init_checkpointer()
    graph_agent1 = build_agent1_graph()
    graph_agent2 = build_agent2_graph()
    graph_agent3 = build_agent3_graph()
    print("[startup] MongoDB checkpointer ready. Agents 1, 2, 3 compiled.")
    yield
    close_checkpointer()
    print("[shutdown] MongoDB connection closed.")

app = FastAPI(title="ERPNext-Auto Agent Server", version="1.0.0", lifespan=lifespan)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def health():
    return {"status": "ok", "service": "ERPNext-Auto"}


# ── WhatsApp Verification (GET) ────────────────────────────────────────────────

@app.get("/webhook/whatsapp-inbound")
async def wa_verify(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == WA_VERIFY
    ):
        return int(params["hub.challenge"])
    raise HTTPException(status_code=403, detail="Verification failed")


# ── WhatsApp Inbound (POST) ────────────────────────────────────────────────────

@app.post("/webhook/whatsapp-inbound")
async def wa_inbound(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        entry   = payload["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        # Ignore status updates
        if "messages" not in value:
            return {"status": "ignored"}

        message  = value["messages"][0]
        phone    = message["from"]
        msg_type = message.get("type")

    except (KeyError, IndexError):
        raise HTTPException(status_code=400, detail="Bad payload structure")

    if msg_type == "image":
        # Phase 4 – Vision Reconciliation (Agent 4 — to be built)
        # TODO: invoke graph_agent4
        return {"status": "ok", "note": "agent4 not yet built"}

    elif msg_type == "text":
        body = message["text"]["body"].strip()
        log.info("[wa_inbound] phone=%s body=%r", phone, body)

        # Approval keyword → Agent 2
        APPROVAL_KEYWORDS = [
            "approved", "let's do it", "yes proceed", "confirm",
            "i approve", "go ahead", "looks good", "yes", "ok proceed",
        ]
        try:
            if any(kw in body.lower() for kw in APPROVAL_KEYWORDS):
                log.info("[wa_inbound] Approval detected from %s → Agent 2", phone)
                await graph_agent2.ainvoke(
                    {"phone": phone, "quotation_name": None, "customer_name": None,
                     "service_item": None, "project_name": None, "task_names": []},
                    config={"configurable": {"thread_id": f"agent2_{phone}"}},
                )
            else:
                # Normal conversation → Agent 1
                await graph_agent1.ainvoke(
                    {
                        "messages": [HumanMessage(content=body)],
                        "phone":    phone,
                        "qualified": False,
                        "lead_data": None,
                    },
                    config={"configurable": {"thread_id": phone}},
                )
        except Exception as e:
            log.error("[wa_inbound] Agent error: %s", e, exc_info=True)
            return {"status": "error", "detail": str(e)}

    return {"status": "ok"}


# ── ERPNext Webhooks ───────────────────────────────────────────────────────────

@app.post("/webhook/quotation-accepted")
async def quotation_accepted(request: Request):
    payload = await request.json()
    # TODO: invoke graph_agent2 when built
    print(f"[webhook] Quotation accepted: {payload.get('name')}")
    return {"status": "ok", "note": "agent2 not yet built"}


@app.post("/webhook/task-completed")
async def task_completed(request: Request):
    payload = await request.json()
    project_name = payload.get("project")
    
    if not project_name:
        return {"status": "ignored", "note": "No project in task"}

    log.info("[webhook] Task completed in project: %s", project_name)
    
    # Run Agent 3 to check if all tasks are done and send invoice
    # In a real setup, you'd fetch the user's phone from the project details
    # For testing, we use the default env var if we don't have the phone
    import os
    from dotenv import load_dotenv
    load_dotenv()
    phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")

    await graph_agent3.ainvoke(
        {
            "project_name": project_name, 
            "phone": phone,
            "all_done": False,
            "quotation_name": None,
            "invoice_name": None
        },
        config={"configurable": {"thread_id": f"agent3_{project_name}"}},
    )
    return {"status": "ok", "note": "agent3 invoked"}


@app.post("/webhook/invoice-submitted")
async def invoice_submitted(request: Request):
    payload = await request.json()
    print(f"[webhook] Invoice submitted: {payload.get('name')}")
    return {"status": "ok"}

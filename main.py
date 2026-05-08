from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from langchain_core.messages import HumanMessage
from checkpointer import init_checkpointer, close_checkpointer
from agents.agent1_crm import build_agent1_graph
from config import WA_VERIFY

# ── Lifespan: init MongoDB on startup, close on shutdown ───────────────────────
graph_agent1 = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph_agent1
    init_checkpointer()
    graph_agent1 = build_agent1_graph()
    print("[startup] MongoDB checkpointer ready. Agent 1 compiled.")
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

        # Approval keyword → Agent 2 (to be built)
        approval_keywords = ["approved", "let's do it", "yes proceed", "confirm"]
        if any(kw in body.lower() for kw in approval_keywords):
            # TODO: invoke graph_agent2
            return {"status": "ok", "note": "agent2 not yet built"}

        # Normal conversation → Agent 1 (thread_id = phone for multi-turn memory)
        await graph_agent1.ainvoke(
            {
                "messages": [HumanMessage(content=body)],
                "phone":    phone,
                "qualified": False,
                "lead_data": None,
            },
            config={"configurable": {"thread_id": phone}},
        )

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
    # TODO: invoke graph_agent3 when built
    print(f"[webhook] Task completed in project: {payload.get('project')}")
    return {"status": "ok", "note": "agent3 not yet built"}


@app.post("/webhook/invoice-submitted")
async def invoice_submitted(request: Request):
    payload = await request.json()
    print(f"[webhook] Invoice submitted: {payload.get('name')}")
    return {"status": "ok"}

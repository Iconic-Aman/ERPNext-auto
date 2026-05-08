from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from state.schemas import Agent1State
from tools.erpnext import create_lead, create_opportunity, create_quotation, fetch_pdf
from tools.whatsapp import send_text, send_document
from config import NVIDIA_API_KEY, NVIDIA_API_URL, LLM_MODEL
import json

llm = ChatOpenAI(
    base_url=NVIDIA_API_URL,    
    api_key=NVIDIA_API_KEY,
    model=LLM_MODEL,
    temperature=0.3
)

SYSTEM_PROMPT = """
You are a professional sales assistant for ERPNext Auto. Your job is to qualify
incoming leads over WhatsApp.

Your goal is to collect the following through natural conversation:
1. What service they are looking for
2. Their approximate budget
3. Their timeline (when they need it)
4. Their name and email

Rules:
- Be friendly, professional, and concise
- Ask one question at a time
- Do not mention internal systems or ERPNext
- Once you have ALL 4 pieces of information, end your message with exactly this JSON block:
  QUALIFIED: {"name": "", "email": "", "service": "", "budget": "", "timeline": ""}
- Until you have all info, continue the conversation naturally
"""

def converse(state: Agent1State) -> Agent1State:
    messages = state.get("messages", [])
    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT)] + messages)
    content = response.content

    if "QUALIFIED:" in content:
        # Extract JSON
        json_str = content.split("QUALIFIED:")[1].strip()
        try:
            lead_data = json.loads(json_str)
        except json.JSONDecodeError:
            lead_data = {}
            
        # Send any text before the QUALIFIED block if present
        reply_text = content.split("QUALIFIED:")[0].strip()
        if reply_text:
            send_text(state["phone"], reply_text)

        return {
            "messages": [response],
            "qualified": True,
            "lead_data": lead_data,
        }

    send_text(state["phone"], content)
    return {"messages": [response], "qualified": False}

def create_crm_records(state: Agent1State) -> Agent1State:
    d = state.get("lead_data", {})
    phone = state["phone"]
    
    # Create CRM records
    lead = create_lead(d.get("name", "Unknown"), phone, d.get("email", ""), d.get("service", ""), d.get("budget", ""), d.get("timeline", ""))
    opp = create_opportunity(lead["name"])
    
    # We use d["service"] as the item_code. Make sure this matches an Item in ERPNext.
    quote = create_quotation(lead["name"], d.get("service", "Standard Service"))
    
    # Send Quotation PDF
    pdf_bytes = fetch_pdf("Quotation", quote["name"])
    send_document(phone, pdf_bytes, f"Quotation-{quote['name']}.pdf", "Here is your quotation!")
    
    return {}

def route_after_converse(state: Agent1State) -> str:
    return "create_crm" if state.get("qualified") else END

# Build Graph
builder = StateGraph(Agent1State)
builder.add_node("converse", converse)
builder.add_node("create_crm", create_crm_records)

builder.set_entry_point("converse")
builder.add_conditional_edges("converse", route_after_converse, {
    "create_crm": "create_crm",
    END: END,
})
builder.add_edge("create_crm", END)

# Graph is compiled by main.py after init_checkpointer() runs
from checkpointer import get_checkpointer

def build_agent1_graph():
    return builder.compile(checkpointer=get_checkpointer())


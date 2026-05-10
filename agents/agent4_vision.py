import json
import base64
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from tools.whatsapp import get_media_url, download_media, send_text
from tools.erpnext_payment import erpnext_find_unpaid_invoices, erpnext_create_payment, erpnext_submit_document
from state.schemas import Agent4State
from checkpointer import get_checkpointer
import os 
from dotenv import load_dotenv

load_dotenv()

vision_llm = ChatOpenAI(
    model="meta/llama-3.2-90b-vision-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url=os.getenv("NVIDIA_API_URL")
)

VISION_PROMPT = """You are a payment verification assistant. Extract the following fields
from this payment receipt image and return ONLY valid JSON, no other text:
{
  "transaction_id": "",
  "amount": 0,
  "currency": "",
  "date": "",
  "sender_name": "",
  "receiver_name": "",
  "bank_name": ""
}
If any field is not visible, use null."""

def download_image(state: Agent4State) -> Agent4State:
    url = get_media_url(state["image_media_id"])
    img_bytes = download_media(url)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return {"_image_b64": img_b64}

def extract_payment_data(state: Agent4State) -> Agent4State:
    response = vision_llm.invoke([
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state.get('_image_b64', '')}"}},
            {"type": "text", "text": VISION_PROMPT},
        ])
    ])
    
    content = response.content.replace('```json\n', '').replace('```', '').strip()
    txn_data = json.loads(content)
    return {"txn_data": txn_data}

def match_invoice(state: Agent4State) -> Agent4State:
    amount = state["txn_data"].get("amount", 0)
    invoices = erpnext_find_unpaid_invoices(amount)
    if invoices:
        return {"matched_invoice": invoices[0]["name"]}
    return {"matched_invoice": None}

def route_after_match(state: Agent4State) -> str:
    return "create_payment_entry" if state.get("matched_invoice") else "ask_clarification"

def ask_clarification(state: Agent4State) -> Agent4State:
    send_text(
        state["phone"],
        "I received your payment screenshot but couldn't automatically match it to an invoice. Could you let me know which invoice number this is for?"
    )
    return {}

def create_payment_entry(state: Agent4State) -> Agent4State:
    d = state["txn_data"]
    amount = d.get("amount", 0)
    txn_ref = d.get("transaction_id") or "UNKNOWN"
    txn_date = d.get("date") or "Today" 
    
    invoices = erpnext_find_unpaid_invoices(amount)
    customer = invoices[0]["customer"] if invoices else "Unknown"

    payment = erpnext_create_payment(
        customer=customer,
        amount=amount,
        txn_ref=txn_ref,
        txn_date=txn_date,
        invoice_name=state["matched_invoice"],
    )
    erpnext_submit_document("Payment Entry", payment["name"])
    return {}

def confirm_to_client(state: Agent4State) -> Agent4State:
    send_text(
        state["phone"],
        f"✅ Payment received and verified. Invoice *{state['matched_invoice']}* is now marked as Paid. Thank you!"
    )
    return {}

def build_agent4_graph():
    builder = StateGraph(Agent4State)
    builder.add_node("download_image",       download_image)
    builder.add_node("extract_payment_data", extract_payment_data)
    builder.add_node("match_invoice",        match_invoice)
    builder.add_node("ask_clarification",    ask_clarification)
    builder.add_node("create_payment_entry", create_payment_entry)
    builder.add_node("confirm_to_client",    confirm_to_client)

    builder.set_entry_point("download_image")
    builder.add_edge("download_image",       "extract_payment_data")
    builder.add_edge("extract_payment_data", "match_invoice")
    builder.add_conditional_edges("match_invoice", route_after_match, {
        "create_payment_entry": "create_payment_entry",
        "ask_clarification":    "ask_clarification",
    })
    builder.add_edge("create_payment_entry", "confirm_to_client")
    builder.add_edge("confirm_to_client",    END)
    builder.add_edge("ask_clarification",    END)

    return builder.compile(checkpointer=get_checkpointer())

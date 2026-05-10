from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages

class Agent1State(TypedDict):
    messages: Annotated[list, add_messages]   # full conversation history
    phone: str                                 # sender's phone number
    qualified: bool
    lead_data: Optional[dict]                  # extracted: name, email, service, budget, timeline

class Agent2State(TypedDict):
    phone: str
    quotation_name: Optional[str]
    customer_name: Optional[str]
    service_item: Optional[str]
    project_name: Optional[str]
    task_names: list[str]

class Agent3State(TypedDict):
    project_name: str
    phone: Optional[str]
    all_done: bool
    quotation_name: Optional[str]
    invoice_name: Optional[str]

class Agent4State(TypedDict):
    phone: str
    image_media_id: str
    _image_b64: Optional[str]
    txn_data: Optional[dict]   # {transaction_id, amount, date, sender_name}
    matched_invoice: Optional[str]

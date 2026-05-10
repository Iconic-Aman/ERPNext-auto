import asyncio
from unittest.mock import patch
from agents.agent4_vision import build_agent4_graph
from checkpointer import init_checkpointer, close_checkpointer

async def run_test():
    try:
        with open("payment.jpg", "rb") as f:
            img_bytes = f.read()
    except FileNotFoundError:
        print("Error: Put a payment screenshot named 'payment.jpg' in this folder first.")
        return

    init_checkpointer()
    graph_agent4 = build_agent4_graph()

    import os
    from dotenv import load_dotenv
    load_dotenv()
    phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")
    
    print(f"Running Agent 4 with mocked WhatsApp image. Sending real messages to {phone}...")
    
    with patch("agents.agent4_vision.get_media_url", return_value="http://mock.url"), \
         patch("agents.agent4_vision.download_media", return_value=img_bytes):
         
        result = await graph_agent4.ainvoke(
            {"phone": phone, "image_media_id": "mock_id_123"},
            config={"configurable": {"thread_id": "pay_test"}}
        )
        
        print("\n=== Agent 4 Result ===")
        print(f"Extracted Data: {result.get('txn_data')}")
        print(f"Matched Invoice: {result.get('matched_invoice')}")
        
    close_checkpointer()

if __name__ == "__main__":
    asyncio.run(run_test())

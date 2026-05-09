import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
url = os.getenv("WEBHOOK_URL", "http://localhost:10000/webhook/whatsapp-inbound")

print(f"--- ERPNext Auto Multi-Turn Webhook Tester ---")
print(f"Simulating inbound messages from: {phone}")
print(f"Target URL: {url}")
print(f"Type 'exit' to quit.")
print("-" * 46)

message_id_counter = 1000

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ['exit', 'quit']:
        break
        
    message_id_counter += 1
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1234567890",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": phone,
                                "phone_number_id": phone_id
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": phone
                                }
                            ],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": f"wamid.{message_id_counter}",
                                    "timestamp": str(int(time.time())),
                                    "text": {
                                        "body": user_input
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"[Webhook sent successfully. Check your WhatsApp for the bot's reply!]")
        else:
            print(f"[Error] Status {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[Connection Error] {e}")

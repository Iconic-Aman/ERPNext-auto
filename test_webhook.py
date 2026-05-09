import requests
import os
from dotenv import load_dotenv

load_dotenv()
phone = os.getenv("WHATSAPP_PHONE_NUMBER", "").lstrip("+")
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
url = os.getenv("WEBHOOK_URL", "http://localhost:10000/webhook/whatsapp-inbound")

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
                                "id": "wamid.12345",
                                "timestamp": "1600000000",
                                "text": {
                                    "body": "Hi, I am interested in your services."
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

headers = {
    "Content-Type": "application/json"
}

print(f"Sending test payload to {url}...")
response = requests.post(url, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

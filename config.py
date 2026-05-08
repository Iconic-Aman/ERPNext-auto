from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")

# ERPNext
ERPNEXT_BASE_URL   = os.getenv("ERPNEXT_BASE_URL", "http://localhost:8000")
ERPNEXT_API_KEY    = os.getenv("ERPNEXT_API_KEY")
ERPNEXT_API_SECRET = os.getenv("ERPNEXT_API_SECRET")

# LLM
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_API_URL = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
LLM_MODEL      = os.getenv("LLM_MODEL", "meta/llama-3.1-8b-instruct")

# WhatsApp
WA_TOKEN    = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WA_VERIFY   = os.getenv("WA_VERIFY_TOKEN")
WA_API_URL  = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v18.0")

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

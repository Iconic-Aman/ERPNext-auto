import httpx
from config import WA_TOKEN, WA_PHONE_ID

_BASE = "https://graph.facebook.com/v18.0"
_HEADERS = {"Authorization": f"Bearer {WA_TOKEN}"}


def send_text(to: str, body: str) -> None:
    httpx.post(
        f"{_BASE}/{WA_PHONE_ID}/messages",
        headers=_HEADERS,
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        },
        timeout=10,
    ).raise_for_status()


def _upload_media(pdf_bytes: bytes) -> str:
    r = httpx.post(
        f"{_BASE}/{WA_PHONE_ID}/media",
        headers={"Authorization": f"Bearer {WA_TOKEN}"},
        files={"file": ("document.pdf", pdf_bytes, "application/pdf")},
        data={"messaging_product": "whatsapp"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["id"]


def send_document(to: str, pdf_bytes: bytes, filename: str, caption: str = "") -> None:
    media_id = _upload_media(pdf_bytes)
    httpx.post(
        f"{_BASE}/{WA_PHONE_ID}/messages",
        headers=_HEADERS,
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"id": media_id, "filename": filename, "caption": caption},
        },
        timeout=10,
    ).raise_for_status()


def get_media_url(media_id: str) -> str:
    r = httpx.get(f"{_BASE}/{media_id}", headers=_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["url"]


def download_media(url: str) -> bytes:
    r = httpx.get(url, headers=_HEADERS, timeout=20)
    r.raise_for_status()
    return r.content

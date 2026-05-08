import sys
from tools.whatsapp import send_text

def test(phone_number):
    print(f"Testing send_text to {phone_number}...")
    try:
        send_text(phone_number, "Hello from ERPNext-Auto Test!")
        print("Success! Message sent.")
    except Exception as e:
        print("Failed:", e)
        if hasattr(e, "response"):
            print("Details:", e.response.text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test(sys.argv[1])
    else:
        print("Usage: python test_whatsapp.py <phone_number_with_country_code>")
        print("Example: python test_whatsapp.py 919876543210")

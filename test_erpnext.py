from tools.erpnext import create_lead

def test():
    print("Testing create_lead...")
    try:
        lead = create_lead(
            name="Test User",
            phone="+1234567890",
            email="test@example.com",
            service="Website Design",
            budget="1000",
            timeline="1 week"
        )
        print("Success! Created Lead:", lead.get("name"))
    except Exception as e:
        print("Failed:", e)
        if hasattr(e, "response"):
            print("Details:", e.response.text)

if __name__ == "__main__":
    test()

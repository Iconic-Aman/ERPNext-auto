from tools.erpnext import _get
items = _get("/api/resource/Item", {"fields": '["item_code","item_name"]', "limit": 20})
for i in items:
    print(i)

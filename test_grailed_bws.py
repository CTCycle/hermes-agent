import os
email = os.environ.get("CARTEL_777_GRAILED_EMAIL", "NOT FOUND")
pw = os.environ.get("CARTEL_777_GRAILED_PASSWORD", "NOT FOUND")
print(f"Email: {email}")
print(f"Password: {pw[:4]}*** (len={len(pw)})")

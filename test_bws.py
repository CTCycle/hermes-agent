import os
pw = os.environ.get("BWS_CARTEL_777_GRAILED_PASSWORD", "NOT FOUND")
print(f"Password found: {pw[:4]}*** (len={len(pw)})")

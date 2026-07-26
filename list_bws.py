import os
# List all BWS_ env vars
for key, val in sorted(os.environ.items()):
    if 'GRAILED' in key.upper() or 'CARTEL' in key.upper() or 'BWS_' in key:
        print(f"{key}: {'*' * min(len(val), 8)} (len={len(val)})")

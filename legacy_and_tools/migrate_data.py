import os
import shutil

DATA_DIR = 'data'
LIVE_DIR = os.path.join(DATA_DIR, 'live')
STAGING_DIR = os.path.join(DATA_DIR, 'staging')

os.makedirs(LIVE_DIR, exist_ok=True)
os.makedirs(STAGING_DIR, exist_ok=True)

# Move existing Years (2025, etc.) to LIVE_DIR
for item in os.listdir(DATA_DIR):
    item_path = os.path.join(DATA_DIR, item)
    if os.path.isdir(item_path) and item not in ['live', 'staging', '__pycache__']:
        print(f"Moving {item} to {LIVE_DIR}...")
        shutil.move(item_path, LIVE_DIR)

print("Migration Complete.")

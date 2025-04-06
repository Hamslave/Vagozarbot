import os
import json

# گرفتن اطلاعات از متغیرهای محیطی
TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")
ADMIN_IDS = [677873313, 7860972907]  # می‌تونی اینم از env بگیری ولی فعلاً باشه

CREDENTIALS_FILE = "credentials.json"

# اگر فایل credentials.json وجود نداشت، از محیط بسازش
if not os.path.exists(CREDENTIALS_FILE):
    credentials_content = os.environ.get("CREDENTIALS_JSON")
    if credentials_content:
        with open(CREDENTIALS_FILE, "w") as f:
            f.write(credentials_content)

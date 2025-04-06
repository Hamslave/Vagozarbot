import os
import json

TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")
ADMIN_IDS = [677873313, 7860972907]
CREDENTIALS_FILE = "credentials.json"

if not os.path.exists(CREDENTIALS_FILE):
    credentials_content = os.environ.get("CREDENTIALS_JSON")
    if credentials_content:
        # می‌توانیم قبل از نوشتن، JSON رو بررسی کنیم تا مطمئن بشیم معتبر هست
        try:
            parsed = json.loads(credentials_content)
            # دوباره به صورت استرینگ منظم می‌نویسیم
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump(parsed, f)
        except json.JSONDecodeError as e:
            print("Error parsing JSON from environment variable:", e)

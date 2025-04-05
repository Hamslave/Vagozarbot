import os

# دریافت توکن و شیت آیدی از متغیرهای محیطی
TOKEN = os.environ.get("TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")

# در صورت نیاز می‌توانید اعتبار سنجی کنید که این مقادیر مقداردهی شده‌اند
if not TOKEN:
    raise ValueError("TOKEN is not set in the environment variables")
if not SHEET_ID:
    raise ValueError("SHEET_ID is not set in the environment variables")
import os

# دریافت محتوای کلید گوگل از متغیر محیطی
google_credentials = os.environ.get("CREDENTIALS_FILE")
if google_credentials:
    # اگر در متغیر محیطی خط‌های جدید به صورت "\\n" ذخیره شده‌اند، آن‌ها را به "\n" تبدیل می‌کنیم.
    google_credentials = google_credentials.replace('\\n', '\n')
    with open("credentials.json", "w") as f:
        f.write(google_credentials)

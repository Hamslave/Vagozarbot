import os

# دریافت توکن و شیت آیدی از متغیرهای محیطی
TOKEN = os.environ.get("TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")

# در صورت نیاز می‌توانید اعتبار سنجی کنید که این مقادیر مقداردهی شده‌اند
if not TOKEN:
    raise ValueError("TOKEN is not set in the environment variables")
if not SHEET_ID:
    raise ValueError("SHEET_ID is not set in the environment variables")

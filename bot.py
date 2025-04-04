import datetime
import re
import gspread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext
)
from config import TOKEN, SHEET_ID

# اتصال به گوگل شیت
gc = gspread.service_account(filename="credentials.json")
sh = gc.open_by_key(SHEET_ID)
sheet1 = sh.worksheet("Sheet1")   # ثبت ملک
sheet2 = sh.worksheet("Sheet2")   # سوالات و متن‌ها
sheet4 = sh.worksheet("Sheet4")   # ذخیره سوالات و پاسخ‌های پشتیبانی
sheetFAQ = sh.worksheet("FAQ")    # شیت FAQ برای پاسخ‌های پشتیبانی
sheet7 = sh.worksheet("Sheet7")   # فرم استخدام (سوالات)
sheet8 = sh.worksheet("Sheet8")   # اطلاعات استخدام

# تابع تولید کد ملک بر اساس نوع ملک
def generate_property_code(property_type):
    prefix = {"مسکونی": "2", "اداری": "3", "تجاری": "4"}.get(property_type, "0")
    return f"{prefix}{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

# الگوی اعتبارسنجی شماره تلفن (انعطاف‌پذیر)
phone_pattern = re.compile(r"^(?:\+98|0098|98|0)?9\d{9}$")

# نمایش منوی اصلی
async def start(update: Update, context: CallbackContext):
    keyboard = [
        ["🏠 ثبت ملک", "🔎 جستجوی ملک"],
        ["📞 پشتیبانی", "📝 استخدام"],
        ["ℹ️ اطلاعات تماس"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👏 به ربات واگذار خوش آمدید! لطفن یک گزینه را انتخاب کنید 🙏 :",
        reply_markup=reply_markup
    )

# ===================== فلو ثبت ملک =====================

async def register_property(update: Update, context: CallbackContext):
    context.user_data["registering"] = True
    context.user_data["answers"] = []
    context.user_data["question_index"] = 0
    context.user_data["waiting_for_phone"] = True
    keyboard = [[KeyboardButton("📲 ارسال شماره تلفن", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    # تغییر متن درخواست شماره تماس
    await update.message.reply_text(
        "🏠 لطفاً شماره تماس خود را ارسال کنید:",
        reply_markup=reply_markup
    )
    return 0

async def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    phone_number = contact.phone_number if contact else update.message.text.strip()
    phone_number = re.sub(r"\s+", "", phone_number)
    if phone_pattern.match(phone_number):
        context.user_data["phone_number"] = phone_number
        context.user_data["waiting_for_phone"] = False
        await update.message.reply_text(f"✅ شماره دریافت شد: {phone_number}")
        await ask_next_question(update, context)
        return 1
    else:
        await update.message.reply_text("❌ شماره وارد شده نامعتبر است. لطفاً شماره را صحیح وارد کنید.")
        return 0

async def handle_text(update: Update, context: CallbackContext):
    if context.user_data.get("registering"):
        if context.user_data.get("waiting_for_phone", False):
            # دریافت شماره به صورت دستی
            phone_number = update.message.text.strip()
            phone_number = re.sub(r"\s+", "", phone_number)
            if phone_pattern.match(phone_number):
                context.user_data["phone_number"] = phone_number
                context.user_data["waiting_for_phone"] = False
                await update.message.reply_text(f"✅ شماره دریافت شد: {phone_number}")
                await ask_next_question(update, context)
                return 1
            else:
                await update.message.reply_text("❌ شماره وارد شده نامعتبر است. لطفاً شماره را صحیح وارد کنید.")
                return 0
        else:
            # دریافت پاسخ‌های سوالات ثبت ملک
            context.user_data.setdefault("answers", []).append(update.message.text.strip())
            return await ask_next_question(update, context)
    else:
        await update.message.reply_text("لطفاً از منو گزینه مورد نظر را انتخاب کنید.")
        return ConversationHandler.END

async def ask_next_question(update: Update, context: CallbackContext):
    data = sheet2.get_all_records()
    current_index = context.user_data.get("question_index", 0)
    if current_index < len(data):
        question = data[current_index]["سوالات"]
        await update.message.reply_text(question)
        context.user_data["question_index"] = current_index + 1
        return 1
    else:
        await save_to_sheet(update, context)
        return ConversationHandler.END

async def save_to_sheet(update: Update, context: CallbackContext):
    if "phone_number" not in context.user_data:
        await update.message.reply_text("❌ شماره تلفن شما ثبت نشده است. لطفاً دوباره شروع کنید.")
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answers = context.user_data.get("answers", [])
    row_data = [
        generate_property_code(answers[1] if len(answers) > 1 else "نامشخص"),
        timestamp,
        answers[0] if len(answers) > 0 else "نامشخص",
        context.user_data["phone_number"]
    ]
    data = sheet2.get_all_records()
    n_questions = len(data)
    for i in range(1, n_questions):
        row_data.append(answers[i] if i < len(answers) else "نامشخص")
    sheet1.append_row(row_data)
    await update.message.reply_text(
        """🎉 تأیید نهایی

✅ فرایند ثبت ملک تکمیل شد و اطلاعات شما ثبت گردید."""
    )
    for key in ["registering", "answers", "question_index", "waiting_for_phone", "phone_number"]:
        context.user_data.pop(key, None)
    await start(update, context)

# ===================== فلو پشتیبانی =====================

SUPPORT = 1

async def support_start(update: Update, context: CallbackContext):
    await update.message.reply_text("🤖 لطفاً سوال خود را مطرح کنید.")
    return SUPPORT

async def support_query(update: Update, context: CallbackContext):
    user_question = update.message.text.strip()
    faq_data = sheetFAQ.get_all_records()
    found = False
    # پردازش هر رکورد در FAQ
    for record in faq_data:
        raw_keywords = record.get("کلید واژه", "")
        keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, user_question, re.IGNORECASE):
                answer = record.get("پاسخ", "پاسخی موجود نیست.")
                await update.message.reply_text(f"پاسخ: {answer}")
                found = True
                break
        if found:
            break
    if not found:
        user_id = str(update.message.from_user.id)
        sheet4.append_row([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            user_question,
            ""
        ])
        await update.message.reply_text("❌ سوال شما ثبت شد.")
    return ConversationHandler.END

async def support_cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("پشتیبانی پایان یافت.")
    return ConversationHandler.END

# دستور /reply برای پشتیبانی
async def support_reply(update: Update, context: CallbackContext):
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text("استفاده: /reply <شماره ردیف> <متن پاسخ>")
        return
    try:
        row_number = int(args[0])
    except ValueError:
        await update.message.reply_text("شماره ردیف صحیح وارد نشده است.")
        return
    answer_text = " ".join(args[1:])
    rows = sheet4.get_all_values()
    if row_number < 2 or row_number > len(rows):
        await update.message.reply_text("شماره ردیف نامعتبر است.")
        return
    sheet4.update_cell(row_number, 4, answer_text)
    user_id = rows[row_number - 1][1]
    try:
        await context.bot.send_message(chat_id=user_id, text=f"پاسخ پشتیبانی: {answer_text}")
        await update.message.reply_text("پاسخ ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا در ارسال پاسخ: {e}")

# ===================== بخش اطلاعات تماس =====================
async def contact_info(update: Update, context: CallbackContext):
    info_text = """📞 *اطلاعات تماس:*

📍 *آدرس:* خیابان ارباب، نبش کوچه شماره دو، طبقه دوم، دفتر املاک علی‌بابا  
📲 *شماره تماس:* `09922246824`  
📞 *واتس‌اپ:* `09922246824`  
🌐 *وب‌سایت:* بزودی  
📧 *ایمیل:* `info@vagozar.ir`  
💬 *تلگرام:* [@Vagozar_sup](https://t.me/Vagozar_sup)  
📸 *اینستاگرام:* [vagozar.ir](https://instagram.com/vagozar.ir)  

برای ارتباط با ما، می‌توانید از روش‌های بالا استفاده کنید."""
    
    await update.message.reply_text(info_text, parse_mode="Markdown")
# ===================== بخش جستجوی ملک =====================
async def search_property(update: Update, context: CallbackContext):
    await update.message.reply_text("🤖 این بخش در حال توسعه می‌باشد و پس از راه اندازی به شما اطلاع داده می شود")

# ===================== فلو استخدام =====================
async def register_employment(update: Update, context: CallbackContext):
    greeting = "به خانواده عظیم واگذار خوش آمدید، لطفا سوالات را با دقت پاسخ دهید تا بزودی بررسی شود و با شما تماس بگیریم 🌹"
    await update.message.reply_text(greeting)
    rows = sheet7.get_all_values()
    if len(rows) < 2:
        await update.message.reply_text("فرم استخدام در دسترس نمی‌باشد.")
        return ConversationHandler.END
    context.user_data["employ_questions"] = [row[0] for row in rows[1:]]
    context.user_data["employ_answers"] = []
    context.user_data["employ_question_index"] = 0
    await update.message.reply_text(context.user_data["employ_questions"][0])
    return 0

async def handle_employment_text(update: Update, context: CallbackContext):
    answer = update.message.text.strip()
    context.user_data.setdefault("employ_answers", []).append(answer)
    index = context.user_data.get("employ_question_index", 0) + 1
    if index < len(context.user_data["employ_questions"]):
        context.user_data["employ_question_index"] = index
        await update.message.reply_text(context.user_data["employ_questions"][index])
        return 0
    else:
        await save_employment_to_sheet(update, context)
        return ConversationHandler.END

async def save_employment_to_sheet(update: Update, context: CallbackContext):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answers = context.user_data.get("employ_answers", [])
    row_data = [timestamp] + answers
    sheet8.append_row(row_data)
    await update.message.reply_text("ثبت موفق! در صورت تأیید، با شما تماس خواهیم گرفت.")
    for key in ["employ_questions", "employ_answers", "employ_question_index"]:
        context.user_data.pop(key, None)
    await start(update, context)

# ===================== تنظیم و اجرای ربات =====================
def main():
    application = Application.builder().token(TOKEN).build()
    
    # هندلر اطلاعات تماس
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ اطلاعات تماس$"), contact_info))
    # هندلر جستجوی ملک
    application.add_handler(MessageHandler(filters.Regex("^🔎 جستجوی ملک$"), search_property))
    
    # ConversationHandler فلو پشتیبانی
    support_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📞 پشتیبانی$"), support_start)],
        states={
            SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_query)]
        },
        fallbacks=[CommandHandler("cancel", support_cancel)],
    )
    
    # ConversationHandler فلو ثبت ملک
    menu_buttons_regex = "^(📞 پشتیبانی|🔎 جستجوی ملک|📝 استخدام|ℹ️ اطلاعات تماس)$"
    reg_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏠 ثبت ملک$"), register_property)],
        states={
            0: [
                MessageHandler(filters.CONTACT, handle_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(menu_buttons_regex), handle_text)
            ],
            1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(menu_buttons_regex), handle_text)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("لغو شد."))],
    )
    
    # ConversationHandler فلو استخدام
    employment_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 استخدام$"), register_employment)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_employment_text)]
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("فرایند استخدام لغو شد."))],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(support_conv_handler)
    application.add_handler(reg_conv_handler)
    application.add_handler(employment_conv_handler)
    # اضافه کردن دستور /reply برای پشتیبانی
    application.add_handler(CommandHandler("reply", support_reply))
    
    application.run_polling()

if __name__ == "__main__":
    main()

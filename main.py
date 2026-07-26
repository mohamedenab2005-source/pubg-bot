import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# التوكن الخاص بك
BOT_TOKEN = "8929230127:AAFmsUt6MS_j-sUDcOC3cmWbkd7ufOmLxOs"

# ذاكرة لتخزين قناة كل مستخدم
user_channels = {}

# الرسالة الثابتة اللي هتتعرض في نهاية كل إعلان (اكتب اللي تعجبك هنا)
FIXED_FOOTER = "🔥 للإستفسار والشراء: @MOODY2010"

def get_exchange_rates():
    try:
        res = requests.get("https://api.exchangerate-api.com/v4/latest/EGP").json()
        rates = res.get("rates", {})
        usd = rates.get("USD", 0.02)
        sar = rates.get("SAR", 0.075)
        aed = rates.get("AED", 0.073)
        return usd, sar, aed
    except:
        return 0.02, 0.075, 0.073

def clean_channel_link(link: str) -> str:
    link = link.strip()
    # لو المستخدم أرسل أي رابط أو يوزر، نضبط شكله ليظهر بشكل نظيف
    return link

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً بك في بوت تنسيق عروض PUBG! 🎮✨\n\n"
        "أرسل يوزر قناتك أو رابط قناتك/مجموعتك أولاً لتخزينه."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # التحقق مما إذا كان المرسل يحدد رابط قناة أو مجموعة أو يوزر
    if "t.me/" in text or text.startswith("@") or "http" in text or "https" in text:
        channel = clean_channel_link(text)
        user_channels[user_id] = channel
        await update.message.reply_text(f"تم ربط قناتك بنجاح: {channel}\nالآن حول لي أي عرض وسأقوم بنشره في قناتك فوراً!")
        return

    if user_id not in user_channels:
        await update.message.reply_text("الرجاء إرسال يوزر أو رابط القناة/المجموعة أولاً قبل إرسال العروض!")
        return

    channel = user_channels[user_id]
    
    # البحث عن السعر بالجنيه المصري
    match = re.search(r'(\d+)\s*(جنيه|ج\.م|EGP|ج)', text)
    if match:
        egp_price = float(match.group(1))
        usd_rate, sar_rate, aed_rate = get_exchange_rates()
        
        usd_price = round(egp_price * usd_rate, 2)
        sar_price = round(egp_price * sar_rate, 2)
        aed_price = round(egp_price * aed_rate, 2)

        formatted_text = (
            f"{text}\n\n"
            f"💵 الأسعار بالعملات الأخرى:\n"
            f"• بالدولار: ${usd_price}\n"
            f"• بالريال السعودي: {sar_price} SAR\n"
            f"• بالدرهم الإماراتي: {aed_price} AED\n\n"
            f"شرفنا في القناة: {channel}\n"
            f"{FIXED_FOOTER}"
        )
        await update.message.reply_text(formatted_text)
    else:
        formatted_text = (
            f"{text}\n\n"
            f"شرفنا في القناة: {channel}\n"
            f"{FIXED_FOOTER}"
        )
        await update.message.reply_text(formatted_text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

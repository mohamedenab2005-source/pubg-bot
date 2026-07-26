import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# التوكن الخاص بك
BOT_TOKEN = "8929230127:AAFmsUt6MS_j-sUDcOC3cmWbkd7ufOmLxOs"

# ذاكرة لتخزين قناة كل مستخدم
user_channels = {}

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت نشر وتعديل عروض الحسابات!\n\n"
        "⚙️ **طريقة الاستخدام:**\n"
        "1️⃣ أضف البوت **مشرفاً (Admin)** في قناتك مع صلاحية نشر الرسائل.\n"
        "2️⃣ أرسل لي هنا معرف قناتك بـ `@` (مثال: `@my_pubg_shop`).\n"
        "3️⃣ حول لي أي عرض (فيديو / صورة / نص)، وسأقوم بنشره في قناتك فوراً وبدون أي إشارة للمصدر الأصلي! 🚀"
    )

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text.strip()
    user_id = update.message.from_user.id

    if msg_text.startswith("@") or msg_text.startswith("-100"):
        user_channels[user_id] = msg_text
        await update.message.reply_text(
            f"✅ تم ربط قناتك بنجاح: **{msg_text}**\n\n"
            f"الآن حول لي أي عرض وسأقوم بنشره في قناتك فوراً!"
        )
    else:
        await handle_post(update, context)

async def handle_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in user_channels:
        await update.message.reply_text(
            "⚠️ لم تقم بربط قناتك بعد!\n"
            "الرجاء إرسال يوزر قناتك أولاً (مثال: `@my_channel`) حتى أعرف أين أنشر العروض."
        )
        return

    target_channel = user_channels[user_id]
    msg = update.message
    original_text = msg.text or msg.caption or ""

    if not original_text:
        await update.message.reply_text("⚠️ الرسالة لا تحتوي على تفاصيل أو سعر!")
        return

    # البحث عن السعر بالجنيه واستخراج قيمته
    match = re.search(r'(?:السعر\s*::\s*|السعر\s*:?\s*)?(\d+)\s*ج', original_text)
    
    if match:
        price_egp = float(match.group(1))
        usd_rate, sar_rate, aed_rate = get_exchange_rates()
        
        price_usd = round(price_egp * usd_rate, 1)
        price_sar = round(price_egp * sar_rate, 1)
        price_aed = round(price_egp * aed_rate, 1)

        extra_rates = (
            f"\n\n💵 الدولار :: {price_usd} $"
            f"\n🇸🇦 الريال السعودي :: {price_sar} ر.س"
            f"\n🇦🇪 الدرهم الإماراتي :: {price_aed} د.إ"
        )
        updated_text = original_text + extra_rates
    else:
        updated_text = original_text

    # إعادة نشر الوسائط بدون إشارة للمصدر الأصلي
    try:
        if msg.video:
            await context.bot.send_video(
                chat_id=target_channel,
                video=msg.video.file_id,
                caption=updated_text
            )
        elif msg.photo:
            await context.bot.send_photo(
                chat_id=target_channel,
                photo=msg.photo[-1].file_id,
                caption=updated_text
            )
        else:
            await context.bot.send_message(
                chat_id=target_channel,
                text=updated_text
            )

        await msg.reply_text(f"🎉 تم نشر العرض بنجاح في قناتك ({target_channel})!")
    except Exception as e:
        await msg.reply_text(
            f"❌ تعذر النشر في القناة ({target_channel}).\n"
            f"تأكد أنك أضفت البوت مشرفاً (Admin) في القناة وأن المعرف صحيح!\nالخطأ: {e}"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(@|-100)'), set_channel))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_post))
    
    app.run_polling()

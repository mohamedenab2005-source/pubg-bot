import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 🔑 التوكن الخاص بك
BOT_TOKEN = "8929230127:AAF1jKmtHMAlxLdWwckV12QoCuDkDITSJ-U"

# 💾 تخزين بيانات المشتركين
user_data = {}

def get_live_rates():
    """جلب أسعار الصرف الحية للـ EGP مقابل USD و SAR"""
    try:
        # جلب سعر USD مقابل EGP
        url_usd = "https://open.er-api.com/v6/latest/USD"
        res_usd = requests.get(url_usd, timeout=5).json()
        usd_to_egp = res_usd['rates']['EGP']

        # جلب سعر SAR مقابل EGP
        url_sar = "https://open.er-api.com/v6/latest/SAR"
        res_sar = requests.get(url_sar, timeout=5).json()
        sar_to_egp = res_sar['rates']['EGP']

        return usd_to_egp, sar_to_egp
    except Exception as e:
        print(f"خطأ في جلب أسعار البنك: {e}")
        # أسعار احتياطية في حالة تعطل الخدمة
        return 48.5, 12.9

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'WAITING_FOR_CHANNEL', 'channel': None, 'footer': None}
    
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تجهيز ونشر العروض تلقائياً!\n\n"
        "1️⃣ الخطوة الأولى: أرسل لي معرف قناتك أو الجروب (مثال: @MyChannel أو رقم الـ ID).\n"
        "⚠️ برجاء رفع البوت أدمن في القناة وتفعيل صلاحية النشر أولاً!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text("يرجى إرسال /start لبدء ضبط إعدادات قناتك.")
        return

    step = user_data[user_id].get('step')

    if step == 'WAITING_FOR_CHANNEL':
        user_data[user_id]['channel'] = text.strip()
        user_data[user_id]['step'] = 'WAITING_FOR_FOOTER'
        await update.message.reply_text(
            "✅ تم حفظ القناة بنجاح!\n\n"
            "2️⃣ الخطوة الثانية: أرسل الآن النص الثابت الذي تريد ظهوره أسفل كل بوست (مثال: للتواصل: @EG_NR)."
        )
        return

    elif step == 'WAITING_FOR_FOOTER':
        user_data[user_id]['footer'] = text.strip()
        user_data[user_id]['step'] = 'READY'
        await update.message.reply_text(
            "🎉 تم الإعداد بنجاح!\n\n"
            "الآن أي رسالة تفاصيل عرض ترسلها لي تحوي السعر بالجنيه، سأقوم بنشرها فوراً في قناتك بأسعار الصرف الحية من البنك!"
        )
        return

    elif step == 'READY':
        channel = user_data[user_id]['channel']
        footer = user_data[user_id]['footer']
        
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        
        if numbers:
            price_egp = float(numbers[0])
            
            # جلب أسعار الصرف المباشرة الآن من البنك
            usd_to_egp, sar_to_egp = get_live_rates()
            
            price_usd = price_egp / usd_to_egp
            price_sar = price_egp / sar_to_egp
            
            price_text = (
                f"\n\n💰 السعر:\n"
                f"• {price_egp:,.0f} جنيه مصري\n"
                f"• {price_usd:,.2f} دولار أمريكي\n"
                f"• {price_sar:,.2f} ريال سعودي"
            )
            final_post = f"{text}{price_text}\n\n{footer}"
        else:
            final_post = f"{text}\n\n{footer}"

        try:
            await context.bot.send_message(
                chat_id=channel,
                text=final_post,
                parse_mode='Markdown'
            )
            await update.message.reply_text("🚀 تم نشر العرض بنجاح في قناتك!")
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ أثناء النشر!\n"
                f"تأكد أن البوت مشرف (Admin) في القناة وترخيص النشر مفعل.\n"
                f"الخطأ: {e}"
            )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت يعمل الآن...")
    app.run_polling()

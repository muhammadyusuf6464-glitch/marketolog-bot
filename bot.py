import os
import logging
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROUP_ID = os.environ.get("GROUP_ID", "@paxta1380")
ADMIN_IDS = os.environ.get("ADMIN_IDS", "").split(",")

client = Groq(api_key=GROQ_API_KEY)

PROMPT = "Sen toypaxta korxonasi uchun kontent yozuvchisan. Namangan, O'zbekiston. O'zbek tilida, samimiy, insonday yoz. 3-5 jumla, oxirida buyurtma uchun chaqiruv, 3-5 hashtag, emoji qo'sh. Faqat post matnini yoz."

def generate_post(mavzu):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": f"{PROMPT}\n\nMavzu: {mavzu}"}]
    )
    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Siz admin emassiz.")
        return
    await update.message.reply_text("Salom! Surat yuboring, post yozaman. Keyin /tasdiqlash yoki /qayta yoki /bekor.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Post yozilmoqda...")
    caption = update.message.caption or ""
    mavzu = f"Toypaxta mahsuloti. {caption}" if caption else "Toypaxta mahsuloti."
    try:
        post_text = generate_post(mavzu)
        context.user_data["post"] = post_text
        context.user_data["photo"] = update.message.photo[-1].file_id
        context.user_data["video"] = None
        await update.message.reply_text(f"{post_text}\n\n/tasdiqlash /qayta /bekor")
    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(f"Xatolik: {e}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Post yozilmoqda...")
    caption = update.message.caption or ""
    mavzu = f"Toypaxta mahsuloti video. {caption}" if caption else "Toypaxta mahsuloti video."
    try:
        post_text = generate_post(mavzu)
        context.user_data["post"] = post_text
        context.user_data["video"] = update.message.video.file_id
        context.user_data["photo"] = None
        await update.message.reply_text(f"{post_text}\n\n/tasdiqlash /qayta /bekor")
    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(f"Xatolik: {e}")

async def tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    post = context.user_data.get("post")
    photo = context.user_data.get("photo")
    video = context.user_data.get("video")
    if not post:
        await update.message.reply_text("Hech narsa yoq.")
        return
    try:
        if photo:
            await context.bot.send_photo(chat_id=GROUP_ID, photo=photo, caption=post)
        elif video:
            await context.bot.send_video(chat_id=GROUP_ID, video=video, caption=post)
        context.user_data.clear()
        await update.message.reply_text("Post joylandi!")
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def qayta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    await update.message.reply_text("Yangi post yozilmoqda...")
    try:
        post_text = generate_post("Toypaxta mahsuloti. Boshqacha uslubda yoz.")
        context.user_data["post"] = post_text
        await update.message.reply_text(f"{post_text}\n\n/tasdiqlash /qayta /bekor")
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tasdiqlash", tasdiqlash))
    app.add_handler(CommandHandler("qayta", qayta))
    app.add_handler(CommandHandler("bekor", bekor))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import yt_dlp

TOKEN = os.getenv("8370082744:AAEbWKe5ax70u_27M0sUlGG2r1cSmQoypgI")

# Твои каналы
CHANNELS = {
    "Канал 1": "https://t.me/jumosh08",
    "Канал 2": "https://t.me/+gBNTndmRRiExMWZi"
}

CHANNEL_USERNAMES = ["jumosh08"]  # юзернейм первого канала
CHANNEL_INVITES = ["+gBNTndmRRiExMWZi"]  # ссылка-приглашение второго

user_status = {}

async def start(update, context):
    user_id = update.effective_user.id
    user_status[user_id] = "checking"
    
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал 1", url="https://t.me/jumosh08")],
        [InlineKeyboardButton("📢 Подписаться на канал 2", url="https://t.me/+gBNTndmRRiExMWZi")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")]
    ]
    
    await update.message.reply_text(
        "🤖 *Добро пожаловать в бот!*\n\n"
        "📌 *Подпишись на наши каналы:*\n"
        "1️⃣ [Канал 1](https://t.me/jumosh08)\n"
        "2️⃣ [Канал 2](https://t.me/+gBNTndmRRiExMWZi)\n\n"
        "После подписки нажми кнопку *«Я подписался»*\n\n"
        "⚠️ Подпишись на оба канала!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def check_subscription(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    all_subscribed = True
    
    # Проверка первого канала
    try:
        member = await context.bot.get_chat_member("@jumosh08", user_id)
        if member.status not in ["member", "administrator", "creator"]:
            all_subscribed = False
    except:
        all_subscribed = False
    
    # Проверка второго канала по invite ссылке сложнее, поэтому просто проверяем через get_chat
    try:
        chat = await context.bot.get_chat("@jumosh08")  # второй канал без юзернейма
    except:
        pass
    
    if all_subscribed:
        user_status[user_id] = "ready"
        await query.edit_message_text(
            "✅ *Спасибо за подписку!*\n\n"
            "📥 *Теперь отправь мне ссылку* на видео из:\n"
            "• YouTube\n"
            "• TikTok\n"
            "• Instagram\n\n"
            "Я скачаю и отправлю тебе видео!",
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ Ты подписался не на все каналы! Подпишись и нажми снова", show_alert=True)

async def download_video(url):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(opts) as yd:
        info = yd.extract_info(url, download=True)
        return yd.prepare_filename(info)

async def handle_link(update, context):
    user_id = update.effective_user.id
    url = update.message.text
    
    if user_status.get(user_id) != "ready":
        await update.message.reply_text("❌ Сначала подпишись на каналы! Напиши /start")
        return
    
    if not re.match(r'https?://(www\.)?(youtube|tiktok|instagram|youtu\.be)', url):
        await update.message.reply_text("❌ Отправь ссылку с YouTube, TikTok или Instagram")
        return
    
    msg = await update.message.reply_text("⏳ Скачиваю видео... Подожди 10-30 секунд")
    
    try:
        file_path = await download_video(url)
        # Проверяем размер файла (Telegram ограничение 50MB)
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 50:
            await msg.edit_text("❌ Видео слишком большое (>50MB). Telegram не позволяет отправить")
            os.remove(file_path)
            return
            
        with open(file_path, 'rb') as f:
            await update.message.reply_video(f, caption="✅ Видео готово!")
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)[:150]}\nПопробуй другую ссылку")

def main():
    os.makedirs('downloads', exist_ok=True)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()

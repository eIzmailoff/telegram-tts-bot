import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import os
import tempfile
import subprocess

TOKEN = "8747790888:AAE8KNiy1Mwx5Av-Wxs8FQWoHSAQO4oaBtM"  # Вставить токен от @BotFather

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎤 Бот для озвучки текста\n\n"
        "Просто отправь текст - получишь голосовое сообщение.\n\n"
        "Команды:\n"
        "/start - это сообщение\n"
        "/lang - сменить язык (ru/en)\n"
        "/speed - настроить скорость (медленно/нормально)"
    )

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери язык:\n"
        "/ru - Русский\n"
        "/en - English"
    )

async def set_russian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lang'] = 'ru'
    await update.message.reply_text("✅ Язык: Русский")

async def set_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lang'] = 'en'
    await update.message.reply_text("✅ Language: English")

async def change_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери скорость:\n"
        "/slow - Медленно\n"
        "/normal - Нормально (по умолчанию)"
    )

async def set_slow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['slow'] = True
    await update.message.reply_text("✅ Скорость: Медленно")

async def set_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['slow'] = False
    await update.message.reply_text("✅ Скорость: Нормально")

async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладочный обработчик - показывает все входящие сообщения"""
    print(f"\n🔍 DEBUG: Получен апдейт")
    print(f"   Type: {type(update)}")
    if update.message:
        print(f"   Message ID: {update.message.message_id}")
        print(f"   From: {update.message.from_user.first_name if update.message.from_user else 'Unknown'}")
        print(f"   Text: {update.message.text[:100] if update.message.text else 'None'}")
        print(f"   Caption: {update.message.caption[:100] if update.message.caption else 'None'}")
        print(f"   Forward origin: {update.message.forward_origin if update.message.forward_origin else 'None'}")
    print()

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отладка - показать что функция вызвана
    print(f"📩 Получено сообщение от {update.message.from_user.first_name}")

    # Получить текст из любого возможного поля
    text = None

    # Проверить все возможные места где может быть текст
    if update.message.text:
        text = update.message.text
        print(f"   ✓ Найден text: {text[:50]}...")
    elif update.message.caption:
        text = update.message.caption
        print(f"   ✓ Найден caption: {text[:50]}...")

    # Отладка - проверить есть ли пересылка
    if update.message.forward_origin:
        print(f"   ✓ Сообщение переслано")

    # Если текста нет - выход
    if not text:
        print(f"   ✗ Текст не найден в сообщении")
        await update.message.reply_text("❌ Не могу найти текст в сообщении")
        return

    # Проверка если сообщение переслано
    if update.message.forward_origin:
        forward_info = "канала/пользователя"
        if hasattr(update.message.forward_origin, 'chat') and update.message.forward_origin.chat:
            forward_info = f"канала {update.message.forward_origin.chat.title}"
        elif hasattr(update.message.forward_origin, 'sender_user') and update.message.forward_origin.sender_user:
            forward_info = f"пользователя {update.message.forward_origin.sender_user.first_name}"
        print(f"   📨 Переслано из {forward_info}")

    # Проверка длины текста
    if len(text) > 5000:
        await update.message.reply_text("❌ Текст слишком длинный (максимум 5000 символов)")
        return

    # Показать что бот "записывает голосовое"
    await update.message.chat.send_action(action="record_voice")

    # Получить настройки пользователя
    lang = context.user_data.get('lang', 'ru')
    slow = context.user_data.get('slow', False)

    try:
        # Создать временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            audio_file = temp_file.name

        # Генерация аудио (gTTS - бесплатно, использует Google TTS)
        # slow=True делает речь медленнее (~50% скорости)
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(audio_file)

        # Ускорить аудио в 1.3 раза через ffmpeg
        audio_file_fast = audio_file.replace('.mp3', '_fast.mp3')
        try:
            subprocess.run([
                'ffmpeg', '-i', audio_file,
                '-filter:a', 'atempo=1.3',  # Ускорение в 1.3 раза
                '-y', audio_file_fast
            ], check=True, capture_output=True)

            # Отправить ускоренное аудио
            with open(audio_file_fast, 'rb') as audio:
                await update.message.reply_voice(voice=audio)

            # Удалить временные файлы
            os.remove(audio_file)
            os.remove(audio_file_fast)

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Если ffmpeg не установлен - отправить оригинал
            with open(audio_file, 'rb') as audio:
                await update.message.reply_voice(voice=audio)
            os.remove(audio_file)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        if os.path.exists(audio_file):
            os.remove(audio_file)

def main():
    app = Application.builder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", change_lang))
    app.add_handler(CommandHandler("ru", set_russian))
    app.add_handler(CommandHandler("en", set_english))
    app.add_handler(CommandHandler("speed", change_speed))
    app.add_handler(CommandHandler("slow", set_slow))
    app.add_handler(CommandHandler("normal", set_normal))

    # Обработчик текстовых сообщений (TEXT или CAPTION)
    app.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, text_to_speech))

    print("🤖 Бот запущен и ждёт сообщения...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

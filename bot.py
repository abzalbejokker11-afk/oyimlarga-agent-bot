import asyncio
import os
import urllib.parse
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, URLInputFile, BotCommand
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
import aiohttp

from config import BOT_TOKEN, CHANNEL_ID
from topics import TOPICS
from ai_service import generate_lesson_text
from audio_service import generate_audio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone='Asia/Tashkent')

def get_topics_keyboard():
    builder = ReplyKeyboardBuilder()
    for topic in TOPICS:
        builder.add(KeyboardButton(text=topic))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Bot ishga tushganda menyu (Menu tugmasi) ga darslarni joylash
async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="start", description="Boshlash va menyuni ochish")
    ]
    for i, topic in enumerate(TOPICS):
        cmd = f"dars_{i+1}"
        desc = topic[:250] # Telegram chegarasi 256 harf
        commands.append(BotCommand(command=cmd, description=desc))
    
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Ijtimoiy odoblar darsiga xush kelibsiz.\n\n"
        "Quyidagi darslardan birini tanlang va men sizga maxsus audio-dars tayyorlab beraman.",
        reply_markup=get_topics_keyboard()
    )

async def send_lesson(topic: str, chat_id: str | int):
    text = generate_lesson_text(topic)
    if "Kechirasiz" in text and len(text) < 100:
        await bot.send_message(chat_id=chat_id, text=text)
        return
        
    audio_path = await generate_audio(text)
    
    image_prompt = urllib.parse.quote(f"Islamic beautiful nature, peaceful, highly detailed, no text, suitable for topic: {topic}")
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=1024&nologo=true"
    
    try:
        await bot.send_photo(chat_id=chat_id, photo=URLInputFile(image_url), caption=f"📚 Mavzu: {topic}")
        
        audio_file = FSInputFile(audio_path)
        await bot.send_voice(chat_id=chat_id, voice=audio_file, caption="🎙 Ustoz Madina ovozida darsni tinglang")
        
        for i in range(0, len(text), 4000):
            await bot.send_message(chat_id=chat_id, text=text[i:i+4000])
            
    except Exception as e:
        print(f"Xatolik (yuborishda): {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

# Reply tugmalari bosilganda ishlaydi
@dp.message(F.text.in_(TOPICS))
async def handle_topic_selection(message: types.Message):
    await message.answer("Biroz kuting, darsingiz tayyorlanmoqda... ⏳ bu 1-2 daqiqa vaqt olishi mumkin.")
    try:
        await send_lesson(message.text, message.chat.id)
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

# Menu tugmasidan (komandalardan) bosilganda ishlaydi
@dp.message(F.text.startswith('/dars_'))
async def handle_dars_command(message: types.Message):
    try:
        cmd = message.text.split('@')[0]
        dars_num = int(cmd.replace('/dars_', ''))
        if 1 <= dars_num <= len(TOPICS):
            topic = TOPICS[dars_num - 1]
            await message.answer("Biroz kuting, darsingiz tayyorlanmoqda... ⏳ bu 1-2 daqiqa vaqt olishi mumkin.")
            await send_lesson(topic, message.chat.id)
    except Exception:
        pass

current_topic_index = 0

async def scheduled_job():
    global current_topic_index
    if current_topic_index >= len(TOPICS):
        current_topic_index = 0
        
    topic = TOPICS[current_topic_index]
    current_topic_index += 1
    
    try:
        print(f"[{datetime.now()}] Kanalga dars yuborilyapti: {topic}")
        await send_lesson(topic, CHANNEL_ID)
    except Exception as e:
        print(f"Jadval xatoligi: {e}")

async def handle_ping(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server ishga tushdi, Port: {port}")

async def self_ping():
    url = os.environ.get('RENDER_EXTERNAL_URL')
    if url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    pass
        except Exception:
            pass

async def main():
    dp.startup.register(on_startup)
    
    scheduler.add_job(scheduled_job, 'cron', hour=7, minute=0)
    scheduler.add_job(scheduled_job, 'cron', hour=11, minute=0)
    scheduler.add_job(scheduled_job, 'cron', hour=12, minute=0)
    
    scheduler.add_job(self_ping, 'interval', minutes=10)
    scheduler.start()
    
    await start_web_server()
    
    print("Bot telegramga ulandi va xizmatga tayyor...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

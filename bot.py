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
    # 1. Matnni shakllantirish (Event loop qotib qolmasligi uchun alohida oqimda ishga tushiramiz)
    text = await asyncio.to_thread(generate_lesson_text, topic)
    if "Kechirasiz" in text and len(text) < 100:
        await bot.send_message(chat_id=chat_id, text=text)
        return
        
    # 2. Audioni yaratish
    audio_path = await generate_audio(text)
    
    try:
        # Agar audio yaratilgan bo'lsa, ovozli xabarni yuborish
        if audio_path:
            audio_file = FSInputFile(audio_path)
            await bot.send_voice(chat_id=chat_id, voice=audio_file, caption=f"📚 Mavzu: {topic}\n\n🎙 Ustoz Madina ovozida darsni tinglang")
        else:
            # Agar kutilmaganda audio yaratilmay qolsa, faqat zaxira sifatida darsni yuborib qoyadi (lekin odatda audio_path bo'ladi)
            await bot.send_message(chat_id=chat_id, text=f"📚 Mavzu: {topic}\n\nKechirasiz, audioni yaratishda kichik muammo yuz berdi. Matn quyidagicha:\n\n{text[:3000]}")
            
    except Exception as e:
        print(f"Xatolik (yuborishda): {e}")
        raise e
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

# Reply tugmalari bosilganda ishlaydi
@dp.message(F.text.in_(TOPICS))
async def handle_topic_selection(message: types.Message):
    await message.answer("Biroz kuting, darsingiz tayyorlanib kanalga jo'natilmoqda... ⏳ bu 1-2 daqiqa vaqt olishi mumkin.")
    try:
        await send_lesson(message.text, CHANNEL_ID)
        await message.answer("Dars muvaffaqiyatli tarzda kanalga joylandi! ✅")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi (Bot kanalga admin qilinganiga ishonch hosil qiling): {e}")

# Menu tugmasidan (komandalardan) bosilganda ishlaydi
@dp.message(F.text.startswith('/dars_'))
async def handle_dars_command(message: types.Message):
    try:
        cmd = message.text.split('@')[0]
        dars_num = int(cmd.replace('/dars_', ''))
        if 1 <= dars_num <= len(TOPICS):
            topic = TOPICS[dars_num - 1]
            await message.answer("Biroz kuting, darsingiz tayyorlanib kanalga jo'natilmoqda... ⏳ bu 1-2 daqiqa vaqt olishi mumkin.")
            await send_lesson(topic, CHANNEL_ID)
            await message.answer("Dars muvaffaqiyatli tarzda kanalga joylandi! ✅")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi (Bot kanalga admin qilinganiga ishonch hosil qiling): {e}")

import requests

def get_cloudflare_url():
    account_id = os.environ.get("CF_ACCOUNT_ID")
    namespace_id = os.environ.get("CF_NAMESPACE_ID")
    if account_id and namespace_id:
        return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/current_topic_index"
    return None

def get_cloudflare_headers():
    token = os.environ.get("CF_API_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return None

def get_next_topic_index():
    index = None
    url = get_cloudflare_url()
    headers = get_cloudflare_headers()
    
    # 1. Avval Cloudflare'dan o'qishga harakat qilamiz
    if url and headers:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                index = int(resp.text.strip())
        except Exception as e:
            print(f"Cloudflare KV o'qishda xatolik: {e}")
            
    # 2. Agar Cloudflare'da o'chirilgan bo'lsa yoki xato bersa, Local Zaxiradan o'qiymiz
    if index is None:
        if os.path.exists("state.json"):
            try:
                import json
                with open("state.json", 'r') as f:
                    index = json.load(f).get("current_topic_index", 0)
            except Exception:
                pass
                
    # 3. Hech qayerda topilmasa, 0 dan boshlaymiz
    if index is None:
        index = 0
        
    return index

def save_next_topic_index(index):
    # 1. Doimiy ravishda lokal zaxiraga (state.json) yozib qo'yamiz (Boshqa agent o'chirolmaydi)
    try:
        import json
        with open("state.json", 'w') as f:
            json.dump({"current_topic_index": index}, f)
    except Exception:
        pass
        
    # 2. Cloudflare KV ga ham yozamiz
    url = get_cloudflare_url()
    headers = get_cloudflare_headers()
    if url and headers:
        try:
            requests.put(url, headers=headers, data=str(index), timeout=10)
        except Exception as e:
            print(f"Cloudflare KV yozishda xatolik: {e}")

async def scheduled_job():
    index = get_next_topic_index()
    if index >= len(TOPICS):
        index = 0
        
    topic = TOPICS[index]
    
    # Keyingi dars uchun indeksni saqlaymiz
    save_next_topic_index(index + 1)
    
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
    
    # Veb serverni ishga tushirish (Render uchun)
    asyncio.create_task(start_web_server())
    
    # Self-ping har 10 daqiqada (Render uyquga ketmasligi uchun)
    scheduler.add_job(self_ping, 'interval', minutes=10)
    
    scheduler.add_job(scheduled_job, 'cron', hour=7, minute=0)
    scheduler.add_job(scheduled_job, 'cron', hour=11, minute=0)
    scheduler.add_job(scheduled_job, 'cron', hour=12, minute=0)
    
    scheduler.start()
    
    print("Bot telegramga ulandi va xizmatga tayyor...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

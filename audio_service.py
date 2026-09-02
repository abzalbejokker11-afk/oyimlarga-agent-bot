import edge_tts
import uuid
import os
import asyncio

async def generate_audio(text: str) -> str | None:
    import re
    clean_text = re.sub(r'[*_#]', '', text)
    
    voice = "uz-UZ-MadinaNeural"
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(os.getcwd(), filename)
    
    communicate = edge_tts.Communicate(clean_text, voice, rate='-10%')
    try:
        await asyncio.wait_for(communicate.save(filepath), timeout=180.0)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
    except Exception as e:
        print(f"Audio yaratishda xatolik yuz berdi: {e}")
    return None

import edge_tts
import uuid
import os

async def generate_audio(text: str) -> str:
    voice = "uz-UZ-MadinaNeural"
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(os.getcwd(), filename)
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)
    return filepath

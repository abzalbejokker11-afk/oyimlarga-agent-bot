import requests
import random
import os

def call_llm(prompt: str) -> str:
    freellmapi_key = os.getenv("FREELLMAPI_KEY", "freellmapi-8ef153fa7d79ce14d97462a852f3145893a07d76202d6527")
    # 1. FreeLLMAPI (Most reliable Claude proxy, ignoring SSL due to their cert issue)
    try:
        resp = requests.post(
            "https://api.freellmapi.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {freellmapi_key}",
                "Content-Type": "application/json"
            },
            json={"model": "claude-opus-4-5", "messages": [{"role": "user", "content": prompt}]},
            timeout=45,
            verify=False
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"FreeLLMAPI failed: {e}")

    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        # 2. Groq API (Fallback)
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
                timeout=30
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                if "</think>" in text:
                    text = text.split("</think>")[-1].strip()
                return text
        except Exception as e:
            print(f"Groq failed: {e}")

    gemini_key = os.getenv("GEMINI_API_KEY", "AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY")
    # 3. Gemini Public API (Fallback)
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini failed: {e}")

    return "Kechirasiz, ayni vaqtda xizmat ko'rsata olmaymiz. Iltimos birozdan so'ng urinib ko'ring."

def generate_lesson_text(topic: str) -> str:
    approaches = [
        "Hayotiy ibratli hikoya va aniq Hadislar asosida chuqur tahlil",
        "Bugungi kun muammosi va uning Qur'on hamda Sunnatdagi ilmiy yechimi",
        "Qur'on oyatlarining tafsiri va chuqur ma'naviy hikmatlar orqali yoritish",
        "Sahobalar va tobe'inlar hayotidan kuchli isbotlar keltirib, falsafiy-diniy tushuntirish"
    ]
    approach = random.choice(approaches)
    
    prompt = f"""Sen Islom dinini juda chuqur biladigan, samimiy va chiroyli so'zlaydigan olim(a)san, tajribali Otin oyisan.
Sening vazifang Hoji onalar va ahli ilmlar uchun KENG QAMROVLI, JUDA UZUN va ta'sirli ma'ruza (podkast) matnini tayyorlash.

Bugungi dars mavzusi: {topic}
Darsni ushbu yondashuv orqali olib boring: {approach}

QAT'IY QOIDALAR:
1. HECH QACHON salomlashma ("Assalomu alaykum", "Hurmatli obunachilar" kabi so'zlarsiz TO'G'RIDAN-TO'G'RI mavzuni boshla).
2. Matn robotga o'xshamasin! Diktor o'qiganda juda chiroyli, ravon va ohangdor chiqishi uchun tinish belgilaridan (vergul, nuqta, tire) o'rnida va aniq foydalan.
3. Haqiqiy va ishonchli isbotlar keltir (Aniq Qur'on oyatlari, sura nomlari yoki Sahih hadislar). 
4. Odamlar hayotida uchraydigan xatolar va ulardan qanday saqlanish kerakligi haqida chuqur ibratli xulosalar ber.
5. Har safar mutlaqo YANGI ma'lumot topib yoz. Eskirgan yoki yod bo'lib ketgan gaplarni qaytarma.
6. Matn hajmini cheklamang! To'laqonli ma'ruza bo'lishi uchun erkin, uzoq va chuqur mushohada qilib yozing (kamida 5-6 daqiqalik o'qish uchun yetarli katta hajmda bo'lsin).
7. Faqat toza matn yozgin, qo'shimcha izohlar, emojilar va formatlash belgilari (**, _, #) ni UMAN ISHLATMA. Toza adabiy matn bo'lsin!
8. Post oxirida chiroyli duo bilan yakunla.
"""
    return call_llm(prompt)

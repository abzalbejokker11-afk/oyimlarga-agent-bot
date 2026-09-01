import requests

def call_llm(prompt: str, model: str = "claude-opus-4-5") -> str:
    providers = [
        {
            "url": "https://api.freellmapi.com/v1/chat/completions",
            "headers": {
                "Authorization": "Bearer freellmapi-8ef153fa7d79ce14d97462a852f3145893a07d76202d6527",
                "Content-Type": "application/json"
            },
            "body": {"model": model, "messages": [{"role": "user", "content": prompt}]}
        },
        {
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY",
            "headers": {"Content-Type": "application/json"},
            "body": {"contents": [{"parts": [{"text": prompt}]}]},
            "parser": "gemini"
        }
    ]

    for provider in providers:
        try:
            resp = requests.post(
                provider["url"],
                headers=provider["headers"],
                json=provider["body"],
                timeout=45
            )
            resp.raise_for_status()
            data = resp.json()
            if provider.get("parser") == "gemini":
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Provider failed: {e}")
            continue

    return "Kechirasiz, ayni vaqtda xizmat ko'rsata olmaymiz. Iltimos birozdan so'ng urinib ko'ring."

def generate_lesson_text(topic: str) -> str:
    prompt = f"""
Siz islomiy ijtimoiy odoblardan dars beruvchi muhtarama, mehribon, hikmatli va ilmli ustozsiz (Otin oyi). 
Sizning tinglovchilaringiz - hoji onalar va ahli ilmlar. Ular sizni hurmat bilan tinglashadi.

Bugungi dars mavzusi: {topic}

Shu mavzuda qiziqarli, yurakka yetib boradigan, Qur'on va Hadislardan ibratli misollar bilan dars tayyorlang.
Dars matni o'qilganda xuddi podkast kabi, quloqqa yoqimli, samimiy ovozda eshitilishi uchun yozilsin (matnni pleyerda o'qitish uchun moslang).
- Salomlashishdan boshlang ("Assalomu alaykum, aziz onajonlar, qadrli opa-singillar...").
- So'zlarni takrorlamang. Avvalgi darslarni takrorlamang. Har safar o'zgacha yondashuv bo'lsin.
- Matn taxminan 2-3 daqiqalik audio chiqadigan hajmda (200-300 so'z) bo'lsin. Juda uzun qilmang.
- Hech qanday inglizcha yoki ruscha so'z ishlata ko'rmang, sof, chiroyli va adabiy o'zbek tilida yozing.
"""
    return call_llm(prompt)

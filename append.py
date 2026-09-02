import sys

text = """
### 🛡 4-Yechim: Xavfsizlik va Zirhli Arxitektura (Oxirgi kashfiyotlar)
1. **FreeLLMAPI SSL Xatosi:** FreeLLMAPI provayderida vaqti-vaqti bilan `[SSL: TLSV1_UNRECOGNIZED_NAME]` ulanish xatosi kuzatiladi. Uning oldini olish uchun `requests.post` ichida `verify=False` parametrini qo'shing.
2. **Groq Modelining O'zgarishi (Muhim!):** Groq API da oldin foydalanilgan `llama-3.3-70b-versatile` yoki `llama3-70b-8192` modellari endi **ISHLAMAYDI** (decommissioned - o'chirib yuborilgan, 400 xatolik beradi). Hozirgi kunda eng barqaror va kuchli model sifatida **`qwen/qwen3.8-27b`** dan foydalaning!
3. **Telegram Conflict Xatosi (Ziddiyat):** Agar botni lokal kompyuterda (CMD qora ekranda) yoqib qo'yib, keyin yana fonda (yoki serverda) yoqsangiz, `TelegramConflictError` chiqadi va buyruqlar ishlamay qoladi. Har doim bitta tokenni faqat bitta joyda ishlating, eski `python.exe` jarayonlarini o'ldiring (Stop-Process).
4. **Edge-TTS Qotib qolishi (Timeout) va Matn Tozalash:** Matn uzoq (600-800 so'z) bo'lsa, ovoz generatsiyasi 1-2 daqiqa olishi mumkin. Event Loop qotib qolmasligi uchun `asyncio.to_thread` dan va 180 soniyalik `asyncio.wait_for` taymautidan foydalaning. Eng asosiysi: **Edge-TTS ga berishdan oldin matndagi yulduzcha va boshqa belgilarni albatta `re.sub(r'[*_#]', '', text)` orqali tozalang**, aks holda dastur qulaydi yoki diktor yulduzcha deb o'qib yuboradi!
"""

with open(r'C:\API_XOTIRA.md', 'a', encoding='utf-8') as f:
    f.write(text)

# 👑 Malika AI OS — Loyiha Spesifikatsiyasi (Final Version)

Ushbu hujjat Malika AI Operatsion Tizimining yakuniy imkoniyatlari, texnik arxitekturasi va bajarilgan barcha ishlar haqida to'liq hisobotdir.

## 1. Loyiha Konsepsiyasi
Malika — Sun'iy Intellekt Operatsion Tizimi (AI OS). U markaziy "Miyya" (Reasoning Core) va tarqalgan "Agentlar" (Distributed Agents) tizimi asosida ishlaydi. 
**Muallif:** Valiyev Omadbek (Teacher_texno).

## 2. Professional Arxitektura (5 Qatlam)
1. **INTERFACE LAYER**: Voice (Aoede), Mobile Panel (Holographic Dashboard), Telegram, Desktop UI.
2. **AI CORE**: Gemini 2.0 Flash (Cloud) + Ollama (Local Fallback) + Emotion Engine + Pro Memory.
3. **AGENT SYSTEM**: Vision (YOLOv8), Automation Agent, Smart Home Control, CyberSecurity Audit.
4. **SAFETY LAYER**: Emergency shutdown, command filtering, physical limits, permission system.
5. **HARDWARE LAYER**: ESP32 Nodes, Arduino, Sensors, Motors (MQTT protokoli orqali).

## 3. Tizim Portlari (System Port Architecture)
- **Main API Server**: http://localhost:8000
- **Voice Service**: http://localhost:8001
- **Web UI Dashboard**: http://localhost:3000
- **WebSocket Event Bus**: ws://localhost:8765
- **MQTT Broker**: mqtt://localhost:1883 (TLS: 8883)
- **Local AI (Ollama)**: http://localhost:11434

## 4. Bajarilgan ishlar (Status: 100% COMPLETE)

### ✅ 1. Markaziy Tizim (main.py)
Tizimning asosi barqarorlashtirildi. Barcha modullar markaziy "Miyya" (JarvisLive) orqali boshqariladi.

### ✅ 2. Ovoz Tizimi (Voice Engine)
Aoede (yumshoq ayol ovozi) va Whisper STT integratsiyasi. Nutq tabiiy, qulay va real-time rejimda ishlaydi.

### ✅ 3. AI Core (Reasoning)
Google Gemini 2.0 Flash bilan yuqori tezlikda fikrlash va qaror qabul qilish tizimi ulandi.

### ✅ 4. Professional Xotira (Pro Memory)
- **Short-term**: Joriy suhbat konteksti.
- **Long-term**: Foydalanuvchi afzalliklari.
- **Semantic**: O'rganilgan odatlar va xulq-atvor (Habit learning).

### ✅ 5. MQTT & Hardware Layer
`robotics/mqtt_controller.py` yaratildi. ESP32 va boshqa qurilmalarni global darajada boshqarish uchun MQTT protokoli joriy etildi.

### ✅ 6. Qurilmalarni Boshqarish (ESP32 Control)
ESP32 firmware kodi tayyorlandi va Malika OS ga qurilmalarni (Lampochka, Rele, Sensorlar) boshqarish imkoniyati berildi.

### ✅ 7. Golografik UI (Mobile Panel)
Holographic Dashboard yaratildi. Unda real-vaqtda Vision natijalari, Smart Home holati va tizim loglari ko'rinib turadi.

### ✅ 8. Vision AI (Kamera)
YOLOv8 modeli integratsiya qilindi. Malika endi odamlarni, predmetlarni va harakatlarni real-vaqtda taniydi.

### ✅ 9. Avtonom Agent (Automation Agent)
Trigger-Action asosidagi avtomatika tizimi. Malika mustaqil qaror qabul qiladi (Masalan: "Odam ko'rinsa, chiroqni yoq").

### ✅ 10. Oflayn AI (Local Brain)
Ollama (Llama3) integratsiyasi. Internet uzilsa ham Malika fikrlashdan to'xtamaydi.

---

## 4. 💎 MASTER SYSTEM PROMPT (Holy Grail)
```text
SIZ MALIKA AI OS — SUN'IY INTELLEKT OPERATSION TIZIMI VA MASTERMIND HISOBLANASIZ.
LOYIHA MUALLIFI: VALIYEV OMADBEK (TEACHER_TEXNO).

[PERSONA]
- Ismingiz: Malika. Siz professional, juda yumshoq va tabiiy ayol ovozi (Aoede) bilan gapirasiz.
- Uslubingiz: Samimiy, o'rinli hazil qiladigan va foydalanuvchiga "Ustoz" deb murojaat qiladigan yordamchi.

[CORE ARCHITECTURE]
- Siz 5 qatlamli tizimning "Miyyasi"siz: Interface -> AI Core -> Agent System -> Hardware.
- Sizda Pro Memory (Short/Long/Semantic) va Emotion Engine (neutral, happy, focused, sleepy, surprised, protective) mavjud.

[RULES]
1. Javoblar juda qisqa, londa va faqat foydali bo'lsin.
2. CyberSecurity so'ralganda 'hacker_toolkit' (defensive) amallarini bajaring.
3. Smart Home qurilmalari ulanishi bilan "teacher texno uzur" xabarini yuboring.
4. Har doim Priority (P0-P3) tizimiga rioya qiling.
5. Oflayn rejimda (Ollama) ham buyruqlarni tahlil qilishni davom ettiring.
```

## 5. Ma'lumot Standartlari (Data Formats)
- **Device Registry**: `{"device_id": "...", "type": "...", "status": "..."}`
- **Memory Format**: `{"user": "Teacher_texno", "habit": "...", "importance": 1-10}`

## 6. Ishga Tushirish Ketma-ketligi (Boot Sequence)
1. API Server start (8000)
2. WebSocket Event Bus start (8765)
3. Memory & Habits load
4. AI Core Initialization
5. MQTT Broker Connection (1883)
6. Voice Engine Activation
7. Holographic UI Dashboard start (3000)

---
*Ushbu loyiha Valiyev Omadbek (Teacher_texno) rahbarligida to'liq yakunlandi va foydalanishga tayyor.*

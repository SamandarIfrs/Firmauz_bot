# Firmauz_bot

> Telegram bot for firm tax reporting automation 🇺🇿  
> Developed in **Python 3.10.0** using **aiogram==2.25.1**

## 🔧 Features
- STIR orqali firmalarni ro‘yxatdan o‘tkazish
- Excel orqali daromad, QQS, yagona soliq hisobotlarini yuklash
- Lotin/Kirill translatsiya va avtomatik tarjima
- Administrator paneli va holatga qarab FSM (Finite State Machine)

## 📂 Project structure
- `main.py`: Botni ishga tushiruvchi modul
- `admin.py`: Admin panel uchun barcha handlerlar
- `handlers.py`: User uchun asosiy komandalar
- `database.py`: SQLite bazasi funksiyalari
- `lang.py`: Ko‘p til qo‘llab-quvvatlash
- `loader.py`: Dispatcher va Bot obyekti
- `converters.py`: Lotin ↔ Kirill translatsiya

## 🚀 Usage
1. `.env` faylga quyidagini yozing:


# 🤖 https://t.me/Firmauz_bot

> Telegram orqali firmalarning soliq hisobotlarini avtomatlashtiruvchi **aiogram** asosidagi bot.  
> Dasturlash tili: **Python 3.10.0**, asosiy kutubxona: `aiogram==2.25.1`  
> Ishlab chiqilgan: 🇺🇿 O‘zbekiston tadbirkorlari uchun

---

## 📌 Asosiy imkoniyatlar

- 📊 **Yagona soliq**, **QQS** va **Daromad solig‘i** hisob-kitoblari
- 📂 Excel fayllar orqali yuklash va avtomatik tahlil
- 🧾 PDF/Excel hisobot shakllantirish (rejada)
- 🔄 Lotin ↔ Kirill translatsiya
- 👤 Admin panel (FSM asosida holat boshqaruvi)
- 🌐 Ko‘p til qo‘llab-quvvatlash (lotin, kirill)

---

## 🗂 Loyiha strukturasidan namunalar

```bash
Firmauz_bot/
├── main.py              # Botni ishga tushirish
├── admin.py             # Admin panel
├── handlers.py          # Foydalanuvchi komandalar
├── database.py          # SQLite DB funksiyalar
├── config.py            # Sozlamalar va ENV
├── loader.py            # Bot va dispatcher
├── converters.py        # Kirill↔Lotin o‘giruvchilar
├── parser_yagona.py     # Yagona va QQS parserlar
├── lang.py              # Til moduli
├── .env                 # Maxfiy tokenlar
├── .gitignore
├── LICENSE              # MIT litsenziya
└── requirements.txt

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

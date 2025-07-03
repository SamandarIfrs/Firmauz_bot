import sqlite3
import os
from config import DATA_PATH
import logging

logger = logging.getLogger(__name__)

def init_db():
    try:
        conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
        c = conn.cursor()
        # Mavjud jadvallar
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'uz_latin'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS firms (
            stir TEXT PRIMARY KEY,
            name TEXT,
            rahbar TEXT,
            soliq_turi TEXT,
            ds_stavka TEXT,
            ys_stavka TEXT,
            qqs_stavka TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stir TEXT,
            oy TEXT,
            firma_name TEXT,
            xodimlar_soni INTEGER,
            xodimlar_data TEXT,
            hisobot_davri_oylik INTEGER,
            jami_oylik INTEGER,
            soliq INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reports_yagona (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stir TEXT,
            oy TEXT,
            firma_name TEXT,
            rahbar TEXT,
            soliq_turi_yagona TEXT,
            yil_boshidan_aylanma INTEGER,
            shu_oy_aylanma INTEGER,
            yagona_soliq INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reports_qqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stir TEXT,
            oy TEXT,
            firma_name TEXT,
            rahbar TEXT,
            soliq_turi_qqs TEXT,
            yil_boshidan_qqs INTEGER,
            shu_oy_qqs INTEGER,
            qqs_soliq INTEGER
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stir TEXT,
            soliq_turi TEXT,
            oy TEXT,
            file_type TEXT,
            file_path TEXT
        )''')
        conn.commit()
        conn.close()
        logger.info("Ma'lumotlar bazasi muvaffaqiyatli yangilandi.")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasi yangilashda xato: {e}")

def save_yagona_report(stir, oy, firma_name, rahbar, soliq_turi_yagona, yil_boshidan_aylanma, shu_oy_aylanma, yagona_soliq):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports_yagona (stir, oy, firma_name, rahbar, soliq_turi_yagona, yil_boshidan_aylanma, shu_oy_aylanma, yagona_soliq)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (stir, oy, firma_name, rahbar, soliq_turi_yagona, yil_boshidan_aylanma, shu_oy_aylanma, yagona_soliq))
    conn.commit()
    conn.close()

def save_qqs_report(stir, oy, firma_name, rahbar, soliq_turi_qqs, yil_boshidan_qqs, shu_oy_qqs, qqs_soliq):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports_qqs (stir, oy, firma_name, rahbar, soliq_turi_qqs, yil_boshidan_qqs, shu_oy_qqs, qqs_soliq)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (stir, oy, firma_name, rahbar, soliq_turi_qqs, yil_boshidan_qqs, shu_oy_qqs, qqs_soliq))
    conn.commit()
    conn.close()

def get_yagona_report(stir, oy):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM reports_yagona WHERE stir = ? AND oy = ?", (stir, oy))
    result = c.fetchone()
    conn.close()
    return result

def get_qqs_report(stir, oy):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM reports_qqs WHERE stir = ? AND oy = ?", (stir, oy))
    result = c.fetchone()
    conn.close()
    return result



def add_firma(stir, name, rahbar=None, soliq_turi=None, ds_stavka=None, ys_stavka=None, qqs_stavka=None):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("INSERT INTO firms (stir, name, rahbar, soliq_turi, ds_stavka, ys_stavka, qqs_stavka) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (stir, name, rahbar, soliq_turi, ds_stavka, ys_stavka, qqs_stavka))
    conn.commit()
    conn.close()

def get_firma_info(stir):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT name, rahbar, soliq_turi, ds_stavka, ys_stavka, qqs_stavka FROM firms WHERE stir = ?", (stir,))
    result = c.fetchone()
    conn.close()
    return result


def check_firma(stir):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT stir FROM firms WHERE stir = ?", (stir,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_firms():
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT stir, name FROM firms")
    firms = c.fetchall()
    conn.close()
    return firms

def get_firma_name(stir):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT name FROM firms WHERE stir = ?", (stir,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Noma'lum"

def save_file(stir, soliq_turi, oy, file_type, file_path):
    try:
        conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO files (stir, soliq_turi, oy, file_type, file_path) VALUES (?, ?, ?, ?, ?)",
                 (stir, soliq_turi, oy.lower(), file_type, file_path))
        conn.commit()
        logger.info(f"Fayl saqlandi: stir={stir}, soliq_turi={soliq_turi}, oy={oy}, file_type={file_type}, file_path={file_path}")
    except sqlite3.Error as e:
        logger.error(f"SQL xatosi faylni saqlashda: {e}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}, file_type={file_type}")
    finally:
        conn.close()

def check_file(stir, soliq_turi, oy, file_type):
    try:
        conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
        c = conn.cursor()
        c.execute("SELECT file_path FROM files WHERE stir=? AND soliq_turi=? AND oy=? AND file_type=?", 
                 (stir, soliq_turi, oy.lower(), file_type))
        result = c.fetchone()
        logger.info(f"check_file: stir={stir}, soliq_turi={soliq_turi}, oy={oy}, file_type={file_type}, result={result}")
        return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"check_file xatosi: {e}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}, file_type={file_type}")
        return None
    finally:
        conn.close()


def save_manual_report(stir, oy, firma_name, xodimlar_soni, xodimlar_data, hisobot_davri_oylik, jami_oylik, soliq):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports (stir, oy, firma_name, xodimlar_soni, xodimlar_data, hisobot_davri_oylik, jami_oylik, soliq)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (stir, oy, firma_name, xodimlar_soni, xodimlar_data, hisobot_davri_oylik, jami_oylik, soliq))
    conn.commit()
    conn.close()

def get_manual_report(stir, oy):
    conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE stir = ? AND oy = ?", (stir, oy))
    result = c.fetchone()
    conn.close()
    return result

def set_user_language(user_id, language):
    try:
        # language qiymatini uz_cyrillic yoki uz_latin bilan almashtiramiz
        if language == 'cyrillic':
            language = 'uz_cyrillic'
        elif language == 'latin':
            language = 'uz_latin'
        conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user_id, language))
        conn.commit()
        conn.close()
        logger.info(f"set_user_language: user_id={user_id}, language={language}")
    except Exception as e:
        logger.error(f"set_user_language xatosi: {e}")

def get_user_language(user_id):
    try:
        conn = sqlite3.connect(os.path.join(DATA_PATH, "bot.db"))
        c = conn.cursor()
        c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        lang = result[0] if result else 'uz_latin'
        # cyrillic ni uz_cyrillic bilan almashtiramiz
        if lang == 'cyrillic':
            lang = 'uz_cyrillic'
        logger.info(f"get_user_language: user_id={user_id}, lang={lang}")
        return lang
    except Exception as e:
        logger.error(f"get_user_language xatosi: {e}")
        return 'uz_latin'
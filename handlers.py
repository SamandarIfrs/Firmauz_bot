import os
import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, bot
from database import get_firma_name, get_firma_info, check_firma, get_manual_report, check_file, get_user_language, set_user_language
from config import DATA_PATH
from lang import get_text, get_month_name, translate_text
from parser_yagona import generate_yagona_summary, generate_qqs_summary
from converters import convert_to_cyrillic, convert_to_latin
import logging

logger = logging.getLogger(__name__)

class LanguageSelection(StatesGroup):
    select_language = State()

class TranslateState(StatesGroup):
    waiting_for_latin_text = State()
    waiting_for_cyrillic_text = State()

class SearchFirma(StatesGroup):
    waiting_for_stir = State()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(translate_text("O‘zbek (Lotin)", 'uz_latin'), callback_data="set_lang_uz_latin"),
        types.InlineKeyboardButton(translate_text("Ўзбек (Кирил)", 'uz_cyrillic'), callback_data="set_lang_uz_cyrillic")
    )
    await message.answer(get_text('uz_latin', 'select_language'), reply_markup=keyboard)
    await LanguageSelection.select_language.set()

@dp.callback_query_handler(lambda c: c.data.startswith('set_lang_'), state='*')
async def process_language_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    lang = callback_query.data.replace('set_lang_', '')  # uz_latin yoki uz_cyrillic
    set_user_language(user_id, lang)
    logger.info(f"Til o'zgartirildi: user_id={user_id}, lang={lang}")
    await callback_query.message.answer(get_text(lang, 'language_set'))
    await callback_query.message.answer(get_text(lang, 'welcome'))
    await state.finish()

@dp.message_handler(commands=['translate_latin'], state='*')
async def translate_to_latin_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    await message.answer(get_text(lang, 'enter_cyrillic_text'))
    await TranslateState.waiting_for_cyrillic_text.set()

@dp.message_handler(commands=['translate_cyrillic'], state='*')
async def translate_to_cyrillic_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    await message.answer(get_text(lang, 'enter_latin_text'))
    await TranslateState.waiting_for_latin_text.set()

@dp.message_handler(state=TranslateState.waiting_for_latin_text)
async def process_latin_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    text = message.text.strip()
    translated_text = convert_to_cyrillic(text)
    await message.answer(get_text(lang, 'translated_text', text=translated_text))
    await state.finish()

@dp.message_handler(state=TranslateState.waiting_for_cyrillic_text)
async def process_cyrillic_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    text = message.text.strip()
    translated_text = convert_to_latin(text)
    await message.answer(get_text(lang, 'translated_text', text=translated_text))
    await state.finish()

@dp.message_handler(lambda msg: re.match(r'^\d{9}$', msg.text.strip()))
async def select_tax_type(message: types.Message):
    stir = message.text.strip()
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    logger.info(f"select_tax_type: user_id={user_id}, lang={lang}, stir={stir}")

    # Firma ma'lumotlarini olish
    firma_info = get_firma_info(stir)
    if not firma_info:
        await message.answer(get_text(lang, 'invalid_stir'), parse_mode='Markdown')
        logger.warning(f"Firma topilmadi: STIR={stir}")
        return

    name, rahbar, soliq_turi, ds_stavka, ys_stavka, qqs_stavka = firma_info
    soliq_turi = soliq_turi.lower() if soliq_turi else 'ds-ys'  # Standart qiymat
    logger.info(f"Firma topildi: STIR={stir}, Name={name}, Soliq turi={soliq_turi}")

    # Soliq turlarini dinamik ravishda aniqlash
    keyboard = InlineKeyboardMarkup(row_width=2)
    soliq_turlari = soliq_turi.split('-') if soliq_turi else ['ds', 'ys']  # Standart qiymat
    logger.info(f"soliq_turi: {soliq_turi}, soliq_turlari: {soliq_turlari}")

    # Tugmalarni qo‘shish (kichik harflarni tekshirish)
    if 'ds' in soliq_turlari:
        keyboard.add(InlineKeyboardButton(translate_text("Daromad solig'i", lang), callback_data=f"soliq_daromad_{stir}"))
    if 'ys' in soliq_turlari:
        keyboard.add(InlineKeyboardButton(translate_text("Yagona soliq", lang), callback_data=f"soliq_yagona_{stir}"))
    if 'qqs' in soliq_turlari:
        keyboard.add(InlineKeyboardButton(translate_text("Qo‘shilgan qiymat solig‘i", lang), callback_data=f"soliq_qqs_{stir}"))

    # Agar tugmalar qo‘shilmagan bo‘lsa, standart tugmalar
    if not keyboard.inline_keyboard:
        logger.warning(f"No buttons added for soliq_turi: {soliq_turi}, adding default buttons")
        keyboard.add(
            InlineKeyboardButton(translate_text("Daromad solig'i", lang), callback_data=f"soliq_daromad_{stir}"),
            InlineKeyboardButton(translate_text("Yagona soliq", lang), callback_data=f"soliq_yagona_{stir}")
        )

    

    # Firma ma'lumotlarini ko'rsatish
    firma_nomi = translate_text(name, lang)
    rahbar = translate_text(rahbar, lang) if rahbar else translate_text("Noma'lum", lang)
    soliq_turi_text = translate_text(soliq_turi, lang) if soliq_turi else translate_text("Noma'lum", lang)
    ds_stavka = ds_stavka if ds_stavka else "Noma'lum"
    ys_stavka = ys_stavka if ys_stavka else "Noma'lum"
    qqs_stavka = qqs_stavka if qqs_stavka else "Noma'lum"

    response = get_text(lang, 'firma_info',
                       stir=stir,
                       firma_nomi=firma_nomi,
                       rahbar=rahbar,
                       soliq_turi=soliq_turi_text,
                       ds_stavka=ds_stavka,
                       ys_stavka=ys_stavka,
                       qqs_stavka=qqs_stavka)
    
    # Xabarni ikkiga bo‘lib yuborish
    await message.answer(response, parse_mode='Markdown')
    await message.answer(get_text(lang, 'select_tax_type', stir=stir), reply_markup=keyboard, parse_mode='Markdown')
    logger.info(f"Keyboard sent: {keyboard.inline_keyboard}")


async def send_report_files_only(stir, soliq_turi, oy, user_id, lang):
    logger.info(f"send_report_files_only: user_id={user_id}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}, lang={lang}")
    file_types = ['excel1', 'excel2', 'html']
    files_found = False
    preferred_lang = 'latin' if lang == 'uz_latin' else 'cyrillic'
    fallback_lang = 'cyrillic' if lang == 'uz_latin' else 'latin'

    for file_type in file_types:
        db_file_type = f"{file_type}_{preferred_lang}" if file_type != 'html' else 'html'
        file_path = check_file(stir, soliq_turi, oy.lower(), db_file_type)
        logger.info(f"Fayl qidirilmoqda: file_type={db_file_type}, file_path={file_path}")

        if file_path:
            normalized_path = os.path.normpath(file_path)
            logger.info(f"Normallashtirilgan yo'l: {normalized_path}")
            if os.path.exists(normalized_path):
                try:
                    with open(normalized_path, 'rb') as f:
                        await bot.send_document(
                            user_id,
                            f,
                            caption=translate_text(f"{os.path.basename(normalized_path)} fayli", lang),
                            parse_mode='HTML'
                        )
                    logger.info(f"Fayl yuborildi: {normalized_path}, user_id={user_id}")
                    files_found = True
                except Exception as e:
                    logger.error(f"Fayl yuborishda xato: file_path={normalized_path}, user_id={user_id}, xato={str(e)}")
                    await bot.send_message(
                        user_id,
                        translate_text(f"❌ Fayl yuborishda xato: {os.path.basename(normalized_path)} - {str(e)}", lang),
                        parse_mode='HTML'
                    )
            else:
                logger.warning(f"Fayl diskda mavjud emas: {normalized_path}, file_type={db_file_type}")
                await bot.send_message(
                    user_id,
                    translate_text(f"❌ Fayl diskda topilmadi: {os.path.basename(normalized_path)}", lang),
                    parse_mode='HTML'
                )
        else:
            # Fallback faylni sinab ko'rish
            if file_type != 'html':
                db_file_type = f"{file_type}_{fallback_lang}"
                file_path = check_file(stir, soliq_turi, oy.lower(), db_file_type)
                logger.info(f"Fallback fayl qidirilmoqda: file_type={db_file_type}, file_path={file_path}")
                if file_path:
                    normalized_path = os.path.normpath(file_path)
                    if os.path.exists(normalized_path):
                        try:
                            with open(normalized_path, 'rb') as f:
                                await bot.send_document(
                                    user_id,
                                    f,
                                    caption=translate_text(f"{os.path.basename(normalized_path)} fayli", lang),
                                    parse_mode='HTML'
                                )
                            logger.info(f"Fallback fayl yuborildi: {normalized_path}, user_id={user_id}")
                            files_found = True
                        except Exception as e:
                            logger.error(f"Fallback fayl yuborishda xato: file_path={normalized_path}, user_id={user_id}, xato={str(e)}")
                            await bot.send_message(
                                user_id,
                                translate_text(f"❌ Fallback fayl yuborishda xato: {os.path.basename(normalized_path)} - {str(e)}", lang),
                                parse_mode='HTML'
                            )
                    else:
                        logger.warning(f"Fallback fayl diskda mavjud emas: {normalized_path}, file_type={db_file_type}")
                        await bot.send_message(
                            user_id,
                            translate_text(f"❌ Fallback fayl diskda topilmadi: {os.path.basename(normalized_path)}", lang),
                            parse_mode='HTML'
                        )
                else:
                    logger.warning(f"Fallback fayl bazada topilmadi: file_type={db_file_type}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
                    await bot.send_message(
                        user_id,
                        translate_text(f"❌ {db_file_type} fayli ma'lumotlar bazasida topilmadi.", lang),
                        parse_mode='HTML'
                    )

    if not files_found:
        await bot.send_message(
            user_id,
            translate_text(f"❌ {get_month_name(lang, oy)} uchun {soliq_turi} fayli topilmadi.", lang),
            parse_mode='HTML'
        )
        logger.error(f"Hech qanday fayl topilmadi: stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
    else:
        logger.info(f"Fayllar yuborildi: stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
    return files_found

async def send_report_files(stir, soliq_turi, oy, user_id, lang):
    logger.info(f"send_report_files: user_id={user_id}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}, lang={lang}")
    file_types = ['excel1', 'excel2', 'html']
    files_found = False
    preferred_lang = 'latin' if lang == 'uz_latin' else 'cyrillic'
    fallback_lang = 'cyrillic' if lang == 'uz_latin' else 'latin'

    for file_type in file_types:
        db_file_type = f"{file_type}_{preferred_lang}" if file_type != 'html' else 'html'
        file_path = check_file(stir, soliq_turi, oy.lower(), db_file_type)
        logger.info(f"Fayl qidirilmoqda: file_type={db_file_type}, file_path={file_path}")

        if file_path:
            normalized_path = os.path.normpath(file_path)
            logger.info(f"Normallashtirilgan yo'l: {normalized_path}")
            if os.path.exists(normalized_path):
                try:
                    with open(normalized_path, 'rb') as f:
                        await bot.send_document(
                            user_id,
                            f,
                            caption=translate_text(f"{os.path.basename(normalized_path)} fayli", lang),
                            parse_mode='HTML'
                        )
                    logger.info(f"Fayl yuborildi: {normalized_path}, user_id={user_id}")
                    files_found = True
                except Exception as e:
                    logger.error(f"Fayl yuborishda xato: file_path={normalized_path}, user_id={user_id}, xato={str(e)}")
                    await bot.send_message(
                        user_id,
                        translate_text(f"❌ Fayl yuborishda xato: {os.path.basename(normalized_path)} - {str(e)}", lang),
                        parse_mode='HTML'
                    )
            else:
                logger.warning(f"Fayl diskda mavjud emas: {normalized_path}, file_type={db_file_type}")
                await bot.send_message(
                    user_id,
                    translate_text(f"❌ Fayl diskda topilmadi: {os.path.basename(normalized_path)}", lang),
                    parse_mode='HTML'
                )
        else:
            # Fallback faylni sinab ko'rish
            if file_type != 'html':
                db_file_type = f"{file_type}_{fallback_lang}"
                file_path = check_file(stir, soliq_turi, oy.lower(), db_file_type)
                logger.info(f"Fallback fayl qidirilmoqda: file_type={db_file_type}, file_path={file_path}")
                if file_path:
                    normalized_path = os.path.normpath(file_path)
                    if os.path.exists(normalized_path):
                        try:
                            with open(normalized_path, 'rb') as f:
                                await bot.send_document(
                                    user_id,
                                    f,
                                    caption=translate_text(f"{os.path.basename(normalized_path)} fayli", lang),
                                    parse_mode='HTML'
                                )
                            logger.info(f"Fallback fayl yuborildi: {normalized_path}, user_id={user_id}")
                            files_found = True
                        except Exception as e:
                            logger.error(f"Fallback fayl yuborishda xato: file_path={normalized_path}, user_id={user_id}, xato={str(e)}")
                            await bot.send_message(
                                user_id,
                                translate_text(f"❌ Fallback fayl yuborishda xato: {os.path.basename(normalized_path)} - {str(e)}", lang),
                                parse_mode='HTML'
                            )
                    else:
                        logger.warning(f"Fallback fayl diskda mavjud emas: {normalized_path}, file_type={db_file_type}")
                        await bot.send_message(
                            user_id,
                            translate_text(f"❌ Fallback fayl diskda topilmadi: {os.path.basename(normalized_path)}", lang),
                            parse_mode='HTML'
                        )
                else:
                    logger.warning(f"Fallback fayl bazada topilmadi: file_type={db_file_type}, stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
                    await bot.send_message(
                        user_id,
                        translate_text(f"❌ {db_file_type} fayli ma'lumotlar bazasida topilmadi.", lang),
                        parse_mode='HTML'
                    )

    # Matn ko‘rinishidagi hisobotni yuborish
    if soliq_turi == "daromad":
        report = get_manual_report(stir, oy)
        if report:
            _, _, _, firma_name, xodimlar_soni, xodimlar_data, hisobot_davri_oylik, jami_oylik, soliq = report
            xodimlar_lines = xodimlar_data.split("\n")
            formatted_xodimlar_data = []
            for line in xodimlar_lines:
                match = re.match(r'^(\d+) \((.*?)\) – (.*?), (.*?): ([\d,]+) (.*?)\s*\((.*?): ([\d,]+) (.*?)\)$', line)
                if match:
                    index, lavozim, ism, _, shu_oy, _, _, yil_boshidan, _ = match.groups()
                    formatted_line = f"{index} ({lavozim}) – {ism}, {translate_text('bu_oy_uchun_hisobotda', lang)}: {shu_oy} {translate_text('so‘m', lang)} ({translate_text('yil_boshidan_hisobotda', lang)}: {yil_boshidan} {translate_text('so‘m', lang)})"
                    formatted_xodimlar_data.append(formatted_line)
                else:
                    formatted_xodimlar_data.append(line)
            xodimlar_data_translated = "\n".join(formatted_xodimlar_data)
            firma_name_translated = translate_text(firma_name, lang)
            result = get_text(lang, 'daromad_report',
                              firma_name=firma_name_translated,
                              oy=get_month_name(lang, oy),
                              xodimlar_soni=xodimlar_soni,
                              xodimlar_data=xodimlar_data_translated,
                              jami_oylik=jami_oylik,
                              hisobot_davri_oylik=hisobot_davri_oylik,
                              soliq=soliq)
            await bot.send_message(user_id, result, parse_mode='Markdown')
        else:
            await bot.send_message(user_id, get_text(lang, 'no_manual_report', oy=get_month_name(lang, oy)))
    elif soliq_turi == "yagona":
        summary = generate_yagona_summary(stir, oy, lang)
        await bot.send_message(user_id, summary, parse_mode='Markdown')
    elif soliq_turi == "qqs":
        summary = generate_qqs_summary(stir, oy, lang)
        await bot.send_message(user_id, summary, parse_mode='Markdown')

    if not files_found:
        await bot.send_message(
            user_id,
            translate_text(f"❌ {get_month_name(lang, oy)} uchun {soliq_turi} fayli topilmadi.", lang),
            parse_mode='HTML'
        )
        logger.error(f"Hech qanday fayl topilmadi: stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
    else:
        logger.info(f"Fayllar yuborildi: stir={stir}, soliq_turi={soliq_turi}, oy={oy}")
    return files_found


        
@dp.callback_query_handler(lambda c: c.data.startswith("soliq_"))
async def select_month_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_user_language(user_id)
    _, soliq_turi, stir = callback_query.data.split("_")

    # Inline keyboard yaratish
    keyboard = InlineKeyboardMarkup(row_width=3)
    oylar = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul"]
    for oy in oylar:
        keyboard.insert(InlineKeyboardButton(get_month_name(lang, oy), callback_data=f"hisobot_{soliq_turi}_{stir}_{oy}"))

    # ❗️Avvalgi tugmalarni olib tashlash
    await callback_query.message.edit_reply_markup(reply_markup=None)

    # Yangisini yuborish
    soliq_turi_text = translate_text(
        "Daromad solig'i" if soliq_turi == "daromad" else
        "Yagona soliq" if soliq_turi == "yagona" else
        "Qo‘shilgan qiymat solig‘i", lang
    )
    await bot.send_message(
        callback_query.from_user.id,
        get_text(lang, 'select_month', soliq_turi=soliq_turi_text),
        reply_markup=keyboard
    )



@dp.callback_query_handler(lambda c: c.data.startswith("hisobot_"))
async def process_report_files(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    lang = get_user_language(user_id)
    logger.info(f"process_report_files: user_id={user_id}, lang={lang}")
    _, soliq_turi, stir, oy = callback_query.data.split("_")

    # ❗️Avvalgi tugmalarni olib tashlash
    await callback_query.message.edit_reply_markup(reply_markup=None)

    # Barcha fayllarni yuborish uchun send_report_files funksiyasini chaqirish
    await send_report_files_only(stir, soliq_turi, oy, user_id, lang)

    # Soliq turiga qarab qo‘shimcha ma'lumotlar
    if soliq_turi == "daromad":
        report = get_manual_report(stir, oy)
        if report:
            _, _, _, firma_name, xodimlar_soni, xodimlar_data, hisobot_davri_oylik, jami_oylik, soliq = report
            # Xodimlar ma'lumotlarini qayta formatlash
            xodimlar_lines = xodimlar_data.split("\n")
            formatted_xodimlar_data = []
            for line in xodimlar_lines:
                match = re.match(r'^(\d+) \((.*?)\) – (.*?), (.*?): ([\d,]+) (.*?)\s*\((.*?): ([\d,]+) (.*?)\)$', line)
                if match:
                    index, lavozim, ism, _, shu_oy, _, _, yil_boshidan, _ = match.groups()
                    formatted_line = f"{index} ({lavozim}) – {ism}, {translate_text('bu_oy_uchun_hisobotda', lang)}: {shu_oy} {translate_text('so‘m', lang)} ({translate_text('yil_boshidan_hisobotda', lang)}: {yil_boshidan} {translate_text('so‘m', lang)})"
                    formatted_xodimlar_data.append(formatted_line)
                else:
                    formatted_xodimlar_data.append(line)
            xodimlar_data_translated = "\n".join(formatted_xodimlar_data)
            firma_name_translated = translate_text(firma_name, lang)
            result = get_text(lang, 'daromad_report',
                              firma_name=firma_name_translated,
                              oy=get_month_name(lang, oy),
                              xodimlar_soni=xodimlar_soni,
                              xodimlar_data=xodimlar_data_translated,
                              jami_oylik=jami_oylik,
                              hisobot_davri_oylik=hisobot_davri_oylik,
                              soliq=soliq)
            await bot.send_message(callback_query.from_user.id, result)
        else:
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(translate_text("Admin panelda qo'lda kiritish", lang), callback_data="manual_input"))
            await bot.send_message(
                callback_query.from_user.id,
                get_text(lang, 'no_manual_report', oy=get_month_name(lang, oy)),
                reply_markup=keyboard
            )
    elif soliq_turi == "yagona":
        firma_name = get_firma_name(stir)
        summary = generate_yagona_summary(stir, oy, lang)
        await bot.send_message(callback_query.from_user.id, summary)
    elif soliq_turi == "qqs":
        firma_name = get_firma_name(stir)
        summary = generate_qqs_summary(stir, oy, lang)
        await bot.send_message(callback_query.from_user.id, summary)

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(translate_text("Soliq turini qayta tanlash", lang), callback_data=f"soliq_{soliq_turi}_{stir}"),
        InlineKeyboardButton(translate_text("Boshqa firma tanlash", lang), callback_data="start")
    )
    await bot.send_message(callback_query.from_user.id, get_text(lang, 'back_options'), reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "start")
async def restart_handler(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    lang = get_user_language(user_id)
    logger.info(f"restart_handler: user_id={user_id}, lang={lang}")
    await bot.send_message(callback_query.from_user.id, get_text(lang, 'welcome'))

@dp.message_handler(commands=['search_firma'])
async def search_firma_command(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    logger.info(f"search_firma_command: user_id={user_id}, lang={lang}")
    await message.answer(translate_text("Firma STIR raqamini kiriting (9 raqam, masalan: 123456789):", lang))
    await SearchFirma.waiting_for_stir.set()

@dp.message_handler(state=SearchFirma.waiting_for_stir)
async def process_firma_search(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    stir = message.text.strip()
    logger.info(f"STIR kiritildi: '{stir}', uzunligi: {len(stir)}, faqat raqamlar: {stir.isdigit()}")

    if not stir.isdigit() or len(stir) != 9:
        await message.answer(translate_text("❌ STIR 9 raqamdan iborat bo'lishi kerak.", lang))
        logger.error(f"Noto'g'ri STIR formati: '{stir}'")
        await state.finish()
        return

    firma_info = get_firma_info(stir)
    if not firma_info:
        await message.answer(translate_text("❌ Bu STIR bo'yicha firma topilmadi.", lang))
        logger.warning(f"Firma topilmadi: STIR={stir}")
        await state.finish()
        return

    name, rahbar, soliq_turi, ds_stavka, ys_stavka, qqs_stavka = firma_info
    logger.info(f"Firma topildi: STIR={stir}, Name={name}, Rahbar={rahbar}, Soliq turi={soliq_turi}")
    firma_nomi = translate_text(name, lang)
    rahbar = translate_text(rahbar, lang) if rahbar else "Noma'lum"
    soliq_turi = translate_text(soliq_turi, lang) if soliq_turi else "Noma'lum"
    ds_stavka = ds_stavka if ds_stavka else "Noma'lum"
    ys_stavka = ys_stavka if ys_stavka else "Noma'lum"
    qqs_stavka = qqs_stavka if qqs_stavka else "Noma'lum"

    response = get_text(lang, 'firma_info',
                       stir=stir,
                       firma_nomi=firma_nomi,
                       rahbar=rahbar,
                       soliq_turi=soliq_turi,
                       ds_stavka=ds_stavka,
                       ys_stavka=ys_stavka,
                       qqs_stavka=qqs_stavka)
    await message.answer(response)
    await state.finish()
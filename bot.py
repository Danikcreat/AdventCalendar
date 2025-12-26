import os
import asyncio
from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ----------------------------
# 1) ENV / BOT INIT
# ----------------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")

TZ_NAME = os.getenv("TZ", "Europe/Minsk")
TZ = ZoneInfo(TZ_NAME)

UNLOCK_HOUR = int(os.getenv("UNLOCK_HOUR", "10"))
UNLOCK_MINUTE = int(os.getenv("UNLOCK_MINUTE", "0"))
DAY4_BEAGLE_DELAY = float(os.getenv("DAY4_BEAGLE_DELAY", "8"))

DB_PATH = "advent.sqlite"

# Можно задать file_id для прогресс-фото, чтобы Telegram брал картинку из кеша
PROGRESS_PHOTO_ID = os.getenv("PROGRESS_PHOTO_ID", "").strip()

DAY3_M1_PHOTO_ID = os.getenv("DAY3_M1_PHOTO_ID", "").strip()
DAY3_M4_PHOTO_ID = os.getenv("DAY3_M4_PHOTO_ID", "").strip()

DAY3_M1_PHOTO_META = {"file_id": DAY3_M1_PHOTO_ID} if DAY3_M1_PHOTO_ID else {"file": "media/img4.png"}
DAY3_M4_PHOTO_META = {"file_id": DAY3_M4_PHOTO_ID} if DAY3_M4_PHOTO_ID else {"file": "media/img5.png"}

DAY4_M2_PHOTO_ID = os.getenv("DAY4_M2_PHOTO_ID", "").strip()
DAY4_M4_PHOTO_ID = os.getenv("DAY4_M4_PHOTO_ID", "").strip()

DAY4_M2_PHOTO_META = {"file_id": DAY4_M2_PHOTO_ID} if DAY4_M2_PHOTO_ID else {"file": "media/img4.png"}
DAY4_M4_PHOTO_META = {"file_id": DAY4_M4_PHOTO_ID} if DAY4_M4_PHOTO_ID else {"file": "media/img5.png"}

# ВАЖНО: parse_mode="HTML" задан по умолчанию для всего бота
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # parse_mode="HTML"
)
dp = Dispatcher()

# ----------------------------
# 2) CONTENT (7 DAYS)
#    Заполни дни 2-7 по аналогии.
# ----------------------------
CONTENT: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "День 1 — «Потерянная варежка»",
        "spark_name": "Искра №1",
        "code_part": "В",
        "steps": [
            {
                "type": "text",
                "text": (
                    "Привет 🐾\n\n"
                    "Сегодня начинается одна маленькая новогодняя история на <b>7 дней</b>.\n\n"
                    "И у неё есть герой… который сейчас в лёгкой панике."
                ),
                "next": True,
            },
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAP7aUqVCWH61Kd1ai1q5VvvCVGojF0AAvkLaxu_5FhK2oCzWwABnR14AQADAgADeQADNgQ",
                "caption":
                  (
                    "Вайбик (да, бигль) шёл по снегу…\n\n"
                    "и нашёл <b>потерянную варежку</b> 🧤\n\n"
                    "Она была тёплая, будто её только что уронили.\n\n"
                    "И на ней была бирка:\n"
                    "<b>«Вернуть хозяйке. Внутри — Искра №1»</b> ✨"
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "Вайбик заглянул внутрь…\n\n"
                    "а там маленькая записка:\n\n"
                    "<b>«Если ты читаешь это — значит, ты теперь в игре.»</b>\n\n"
                    "<b>7 дней</b>.\n"
                    "Каждый день — новая глава и маленький сюрприз.\n\n"
                    "Вайбик сказал, что без тебя он не дойдёт до финала 🤍"
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "Но сначала Вайбик должен понять, как тебя вести по этой истории.\n\n"
                    "Какой режим включаем? 👇"
                ),
                "buttons": [
                    {"text": "❄️ Нежно и тепло", "action": "set_mode", "value": "soft"},
                    {"text": "🎄 Смешно и легко", "action": "set_mode", "value": "fun"},
                    {"text": "✨ Микс", "action": "set_mode", "value": "mix"},
                ],
            },
            # ответ бота на выбор режима (отправим автоматически)
            {
                "type": "text",
                "text": "Принято. Варежку закрепляю на хвост, курс — на Новый год 🐶🧤✨",
                "next": False,
            },
            # финал дня: картинка + кнопка забрать искру
            {
                "type": "photo",
                "file": "media/img3.png",
                "caption": (
                    "Тогда торжественно:\n\n"
                    "<b>Искра №1 найдена</b> ✨\n\n"
                    "Сегодняшний подарок — маленький, но очень важный:\n"
                    "<b>открытка от Вайбика</b> (и чуть-чуть от меня) 🤍\n\n"
                    "Завтра варежка покажет следующую подсказку."
                ),
                "buttons": [
                    {"text": "✨ Забрать Искру", "action": "get_spark"},
                ],
                # опционально: после открытки автоматически отправить голосовое
                "after": [
                    {"type": "voice", "file": "media/day1/voice.ogg"},
                ],
            },
        ],
    },

    2: {
        "title": "День 2 — «Лавка сияния»",
        "spark_name": "Искра №2",
        "code_part": "А",
        "steps": [
            {
                "type": "text",
                "text": (
                    "Доброе утро ✨\n"
                    "Вайбик сегодня проснулся раньше обычного.\n"
                    "Варежка из вчерашнего дня всё ещё была тёплой…\n"
                    "и привела его к одному странному месту."
                ),
                "next": True,
            },
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAOXaUglTZimhXKMTBPxQ3wFMoXaTjkAAgMPaxt2VUFKWeaxTfdixPcBAAMCAAN5AAM2BA",
                "caption": (
                    "На узкой заснеженной улочке\n"
                    "Вайбик увидел вывеску:\n\n"
                    "«Лавка сияния» ✨\n\n"
                    "Говорят, сюда приходят,\n"
                    "когда хочется снова почувствовать себя красивой,\n"
                    "живой\n"
                    "и немного счастливее."
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "Вайбик говорит, что лавка работает\n"
                    "только если выбрать, какое сияние нужно сегодня.\n\n"
                    "Что выбираем? 👇"
                ),
                "buttons": [
                    {"text": "✨ Внутренний свет", "action": "glow", "value": "inner"},
                    {"text": "💄 Внешний блеск", "action": "glow", "value": "outer"},
                    {"text": "🌸 И то и другое", "action": "glow", "value": "both"},
                ],
            },
            {
                "type": "text",
                "text": (
                    "Отличный выбор.\n"
                    "Хозяин лавки улыбнулся и протянул Вайбику маленький флакон ✨\n\n"
                    "Внутри была вторая Искра."
                ),
                "no_menu": True
            },
            {
                "type": "photo",
                "file": "media/img6.png",
                "caption": (
                    "Искра №2 найдена ✨\n\n"
                    "Хозяин лавки сказал:\n"
                    "«Сияние — это когда ты позволяешь себе заботу».\n\n"
                    "Поэтому сегодня — подарок для тебя 💛\n"
                    "сертификат в Золотое Яблоко\n"
                    "на то, что захочется именно тебе."
                ),
                "buttons": [
                    {"text": "✨ Забрать Искру", "action": "get_spark"},
                ],
            },
        ],
    },
    3: {
        "title": "День 3 — «След памяти»",
        "spark_name": "Искра №3",
        "code_part": "Б",
        "steps": [
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAIBamlMd0nq52EQ5nvz07Gi-5c2GwRHAAJyE2sb_gdhSu0nBBbcnKjLAQADAgADeQADNgQ",
                "caption": (
                    "Привет 🌸\n"
                    "Сегодня Вайбик идёт медленно.\n"
                    "Он заметил, что на снегу\n"
                    "остаются следы — и каждый из них что-то хранит."
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "Вайбик понял одну вещь:\n"
                    "не всё, что важно, видно глазами.\n\n"
                    "Иногда после тебя остаётся\n"
                    "след памяти —\n"
                    "ощущение,\n"
                    "запах,\n"
                    "чувство.\n\n"
                    "И сегодня он учится оставлять именно такой след."
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "Вайбик говорит, что у каждого дня\n"
                    "есть свой аромат.\n\n"
                    "Какой сегодня ближе тебе? 👇"
                ),
                "buttons": [
                    {"text": "🌸 Цветочный и нежный", "action": "aroma", "value": "floral"},
                    {"text": "🌿 Свежий и спокойный", "action": "aroma", "value": "fresh"},
                    {"text": "🍊 Тёплый и уютный", "action": "aroma", "value": "warm"},
                    {"text": "✨ Загадочный и вечерний", "action": "aroma", "value": "mystery"},
                ],
            },
            {
                "type": "text",
                "text": (
                    "Вайбик остановился, вдохнул глубже…\n"
                    "и в этом аромате появилась\n"
                    "третья Искра ✨"
                ),
                "no_menu": True
            },
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAIBbGlMeQS9YPjRH9w-_GEGbf1_oTnoAAJzE2sb_gdhSljP74T9LdyaAQADAgADeQADNgQ",
                "caption": (
                    "✨ Искра №3 найдена\n\n"
                    "Вайбик говорит:\n"
                    "«Ароматы — это воспоминания, которые можно носить с собой».\n\n"
                    "Поэтому сегодня — подарок для тебя 🌸\n"
                    "сертификат на духи ETIB\n"
                    "чтобы ты выбрала аромат,\n"
                    "который захочешь оставить после себя."
                ),
                "buttons": [
                    {"text": "✨ Забрать Искру", "action": "get_spark"},
                ],
            },
        ],
    },
    4: {
        "title": "День 4 — «Чайная станция»",
        "spark_name": "Искра №4",
        "code_part": "Й",
        "steps": [
            {
                "type": "text",
                "text": (
                    "Доброе утро ☕\n"
                    "Сегодня Вайбик никуда не спешит.\n"
                    "Снег идёт медленно,\n"
                    "и путь вдруг стал тише."
                ),
                "next": True,
            },
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAIBsmlOMgfCO2eML5Xj89fRSQ3kqUXHAAI6EGsbxlZxSiq-3jo-2xyrAQADAgADeQADNgQ",
                "caption": (
                    "По дороге Вайбик нашёл маленькую станцию.\n"
                    "Там было тепло. Пахло чаем.\n"
                    "И свет горел так, будто ждал именно его.\n\n"
                    "Он понял:\n"
                    "иногда, чтобы идти дальше,\n"
                    "нужно просто остановиться и согреться."
                ),
                "next": True,
            },
            {
                "type": "text",
                "text": (
                    "На станции Вайбик заметил странное правило 🐾\n\n"
                    "Чтобы получить следующую Искру, нужно показать фото бигля.\n\n"
                    "Найди и пришли любую фотографию бигля:\n"
                    "– настоящего\n"
                    "– с интернета\n"
                    "– мем\n\n"
                    "Всё подойдёт 🤍"
                ),
                "no_menu": True
            },
            {
                "type": "text",
                "text": (
                    "Вайбик внимательно посмотрел…\n"
                    "повилял хвостом и сказал:\n\n"
                    "«Одобрено. Очень уютный бигль» 🐶✨\n\n"
                    "В этот момент станция зажглась мягким светом — и появилась четвёртая Искра."
                ),
                "no_menu": True
            },
            {
                "type": "photo",
                "file_id": "AgACAgIAAxkBAAIBt2lOOFB7VSWQ1XVU3W-Ob1vytQfyAAJrEGsbxlZxSmx9j8Gt71oJAQADAgADeQADNgQ",
                "caption": (
                    "✨ Искра №4 найдена\n\n"
                    "На чайной станции Вайбик оставил для тебя\n"
                    "набор уюта 🤍\n\n"
                    "☕ новогодний чай\n"
                    "🕯️ свечи с тёплым ароматом\n\n"
                    "Чтобы в один из вечеров\n"
                    "ты тоже могла просто остановиться\n"
                    "и почувствовать тепло."
                ),
                "buttons": [
                    {"text": "✨ Забрать Искру", "action": "get_spark"},
                ],
            },
        ],
    },
    5: {"title": "День 5 — (заполни)", "spark_name": "Искра №5", "code_part": "E5", "steps": [
        {"type":"text","text":"День 5 пока не заполнен 🙂","buttons":[{"text":"⬅️ В меню","action":"menu"}]}
    ]},
    6: {"title": "День 6 — (заполни)", "spark_name": "Искра №6", "code_part": "F6", "steps": [
        {"type":"text","text":"День 6 пока не заполнен 🙂","buttons":[{"text":"⬅️ В меню","action":"menu"}]}
    ]},
    7: {"title": "День 7 — (заполни)", "spark_name": "Искра №7", "code_part": "G7", "steps": [
        {"type":"text","text":"День 7 пока не заполнен 🙂","buttons":[{"text":"⬅️ В меню","action":"menu"}]}
    ]},
}

# ----------------------------
# 3) DB
# ----------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  opened_day INTEGER NOT NULL DEFAULT 1,
  active_day INTEGER NOT NULL DEFAULT 1,
  active_step INTEGER NOT NULL DEFAULT 0,
  mode TEXT NOT NULL DEFAULT 'mix',
  sparks TEXT NOT NULL DEFAULT '',
  codes TEXT NOT NULL DEFAULT '',
  next_unlock_at TEXT NOT NULL
);
"""

def _now() -> datetime:
    return datetime.now(tz=TZ)

def _next_unlock_time() -> datetime:
    """
    Следующий момент открытия нового дня:
    завтра в UNLOCK_HOUR:UNLOCK_MINUTE по TZ
    """
    now = _now()
    tomorrow = (now + timedelta(days=1)).date()
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, UNLOCK_HOUR, UNLOCK_MINUTE, tzinfo=TZ)

def _split_pipe(s: str) -> List[str]:
    s = (s or "").strip()
    return [x for x in s.split("|") if x] if s else []

def _add_unique_pipe(s: str, value: str) -> str:
    items = _split_pipe(s)
    if value not in items:
        items.append(value)
    return "|".join(items)

def _resolve_media_source(item: Dict[str, Any]):
    """
    Возвращает либо file_id, либо FSInputFile по локальному пути.
    Позволяет использовать заранее загруженные медиа.
    """
    file_id = item.get("file_id")
    if file_id:
        return file_id

    file_path = item.get("file")
    if file_path:
        return FSInputFile(file_path)

    raise ValueError("Не указан источник медиа (file или file_id)")

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SCHEMA)
        await db.commit()

async def db_upsert_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id, next_unlock_at) VALUES(?, ?)",
            (user_id, _next_unlock_time().isoformat()),
        )
        await db.commit()

async def db_get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, opened_day, active_day, active_step, mode, sparks, codes, next_unlock_at "
            "FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "user_id": row[0],
            "opened_day": row[1],
            "active_day": row[2],
            "active_step": row[3],
            "mode": row[4],
            "sparks": row[5],
            "codes": row[6],
            "next_unlock_at": row[7],
        }

async def db_set_progress(user_id: int, active_day: int, active_step: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET active_day=?, active_step=? WHERE user_id=?",
            (active_day, active_step, user_id),
        )
        await db.commit()

async def db_set_mode(user_id: int, mode: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET mode=? WHERE user_id=?",
            (mode, user_id),
        )
        await db.commit()

async def db_add_spark_code(user_id: int, spark: str, code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT sparks, codes FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        sparks = _add_unique_pipe(row[0], spark)
        codes = _add_unique_pipe(row[1], code)
        await db.execute(
            "UPDATE users SET sparks=?, codes=? WHERE user_id=?",
            (sparks, codes, user_id),
        )
        await db.commit()

async def db_unlock_next_day_for_due_users():
    """
    Проверяем каждые 5 минут:
    если next_unlock_at <= now и opened_day < 7 -> opened_day++ и next_unlock_at += 1 день
    """
    now = _now()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, opened_day, next_unlock_at FROM users"
        )
        users = await cur.fetchall()

    for user_id, opened_day, next_unlock_at in users:
        try:
            due = datetime.fromisoformat(next_unlock_at)
        except Exception:
            due = _next_unlock_time()

        if opened_day >= 7:
            continue

        if due <= now:
            new_day = opened_day + 1
            # следующий unlock — через сутки (в то же время)
            new_due = due + timedelta(days=1)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET opened_day=?, next_unlock_at=? WHERE user_id=?",
                    (new_day, new_due.isoformat(), user_id),
                )
                await db.commit()

            # уведомление
            try:
                await bot.send_message(
                    user_id,
                    f"🐶✨ Доступен новый день адвента: <b>День {new_day}</b>!\n"
                    f"Жми «Открыть доступный день» 🙂",
                    reply_markup=menu_kb()
                )
            except Exception:
                # пользователь мог заблокировать бота — игнорим
                pass

# ----------------------------
# 4) UI (KEYBOARDS)
# ----------------------------
def menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Открыть доступный день", callback_data="open_day")
    kb.button(text="✨ Прогресс", callback_data="progress")
    kb.adjust(1)
    return kb.as_markup()

def build_step_kb(day: int, step_idx: int, step: Dict[str, Any], total_steps: int):
    kb = InlineKeyboardBuilder()

    buttons = step.get("buttons")
    if buttons:
        for b in buttons:
            text = b["text"]
            action = b.get("action", "")
            if action == "url":
                kb.button(text=text, url=b["url"])
            elif action == "set_mode":
                kb.button(text=text, callback_data=f"mode:{day}:{step_idx}:{b['value']}")
            elif action == "glow":
                kb.button(text=text, callback_data=f"glow:{day}:{step_idx}:{b['value']}")
            elif action == "aroma":
                kb.button(text=text, callback_data=f"aroma:{day}:{step_idx}:{b['value']}")
            elif action == "get_spark":
                kb.button(text=text, callback_data=f"spark:{day}")
            elif action == "menu":
                kb.button(text=text, callback_data="menu")
            elif action == "next":
                kb.button(text=text, callback_data=f"next:{day}:{step_idx}")
            else:
                # на будущее — свои экшены
                kb.button(text=text, callback_data=f"noop")
        kb.adjust(1)
        return kb.as_markup()

    # Если нет кастомных кнопок — делаем "Дальше" автоматически
    if step.get("next", False) and step_idx < total_steps - 1:
        kb.button(text="➡️ Дальше", callback_data=f"next:{day}:{step_idx}")
        kb.adjust(1)
        return kb.as_markup()

    # Можно отключить кнопку меню явным флагом в шаге
    if step.get("no_menu"):
        return None

    # Если последний шаг без кнопок — хотя бы меню
    kb.button(text="⬅️ В меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()

# ----------------------------
# 5) SENDER (step engine)
# ----------------------------
async def send_step(chat_id: int, day: int, step_idx: int):
    day_data = CONTENT.get(day)
    if not day_data:
        await bot.send_message(chat_id, "Такого дня нет 😅", reply_markup=menu_kb())
        return

    steps = day_data["steps"]
    if step_idx < 0 or step_idx >= len(steps):
        await bot.send_message(chat_id, "Этот день уже закончился 🙂", reply_markup=menu_kb())
        return

    step = steps[step_idx]
    total = len(steps)
    reply_markup = build_step_kb(day, step_idx, step, total)

    t = step["type"]

    try:
        if t == "text":
            await bot.send_message(chat_id, step["text"], reply_markup=reply_markup)

        elif t == "photo":
            caption = step.get("caption", "")
            await bot.send_photo(
                chat_id,
                _resolve_media_source(step),
                caption=caption,
                reply_markup=reply_markup
            )

        elif t == "voice":
            await bot.send_voice(chat_id, _resolve_media_source(step), reply_markup=reply_markup)

        elif t == "video":
            caption = step.get("caption", None)
            await bot.send_video(
                chat_id,
                _resolve_media_source(step),
                caption=caption,
                reply_markup=reply_markup
            )

        elif t == "video_note":
            await bot.send_video_note(chat_id, _resolve_media_source(step), reply_markup=reply_markup)

        elif t == "sticker":
            # sticker отправляется по file_id
            await bot.send_sticker(chat_id, step["file_id"], reply_markup=reply_markup)

        else:
            await bot.send_message(chat_id, f"Неизвестный тип шага: {t}", reply_markup=menu_kb())

        # Автосообщения после шага (например голосовое после открытки)
        after = step.get("after") or []
        for a in after:
            at = a["type"]
            if at == "voice":
                await bot.send_voice(chat_id, _resolve_media_source(a))
            elif at == "photo":
                await bot.send_photo(chat_id, _resolve_media_source(a), caption=a.get("caption", ""))
            elif at == "video":
                await bot.send_video(chat_id, _resolve_media_source(a), caption=a.get("caption"))
            elif at == "video_note":
                await bot.send_video_note(chat_id, _resolve_media_source(a))
            elif at == "sticker":
                await bot.send_sticker(chat_id, a["file_id"])
            elif at == "text":
                await bot.send_message(chat_id, a["text"])

    except (FileNotFoundError, ValueError) as err:
        await bot.send_message(
            chat_id,
            f"⚠️ Не вышло отправить медиа: {err}",
            reply_markup=menu_kb()
        )

# ----------------------------
# 6) HANDLERS
# ----------------------------
@dp.message(F.text == "/start")
async def cmd_start(m: Message):
    await db_upsert_user(m.from_user.id)
    photo_meta = {"file_id": PROGRESS_PHOTO_ID} if PROGRESS_PHOTO_ID else {"file": "media/img1.png"}
    await m.answer_photo(
        _resolve_media_source(photo_meta),
        caption=(
            "Привет! Я Вайбик 🐶✨\n"
            "Здесь будет новогодняя история на <b>7 дней</b>.\n\n"
            "Нажимай ниже:"
        ),
        reply_markup=menu_kb()
    )

@dp.callback_query(F.data == "menu")
async def cb_menu(c: CallbackQuery):
    await c.message.answer("Меню:", reply_markup=menu_kb())
    await c.answer()

@dp.callback_query(F.data == "progress")
async def cb_progress(c: CallbackQuery):
    user = await db_get_user(c.from_user.id)
    if not user:
        await db_upsert_user(c.from_user.id)
        user = await db_get_user(c.from_user.id)

    sparks = _split_pipe(user["sparks"])
    codes = _split_pipe(user["codes"])
    opened_day = user["opened_day"]

    text = (
        f"✨ <b>Твой прогресс</b>\n\n"
        f"Открыто дней: <b>{opened_day}/7</b>\n"
        f"Искры: <b>{len(sparks)}/7</b>\n"
        f"Буквы: <b>{len(codes)}/7</b>\n\n"
        f"Буквы: {', '.join(codes) if sparks else 'пока нет'}"
    )
    media_meta = {"file_id": PROGRESS_PHOTO_ID} if PROGRESS_PHOTO_ID else {"file": "media/img1.png"}
    await c.message.answer_photo(
        _resolve_media_source(media_meta),
        caption=text,
        reply_markup=menu_kb()
    )
    await c.answer()

STEP_DELAY = float(os.getenv("STEP_DELAY", "1.5"))

@dp.callback_query(F.data == "open_day")
async def cb_open_day(c: CallbackQuery):
    user = await db_get_user(c.from_user.id)
    if not user:
        await db_upsert_user(c.from_user.id)
        user = await db_get_user(c.from_user.id)

    day = user["opened_day"]
    # начинаем день с первого шага
    await db_set_progress(c.from_user.id, active_day=day, active_step=0)

    title = CONTENT.get(day, {}).get("title", f"День {day}")
    await c.message.answer(f"📅 <b>{title}</b>\n(пойдём по сообщениям шаг за шагом)", reply_markup=None)
    await sleep(STEP_DELAY)
    await send_step(c.from_user.id, day, 0)
    await c.answer()

@dp.callback_query(F.data.startswith("next:"))
async def cb_next(c: CallbackQuery):
    # next:day:step
    _, day_s, step_s = c.data.split(":")
    day = int(day_s)
    step_idx = int(step_s)

    user = await db_get_user(c.from_user.id)
    if not user:
        await c.answer("Нажми /start 🙂", show_alert=True)
        return

    # защита от старых кнопок
    if user["active_day"] != day or user["active_step"] != step_idx:
        await c.answer("Эта кнопка уже неактуальна 🙂", show_alert=False)
        return

    # убираем кнопки у прошлого сообщения (чтобы не нажимали по 10 раз)
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    new_step = step_idx + 1
    await db_set_progress(c.from_user.id, active_day=day, active_step=new_step)
    await send_step(c.from_user.id, day, new_step)
    await c.answer()

@dp.callback_query(F.data.startswith("mode:"))
async def cb_mode(c: CallbackQuery):
    # mode:day:step:value
    _, day_s, step_s, value = c.data.split(":")
    day = int(day_s)
    step_idx = int(step_s)

    user = await db_get_user(c.from_user.id)
    if not user:
        await c.answer("Нажми /start 🙂", show_alert=True)
        return

    if user["active_day"] != day or user["active_step"] != step_idx:
        await c.answer("Эта кнопка уже неактуальна 🙂", show_alert=False)
        return

    await db_set_mode(c.from_user.id, value)

    # уберём кнопки выбора режима у сообщения
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # после выбора режима автоматически отправим:
    # 1) ответ (следующий шаг)
    # 2) финал (ещё следующий шаг)
    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 1)
    await send_step(c.from_user.id, day, step_idx + 1)

    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 2)
    await send_step(c.from_user.id, day, step_idx + 2)

    await c.answer("Принято ✅")

@dp.callback_query(F.data.startswith("glow:"))
async def cb_glow(c: CallbackQuery):
    # glow:day:step:value
    _, day_s, step_s, _choice = c.data.split(":")
    day = int(day_s)
    step_idx = int(step_s)

    user = await db_get_user(c.from_user.id)
    if not user:
        await c.answer("Нажми /start 🙂", show_alert=True)
        return

    if user["active_day"] != day or user["active_step"] != step_idx:
        await c.answer("Эта кнопка уже неактуальна 🙂", show_alert=False)
        return

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 1)
    await send_step(c.from_user.id, day, step_idx + 1)

    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 2)
    await send_step(c.from_user.id, day, step_idx + 2)

    await c.answer("Сияние активировано ✨")

@dp.callback_query(F.data.startswith("aroma:"))
async def cb_aroma(c: CallbackQuery):
    # aroma:day:step:value
    _, day_s, step_s, _choice = c.data.split(":")
    day = int(day_s)
    step_idx = int(step_s)

    user = await db_get_user(c.from_user.id)
    if not user:
        await c.answer("Нажми /start 🙂", show_alert=True)
        return

    if user["active_day"] != day or user["active_step"] != step_idx:
        await c.answer("Эта кнопка уже неактуальна 🙂", show_alert=False)
        return

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 1)
    await send_step(c.from_user.id, day, step_idx + 1)

    await db_set_progress(c.from_user.id, active_day=day, active_step=step_idx + 2)
    await send_step(c.from_user.id, day, step_idx + 2)

    await c.answer("Аромат сохранён 🌸")

@dp.callback_query(F.data.startswith("spark:"))
async def cb_spark(c: CallbackQuery):
    # spark:day
    _, day_s = c.data.split(":")
    day = int(day_s)

    user = await db_get_user(c.from_user.id)
    if not user:
        await c.answer("Нажми /start 🙂", show_alert=True)
        return

    day_data = CONTENT.get(day)
    if not day_data:
        await c.answer("Странно… такого дня нет", show_alert=True)
        return

    await db_add_spark_code(c.from_user.id, day_data["spark_name"], day_data["code_part"])

    # убираем кнопки у сообщения с искрой
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    caption = (
        f"✨ Ты получила: <b>{day_data['spark_name']}</b>\n"
        f"🔑 Одна буква секретного слова: <code>{day_data['code_part']}</code>\n\n"
        "Увидимся завтра 🤍"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu")
    kb.adjust(1)

    await c.message.answer_photo(
        _resolve_media_source({"file_id": "AgACAgIAAxkBAAOvaUgnNw2JzDxnByBIIpwFPoQob4IAAhAPaxt2VUFKQl2M5j59ho0BAAMCAAN5AAM2BA"}),
        caption=caption,
        reply_markup=kb.as_markup()
    )
    await c.answer("Искра добавлена ✅")

# (опционально) ловушка file_id стикеров: отправь стикер боту, он пришлёт file_id
@dp.message(F.sticker)
async def sticker_file_id(m: Message):
    await m.answer(f"file_id:\n<code>{m.sticker.file_id}</code>")

@dp.message(F.photo)
async def photo_file_id(m: Message):
    user = await db_get_user(m.from_user.id)
    if user and user["active_day"] == 4 and user["active_step"] == 2:
        step_idx = user["active_step"]
        try:
            await bot.send_photo(791104636, m.photo[-1].file_id)
        except Exception:
            pass

        await db_set_progress(m.from_user.id, active_day=4, active_step=step_idx + 1)
        await send_step(m.from_user.id, 4, step_idx + 1)

        # Pause before the gift step.
        await sleep(DAY4_BEAGLE_DELAY)

        await db_set_progress(m.from_user.id, active_day=4, active_step=step_idx + 2)
        await send_step(m.from_user.id, 4, step_idx + 2)
        return

    await m.answer(f"file_id:\n<code>{m.photo[-1].file_id}</code>")


# ----------------------------
# 7) BACKGROUND LOOP (unlock checker)
# ----------------------------
async def unlock_loop():
    while True:
        try:
            await db_unlock_next_day_for_due_users()
        except Exception:
            pass
        await asyncio.sleep(300)  # каждые 5 минут

# ----------------------------
# 8) MAIN
# ----------------------------
async def main():
    await db_init()

    # запускаем цикл открытия новых дней
    asyncio.create_task(unlock_loop())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

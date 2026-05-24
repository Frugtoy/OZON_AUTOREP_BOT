import asyncio
import logging
from random import choice

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from services import ReviewService
from fileworker import (
    get_all_reviews,
    get_reviews_for_rating,
    add_review_to_rating,
    remove_review_from_rating,
    save_reviews,
)

logger = logging.getLogger(__name__)
router = Router()

sudo = settings.admin_ids
ADMIN_LIST = get_all_reviews().get("admin_list", settings.admin_ids)

service = ReviewService()


class Form(StatesGroup):
    ADD_REVIEW_TEXT = State()
    DELETE_REVIEW_SELECTION = State()
    FILTER_RATING_ACTION = State()
    ADMIN_ADD_USER = State()
    ADMIN_REMOVE_USER = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_LIST


def generate_random_review() -> str:
    active_ratings = get_all_reviews().get("score_list", [])
    if not active_ratings:
        return "Нет активных рейтингов!"
    chosen = choice(active_ratings)
    reviews = get_reviews_for_rating(f"rating_{chosen}")
    if not reviews:
        return f"Нет отзывов для рейтинга {chosen}."
    return choice(reviews)


def format_reviews(reviews: dict, rating: int) -> str:
    items = reviews.get(f"rating_{rating}", [])
    if not items:
        return f"Нет отзывов для рейтинга {rating}.\n"
    return "\n".join([f"➤ {rating}.{i+1}) {r}" for i, r in enumerate(items)])


# ─── Start ───────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message):
    if is_admin(message.from_user.id):
        kb = InlineKeyboardBuilder()
        kb.button(text="Настройка конфига", callback_data="config_setup")
        kb.button(text="Посмотреть конфиг", callback_data="view_config")
        kb.button(text="Настройка администрации", callback_data="admin_setup")
        kb.button(text="Запустить автоматические ответы", callback_data="start_auto_answers")
        kb.button(text="Остановить автоматические ответы", callback_data="stop_auto_answers")
        kb.button(text="Статистика", callback_data="dashboard")
        kb.adjust(1)
        await message.answer(
            "Добро пожаловать в бот управления отзывами! Выберите действие:",
            reply_markup=kb.as_markup(),
        )
    else:
        await message.answer("Добро пожаловать! У вас нет прав для полного доступа.")


# ─── Config view ─────────────────────
@router.callback_query(F.data == "view_config")
async def view_config(callback: CallbackQuery):
    settings_data = get_all_reviews()
    active = settings_data.get("score_list", [])
    stats = "\n".join(format_reviews(settings_data, r) for r in active)
    report = (
        f"📌 *Активные рейтинги:* `{', '.join(map(str, active))}`\n\n"
        f"*Отзывы по каждому рейтингу:*\n{stats}"
    )
    await callback.message.edit_text(report, parse_mode="Markdown")


# ─── Config setup ────────────────────
@router.callback_query(F.data == "config_setup")
async def setup_config(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить отзыв", callback_data="add_review")
    kb.button(text="Удалить отзыв", callback_data="delete_review")
    kb.button(text="Фильтр рейтинга", callback_data="filter_rating")
    kb.adjust(1)
    await callback.message.edit_text("Выберите операцию:", reply_markup=kb.as_markup())


# ─── Add review ──────────────────────
@router.callback_query(F.data == "add_review")
async def add_review_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for r in range(1, 6):
        kb.button(text=f"{r} звезда(-ы)", callback_data=f"add_review_rating_{r}")
    kb.adjust(5)
    await callback.message.edit_text("Выберите рейтинг:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("add_review_rating_"))
async def select_rating_add(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[3])
    await state.update_data(selected_rating=rating)
    await state.set_state(Form.ADD_REVIEW_TEXT)
    await callback.message.edit_text("Введите текст отзыва:")


@router.message(Form.ADD_REVIEW_TEXT)
async def process_add_review(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    rating = data["selected_rating"]
    add_review_to_rating(str(rating), text)
    await state.clear()
    await message.answer("Отзыв успешно добавлен!")


# ─── Delete review ───────────────────
@router.callback_query(F.data == "delete_review")
async def delete_review_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for r in range(1, 6):
        kb.button(text=f"{r} звезда(-ы)", callback_data=f"delete_review_rating_{r}")
    kb.adjust(5)
    await callback.message.edit_text("Выберите рейтинг:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("delete_review_rating_"))
async def select_rating_delete(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[3])
    reviews = get_reviews_for_rating(f"rating_{rating}")
    if not reviews:
        await callback.message.edit_text("Нет отзывов для этого рейтинга.")
        return
    kb = InlineKeyboardBuilder()
    for i, rev in enumerate(reviews):
        kb.button(text=f"{i+1}. {rev[:20]}...", callback_data=f"delete_review_confirm_{i}_{rating}")
    kb.adjust(1)
    await callback.message.edit_text("Выберите отзыв:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("delete_review_confirm_"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    _, _, idx, rating = callback.data.split("_")
    idx = int(idx)
    all_rev = get_all_reviews()
    reviews = all_rev[f"rating_{rating}"]
    removed = reviews.pop(idx)
    all_rev[f"rating_{rating}"] = reviews
    save_reviews(all_rev)
    await callback.message.edit_text(
        f"Удалён отзыв №{idx+1}:\n*{removed}*", parse_mode="Markdown"
    )


# ─── Filter rating ───────────────────
@router.callback_query(F.data == "filter_rating")
async def filter_rating(callback: CallbackQuery, state: FSMContext):
    settings_data = get_all_reviews()
    active = settings_data.get("score_list", [])
    kb = InlineKeyboardBuilder()
    kb.button(text="🖍️ Очистить фильтры", callback_data="clear_filters")
    kb.button(text="📋 Добавить рейтинг", callback_data="add_rating")
    kb.button(text="❌ Удалить рейтинг", callback_data="remove_rating")
    kb.adjust(1)
    await callback.message.edit_text(
        f"Текущие активные: `{', '.join(map(str, active))}`",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "clear_filters")
async def clear_filters(callback: CallbackQuery):
    data = get_all_reviews()
    data["score_list"] = []
    save_reviews(data)
    await callback.message.edit_text("✅ Фильтры очищены.")


@router.callback_query(F.data == "add_rating")
async def add_rating_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.FILTER_RATING_ACTION)
    await callback.message.edit_text("Введите число от 1 до 5:")


@router.message(Form.FILTER_RATING_ACTION)
async def process_add_rating(message: Message, state: FSMContext):
    r = message.text.strip()
    if not r.isdigit() or not 1 <= int(r) <= 5:
        await message.answer("Введите число от 1 до 5.")
        return
    data = get_all_reviews()
    data["score_list"] = sorted(list(set(data.get("score_list", []) + [int(r)])))
    save_reviews(data)
    await state.clear()
    await message.answer(f"Рейтинг *{r}* добавлен.", parse_mode="Markdown")


@router.callback_query(F.data == "remove_rating")
async def remove_rating_start(callback: CallbackQuery, state: FSMContext):
    data = get_all_reviews()
    active = data.get("score_list", [])
    if not active:
        await callback.message.edit_text("Нет активных рейтингов.")
        return
    kb = InlineKeyboardBuilder()
    for r in active:
        kb.button(text=f"{r} звезда(-ы)", callback_data=f"remove_rating_confirm_{r}")
    kb.adjust(1)
    await callback.message.edit_text("Выберите рейтинг:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("remove_rating_confirm_"))
async def confirm_remove_rating(callback: CallbackQuery):
    r = int(callback.data.split("_")[3])
    data = get_all_reviews()
    data["score_list"].remove(r)
    save_reviews(data)
    await callback.message.edit_text(f"Рейтинг *{r}* удалён.", parse_mode="Markdown")


# ─── Admin setup ─────────────────────
@router.callback_query(F.data == "admin_setup")
async def admin_setup(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("Нужны права администратора.")
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить администратора", callback_data="add_admin")
    kb.button(text="Удалить администратора", callback_data="remove_admin")
    kb.adjust(1)
    await callback.message.edit_text("Выбор действия:", reply_markup=kb.as_markup())


@router.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("Нужны права.")
        return
    await state.set_state(Form.ADMIN_ADD_USER)
    await callback.message.edit_text("Введите chat_id пользователя:")


@router.message(Form.ADMIN_ADD_USER)
async def process_add_admin(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("chat_id должен быть целым числом.")
        return
    uid = int(uid)
    data = get_all_reviews()
    data.setdefault("admin_list", []).append(uid)
    save_reviews(data)
    await state.clear()
    await message.answer(f"Пользователь {uid} добавлен.")


@router.callback_query(F.data == "remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("Нужны права.")
        return
    await state.set_state(Form.ADMIN_REMOVE_USER)
    await callback.message.edit_text("Введите chat_id для удаления:")


@router.message(Form.ADMIN_REMOVE_USER)
async def process_remove_admin(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("chat_id должен быть целым числом.")
        return
    uid = int(uid)
    data = get_all_reviews()
    if uid in data.get("admin_list", []):
        data["admin_list"].remove(uid)
        save_reviews(data)
        await state.clear()
        await message.answer(f"Пользователь {uid} удалён.")
    else:
        await message.answer("Пользователь не найден.")


# ─── Auto answers ────────────────────
auto_tasks: dict[int, asyncio.Task] = {}


async def auto_loop(chat_id: int, bot):
    while True:
        await bot.send_message(chat_id, generate_random_review())
        await asyncio.sleep(5)


@router.callback_query(F.data == "start_auto_answers")
async def start_auto(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id in auto_tasks:
        await callback.message.edit_text("Автоответчик уже запущен.")
        return
    task = asyncio.create_task(auto_loop(chat_id, callback.bot))
    auto_tasks[chat_id] = task
    await callback.message.edit_text("Автоответчик запущен.")


@router.callback_query(F.data == "stop_auto_answers")
async def stop_auto(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id in auto_tasks:
        auto_tasks.pop(chat_id).cancel()
        await callback.message.edit_text("Автоответчик остановлен.")
    else:
        await callback.message.edit_text("Автоответчик не запущен.")


# ─── Dashboard ─────────────────────
@router.callback_query(F.data == "dashboard")
async def get_dashboard(callback: CallbackQuery):
    from pathlib import Path

    path = Path("data/rewiews_counter.json")
    if not path.exists():
        await callback.message.edit_text("Нет данных.")
        return
    text = path.read_text(encoding="utf-8")
    await callback.message.edit_text(f"📊 Статистика:\n```\n{text}\n```", parse_mode="Markdown")

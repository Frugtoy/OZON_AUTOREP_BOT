from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from dotenv import load_dotenv
from fileworker import *  # Импортируем модуль fileworker
import asyncio 
import random
from autorep import run as autorep_run
import dashboard
load_dotenv()

# Настройки бота
router = Router()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

sudo = [438662734]
ADMIN_LIST = get_all_reviews().get('admin_list', [438662734])  # Списки администраторов хранятся в конфигурации

# Класс состояний
class Form(StatesGroup):
    ADD_REVIEW_TEXT = State()
    DELETE_REVIEW_SELECTION = State()
    FILTER_RATING_ACTION = State()
    ADMIN_ADD_USER = State()
    ADMIN_REMOVE_USER = State()

# Проверка на присутствие пользователя в списке администраторов
def is_admin(user_id):
    return user_id in ADMIN_LIST

# Генерация случайного отзыва из активного рейтинга
def generate_random_review():
    active_ratings = get_all_reviews()['score_list']
    if not active_ratings:
        return "Нет активных рейтингов!"
    chosen_rating = random.choice(active_ratings)
    reviews = get_reviews_for_rating(f'rating_{chosen_rating}')
    if not reviews:
        return f"Нет отзывов для рейтинга {chosen_rating}."
    return random.choice(reviews)

# Автоответчик
async def auto_answer_task(chat_id):
    while True:
        await bot.send_message(chat_id, generate_random_review())
        await asyncio.sleep(5)

auto_answer_tasks = {}  # Хранение запущенных автоответчиков по chat_id

# Главная страница
@router.message(CommandStart())
async def cmd_start(message: Message):
    print(message.from_user.id)
    if is_admin(message.from_user.id):
        menu_kb = InlineKeyboardBuilder()
        menu_kb.button(text="Настройка конфига", callback_data='config_setup')
        menu_kb.button(text="Посмотреть конфиг", callback_data='view_config')
        menu_kb.button(text="Настройка администрации", callback_data='admin_setup')
        menu_kb.button(text="Запустить автоматические ответы", callback_data='start_auto_answers')
        menu_kb.button(text="Остановить автоматические ответы", callback_data='stop_auto_answers')
        menu_kb.button(text="Статистика", callback_data='dashboard')
        menu_kb.adjust(1)
        await message.answer("Добро пожаловать в бот управления отзывами! Выберите действие:", reply_markup=menu_kb.as_markup())
    else:
        await message.answer("Добро пожаловать в бот управления отзывами! У вас нет прав для полного доступа.")

# Настройка администрации
@router.callback_query(F.data == 'admin_setup')
async def admin_setup(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Вам нужны права администратора для выполнения этой операции."
        )
        return
    admin_kb = InlineKeyboardBuilder()
    admin_kb.button(text="Добавить администратора", callback_data='add_admin')
    admin_kb.button(text="Удалить администратора", callback_data='remove_admin')
    admin_kb.adjust(1)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выбор действия для администрирования:",
        reply_markup=admin_kb.as_markup()
    )

# Добавление администратора
@router.callback_query(F.data == 'add_admin')
async def add_admin_start(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Вам нужны права администратора для выполнения этой операции."
        )
        return
    await state.set_state(Form.ADMIN_ADD_USER)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите chat_id пользователя, которого хотите добавить в администраторы:"
    )

@router.message(Form.ADMIN_ADD_USER)
async def process_add_admin(message: Message, state: FSMContext):
    new_admin_id = message.text.strip()
    if not new_admin_id.isdigit():
        await message.answer("chat_id должен быть целым числом.")
        return
    new_admin_id = int(new_admin_id)
    settings = get_all_reviews()
    settings['admin_list'].append(new_admin_id)
    save_reviews(settings)
    await state.clear()
    await message.answer(f"Пользователь с chat_id {new_admin_id} успешно добавлен в администраторы.")

# Удаление администратора
@router.callback_query(F.data == 'remove_admin')
async def remove_admin_start(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Вам нужны права администратора для выполнения этой операции."
        )
        return
    await state.set_state(Form.ADMIN_REMOVE_USER)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите chat_id пользователя, которого хотите удалить из администраторов:"
    )

@router.message(Form.ADMIN_REMOVE_USER)
async def process_remove_admin(message: Message, state: FSMContext):
    admin_id = message.text.strip()
    if not admin_id.isdigit():
        await message.answer("chat_id должен быть целым числом.")
        return
    admin_id = int(admin_id)
    settings = get_all_reviews()
    if admin_id in settings['admin_list']:
        settings['admin_list'].remove(admin_id)
        save_reviews(settings)
        await state.clear()
        await message.answer(f"Пользователь с chat_id {admin_id} успешно удалён из администраторов.")
    else:
        await message.answer("Такой пользователь не найден среди администраторов.")

# Автозапуск сообщений
@router.callback_query(F.data == 'start_auto_answers')
async def start_auto_answers(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id in auto_answer_tasks:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Автоответчик уже запущен."
        )
        return
    
    task = asyncio.create_task(autorep_run())
    auto_answer_tasks[chat_id] = task
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Автоответчик запущен. Ответы отправляются каждые 5 секунд."
    )

# Завершение автозапуска сообщений
@router.callback_query(F.data == 'stop_auto_answers')
async def stop_auto_answers(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    if chat_id in auto_answer_tasks:
        task = auto_answer_tasks.pop(chat_id)
        task.cancel()
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Автоответчик остановлен."
        )
    else:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Автоответчик не запущен."
        )


@router.callback_query(F.data == 'dashboard')
async def get_dashboard(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    # print(dashboard.get_bd_stat())
    with open('data/rewiews_counter.json') as file:
        buf = file.read()[1:-1]
        
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"{buf}"
    )


# Форматирование красивого представления данных
def format_reviews_by_rating(reviews, rating):
    review_list = reviews.get(f'rating_{rating}', [])
    if not review_list:
        return f"Нет отзывов для рейтинга {rating}.\n"
    return "\n".join([f"➤ {rating}.{i+1}) {review}" for i, review in enumerate(review_list)])
# # Главная страница
# @router.message(CommandStart())
# async def cmd_start(message: Message):
#     menu_kb = InlineKeyboardBuilder()
#     menu_kb.button(text="Настройка конфига", callback_data='config_setup')
#     menu_kb.button(text="Посмотреть конфиг", callback_data='view_config')
#     menu_kb.adjust(1)
#     await message.answer("Добро пожаловать в бот управления отзывами! Выберите действие:", reply_markup=menu_kb.as_markup())

# Просмотр текущей конфигурации
@router.callback_query(F.data == 'view_config')
async def view_current_config(callback_query: CallbackQuery):
    settings = get_all_reviews()
    active_ratings = settings['score_list']
    stats = f"\n".join(format_reviews_by_rating(settings, rating) for rating in active_ratings)
    report = (
        f"📌 *Активные рейтинги:* `{', '.join(map(str, active_ratings))}`\n\n"
        f"*Отзывы по каждому рейтингу:*\n{stats}"
    )
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=report,
        parse_mode="Markdown"
    )

# Настройка конфига
@router.callback_query(F.data == 'config_setup')
async def setup_config(callback_query: CallbackQuery):
    config_kb = InlineKeyboardBuilder()
    config_kb.button(text="Добавить отзыв", callback_data='add_review')
    config_kb.button(text="Удалить отзыв", callback_data='delete_review')
    config_kb.button(text="Фильтр рейтинга", callback_data='filter_rating')
    config_kb.adjust(1)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите операцию для настройки:",
        reply_markup=config_kb.as_markup()
    )

# Добавление отзыва
@router.callback_query(F.data == 'add_review')
async def add_review_start(callback_query: CallbackQuery, state: FSMContext):
    ratings_kb = InlineKeyboardBuilder()
    for rating in range(1, 6):
        ratings_kb.button(text=f"{rating} звезда(-ы)", callback_data=f'add_review_rating_{rating}')
    ratings_kb.adjust(5)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите рейтинг для отзыва:",
        reply_markup=ratings_kb.as_markup()
    )

@router.callback_query(F.data.startswith('add_review_rating_'))
async def select_rating_for_add(callback_query: CallbackQuery, state: FSMContext):
    selected_rating = int(callback_query.data.split("_")[3])
    await state.update_data(selected_rating=selected_rating)
    await state.set_state(Form.ADD_REVIEW_TEXT)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите текст отзыва:"
    )

@router.message(Form.ADD_REVIEW_TEXT)
async def process_add_review_text(message: Message, state: FSMContext):
    review_text = message.text.strip()
    user_data = await state.get_data()
    selected_rating = user_data['selected_rating']
    add_review_to_rating(str(selected_rating), review_text)
    await state.clear()
    await message.answer("Отзыв успешно добавлен!")

# Удаление отзыва
@router.callback_query(F.data == 'delete_review')
async def delete_review_start(callback_query: CallbackQuery, state: FSMContext):
    ratings_kb = InlineKeyboardBuilder()
    for rating in range(1, 6):
        ratings_kb.button(text=f"{rating} звезда(-ы)", callback_data=f'delete_review_rating_{rating}')
    ratings_kb.adjust(5)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите рейтинг для удаления отзыва:",
        reply_markup=ratings_kb.as_markup()
    )

@router.callback_query(F.data.startswith('delete_review_rating_'))
async def select_rating_for_delete(callback_query: CallbackQuery, state: FSMContext):
    selected_rating = int(callback_query.data.split("_")[3])
    reviews = get_reviews_for_rating(f'rating_{selected_rating}')
    if not reviews:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Нет отзывов для этого рейтинга."
        )
        return
    reviews_kb = InlineKeyboardBuilder()
    for idx, review in enumerate(reviews):
        reviews_kb.button(text=f"{idx + 1}. {review[:20]}...", callback_data=f'delete_review_confirm_{idx}_{selected_rating}')
    reviews_kb.adjust(1)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите отзыв для удаления:",
        reply_markup=reviews_kb.as_markup()
    )

@router.callback_query(F.data.startswith('delete_review_confirm_'))
async def confirm_delete_review(callback_query: CallbackQuery, state: FSMContext):
    _, index, selected_rating = callback_query.data.split("_")[2:]
    index = int(index)
    # Получаем ВСЕ данные отзывов
    all_reviews = get_all_reviews()
    # Получаем конкретно тот рейтинг, который хотим изменить
    reviews = all_reviews[f'rating_{selected_rating}']
    # Удаляем отзыв из нужного рейтинга
    removed_review = reviews.pop(index)
    # Сохраняем изменения обратно в общую структуру
    all_reviews[f'rating_{selected_rating}'] = reviews
    # Сохраняем откорректированные данные
    save_reviews(all_reviews)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Удалён отзыв №{index + 1}:\n*{removed_review}*",
        parse_mode="Markdown"
    )

# Настройка фильтра рейтинга
@router.callback_query(F.data == 'filter_rating')
async def manage_filter_rating(callback_query: CallbackQuery, state: FSMContext):
    settings = get_all_reviews()
    active_ratings = settings['score_list']
    filter_kb = InlineKeyboardBuilder()
    filter_kb.button(text="🖍️ Очистить фильтры", callback_data='clear_filters')
    filter_kb.button(text="📋 Добавить рейтинг", callback_data='add_rating')
    filter_kb.button(text="❌ Удалить рейтинг", callback_data='remove_rating')
    filter_kb.adjust(1)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Текущие активные рейтинги: `{', '.join(map(str, active_ratings))}`",
        reply_markup=filter_kb.as_markup(),
        parse_mode="Markdown"
    )

# Очистка фильтров
@router.callback_query(F.data == 'clear_filters')
async def clear_filters(callback_query: CallbackQuery):
    settings = get_all_reviews()
    settings['score_list'] = []
    save_reviews(settings)
    
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="✅ Текущие фильтры успешно очищены.",
        parse_mode="Markdown"
    )

# Добавление рейтинга в фильтр
@router.callback_query(F.data == 'add_rating')
async def add_rating_start(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(Form.FILTER_RATING_ACTION)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите число от 1 до 5 для добавления в фильтр:"
    )

@router.message(Form.FILTER_RATING_ACTION)
async def process_add_rating(message: Message, state: FSMContext):
    rating = message.text.strip()
    if not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
        await message.answer("Введено неправильное значение. Введите число от 1 до 5.")
        return
    settings = get_all_reviews()
    settings['score_list'].append(int(rating))
    settings['score_list'] = sorted(list(set(settings['score_list'])))  # Сортируем и устраняем дублирование
    save_reviews(settings)
    await state.clear()
    await message.answer(f"Рейтинг *{rating}* успешно добавлен в фильтр.", parse_mode="Markdown")

# Удаление рейтинга из фильтра
@router.callback_query(F.data == 'remove_rating')
async def remove_rating_start(callback_query: CallbackQuery, state: FSMContext):
    settings = get_all_reviews()
    active_ratings = settings['score_list']
    if not active_ratings:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Нет активных рейтингов для удаления."
        )
        return
    ratings_kb = InlineKeyboardBuilder()
    for rating in active_ratings:
        ratings_kb.button(text=f"{rating} звезда(-ы)", callback_data=f'remove_rating_confirm_{rating}')
    ratings_kb.adjust(1)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите рейтинг для удаления из фильтра:",
        reply_markup=ratings_kb.as_markup()
    )

@router.callback_query(F.data.startswith('remove_rating_confirm_'))
async def confirm_remove_rating(callback_query: CallbackQuery, state: FSMContext):
    selected_rating = int(callback_query.data.split("_")[2])
    settings = get_all_reviews()
    settings['score_list'].remove(selected_rating)
    save_reviews(settings)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Рейтинг *{selected_rating}* успешно удалён из фильтра.",
        parse_mode="Markdown"
    )

# Регистрация роутеров
dp.include_router(router)

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)
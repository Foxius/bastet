from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

from database import (
    create_connection,
    add_user_to_stats,
    get_active_task,
    get_random_task,
    add_task_to_user,
    update_user_stats,
    delete_task_from_user,
    get_user_stats,
    add_task,
    delete_task,
    get_task_by_id,
    get_all_tasks,
)
from loader import bot
from config import CHAT_ID, ADMIN_IDS

# Создаем роутер
router = Router()

import logging

logging.basicConfig(level=logging.INFO)

# Состояния для FSM
class TaskState(StatesGroup):
    waiting_for_task = State()
    waiting_for_new_task = State()
    waiting_for_task_to_delete = State()
    viewing_tasks = State()

# Кастомный фильтр для проверки прав администратора
class AdminFilter:
    def __call__(self, message: types.Message) -> bool:
        is_admin = message.from_user.id in ADMIN_IDS
        logging.info(f"User {message.from_user.id} is admin: {is_admin}")
        return is_admin
    
# Команда /start
@router.message(Command("start"))
async def start(message: types.Message):
    if message.chat.id != CHAT_ID:
        return
    
    user_id = message.from_user.id
    conn = create_connection()
    add_user_to_stats(conn, user_id)
    conn.close()
    
    await message.reply("Привет! Я бот для выдачи заданий. Используй /task, чтобы получить задание.")

# Команда /task
@router.message(Command("task"))
async def get_task(message: types.Message, state: FSMContext):
    if message.chat.id != CHAT_ID:
        return
    
    user_id = message.from_user.id
    conn = create_connection()
    
    if get_active_task(conn, user_id):
        await message.reply("У вас уже есть активное задание.")
        conn.close()
        return
    
    task = get_random_task(conn)
    
    if not task:
        await message.reply("Задания закончились.")
        conn.close()
        return
    
    task_id, task_text = task
    add_task_to_user(conn, user_id, task_id)
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    accept_button = InlineKeyboardButton("Принять", callback_data=f"accept:{user_id}:{task_id}")
    decline_button = InlineKeyboardButton("Отказаться", callback_data=f"decline:{user_id}:{task_id}")
    keyboard.add(accept_button, decline_button)
    
    await message.reply(f"Ваше задание: {task_text}", reply_markup=keyboard)
    await state.set_state(TaskState.waiting_for_task)
    conn.close()

# Команда /stats
@router.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.chat.id != CHAT_ID:
        return
    
    user_id = message.from_user.id
    conn = create_connection()
    
    completed_tasks = get_user_stats(conn, user_id)
    
    await message.reply(f"Ваша статистика: {completed_tasks} выполненных заданий.")
    
    conn.close()

@router.message(Command("addtask"), AdminFilter())
async def add_task_command(message: types.Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} started /addtask command.")
    await message.reply("Пожалуйста, введите текст нового задания.")
    await state.set_state(TaskState.waiting_for_new_task)
    logging.info(f"State set to TaskState.waiting_for_new_task for user {message.from_user.id}.")

@router.message(TaskState.waiting_for_new_task)
async def process_new_task(message: types.Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} submitted a new task: {message.text}")
    conn = create_connection()
    try:
        add_task(conn, message.text)
        await message.reply("Задание успешно добавлено.")
    except Exception as e:
        logging.error(f"Error adding task: {e}")
        await message.reply("Произошла ошибка при добавлении задания.")
    finally:
        conn.close()
        await state.clear()

# Обработка нажатий кнопок (принять/отклонить задание)
@router.callback_query(lambda c: c.data.startswith(('accept', 'decline')))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, user_id, task_id = callback_query.data.split(":")
    
    user_id = int(user_id)
    
    conn = create_connection()
    
    if action == "accept":
        await callback_query.answer("Задание принято!")
    elif action == "decline":
        update_user_stats(conn, user_id, -1)
        await callback_query.answer("Задание отклонено!")
    
    delete_task_from_user(conn, user_id)
    stats = get_user_stats(conn, user_id)
    
    await callback_query.message.edit_text(f"Статистика: {stats} заданий.")
    
    await state.clear()
    conn.close()

# Обработка сообщений от администраторов для зачета задания
@router.message(StateFilter(None))
async def process_admin_feedback(message: types.Message):
    if message.chat.id != CHAT_ID:
        return
    
    if not message.reply_to_message:
        return
    
    user_id = message.reply_to_message.from_user.id
    feedback_text = message.text.lower()
    
    conn = create_connection()
    
    active_task = get_active_task(conn, user_id)
    
    if active_task:
        task_id = active_task[0]
        
        if feedback_text == "зачтено":
            update_user_stats(conn, user_id, 1)
            await message.reply("Задание зачтено. Статистика обновлена.")
        elif feedback_text == "не зачтено":
            update_user_stats(conn, user_id, -1)
            await message.reply("Задание не зачтено. Статистика обновлена.")
        
        delete_task_from_user(conn, user_id)
        stats = get_user_stats(conn, user_id)
        
        await bot.send_message(user_id, f"Ваша новая статистика: {stats} выполненных заданий.")
    
    conn.close()
        
# Команда /deletetask (только для администраторов)
@router.message(Command("deletetask"), AdminFilter())
async def delete_task_command(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, введите ID задания, которое нужно удалить.")
    await state.set_state(TaskState.waiting_for_task_to_delete)

# Обработка ID для удаления задания
@router.message(TaskState.waiting_for_task_to_delete)
async def process_task_to_delete(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text)
        conn = create_connection()
        task_text = get_task_by_id(conn, task_id)

        if task_text:
            delete_task(conn, task_id)
            await message.reply(f"Задание с ID {task_id} ('{task_text}') успешно удалено.")
        else:
            await message.reply("Задание с таким ID не найдено.")

        conn.close()
    except ValueError:
        await message.reply("Некорректный ID задания. Пожалуйста, введите число.")

    await state.clear()

# Команда /viewtasks (только для администраторов)
@router.message(Command("viewtasks"), AdminFilter())
async def view_tasks_command(message: types.Message):
    await show_tasks(message.from_user.id, 0)

# Функция для отображения задач с пагинацией
async def show_tasks(user_id: int, page: int):
    conn = create_connection()
    tasks = get_all_tasks(conn)

    tasks_per_page = 10
    total_pages = (len(tasks) + tasks_per_page - 1) // tasks_per_page
    start_index = page * tasks_per_page
    end_index = start_index + tasks_per_page

    keyboard = InlineKeyboardMarkup(row_width=1)

    for task in tasks[start_index:end_index]:
        task_id, task_text = task
        keyboard.add(InlineKeyboardButton(task_text, callback_data=f"task:{task_id}"))

    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton("Назад", callback_data=f"page:{page - 1}"))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед", callback_data=f"page:{page + 1}"))

    keyboard.add(*nav_buttons)

    await bot.send_message(user_id, "Список заданий:", reply_markup=keyboard)
    conn.close()

# Обработка нажатий кнопок навигации по страницам
@router.callback_query(lambda c: c.data.startswith('page:'))
async def process_navigation(callback_query: types.CallbackQuery):
    action, page_str = callback_query.data.split(":")
    page = int(page_str)
    await show_tasks(callback_query.from_user.id, page)
    await callback_query.answer()
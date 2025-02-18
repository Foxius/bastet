from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType

from database import (
    create_connection,
    add_user_to_stats,
    get_active_task,
    get_random_task,
    add_task_to_user,
    get_top_users,
    update_user_stats,
    delete_task_from_user,
    get_user_stats,
    add_task,
    delete_task,
    get_task_by_id,
    get_all_tasks,
)
from loader import bot
from config import CHATS, ADMIN_IDS

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
@router.message(Command("start"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def start(message: types.Message):
    user_id = message.from_user.id
    conn = create_connection()
    add_user_to_stats(conn, user_id)
    conn.close()
    
    await message.reply("Привет! Я бот для выдачи заданий. Используй /task, чтобы получить задание.")

# Команда /task
@router.message(Command("task"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def get_task(message: types.Message, state: FSMContext):
    if message.chat.id not in CHATS:
        return
    user_id = message.from_user.id

    conn = create_connection()
    add_user_to_stats(conn, user_id)

    # Проверяем, есть ли у пользователя активное задание
    if get_active_task(conn, user_id):
        await message.reply("У вас уже есть активное задание.")
        conn.close()
        return
    
    # Получаем случайное задание
    task = get_random_task(conn)
    
    if not task:
        await message.reply("Задания закончились.")
        conn.close()
        return
    
    task_id, task_text = task
    
    # Создаем кнопки
    accept_button = InlineKeyboardButton(text="Принять", callback_data=f"accept:{user_id}:{task_id}")
    decline_button = InlineKeyboardButton(text="Отказаться", callback_data=f"decline:{user_id}:{task_id}")
    
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[accept_button, decline_button]])
    
    await message.reply(f"Ваше задание: {task_text}\nОтчет отправлять @Miss_Bastet5", reply_markup=keyboard)
    await state.set_state(TaskState.waiting_for_task)
    conn.close()
    
# Обработчик для кнопок "Принять" и "Отказаться"
@router.callback_query(lambda c: c.data.startswith(('accept:', 'decline:')))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, user_id, task_id = callback_query.data.split(":")
    
    user_id = int(user_id)
    task_id = int(task_id)
    
    conn = create_connection()
    
    if action == "accept":
        # Добавляем задание в таблицу user_task как активное
        add_task_to_user(conn, user_id, task_id)
        tsk = get_task_by_id(conn, task_id)
        try:
            await bot.send_message(user_id, f"Ваше задание {tsk}\nОтчет отправлять @Miss_Bastet5")
        except:
            await bot.send_message(chat_id=callback_query.message.chat.id, text=f"Ваше задание {tsk}\nОтчет отправлять @Miss_Bastet5. Чтобы в будущем задания дублировались - нажмите кнопку 'старт' боту @bastet_task_bot")
        await callback_query.answer("Задание принято! Теперь вы можете его выполнять.")
    elif action == "decline":
        # Убираем задание (если нужно)
        delete_task_from_user(conn, user_id)
        await callback_query.answer("Задание отклонено.")
    
    # Редактируем сообщение с заданием
    await callback_query.message.edit_text("Вы приняли задание. Удачи!")
    
    # Очищаем состояние
    await state.clear()
    conn.close()

# Команда /addtask (только для администраторов в ЛС)
@router.message(Command("addtask"), AdminFilter(), F.chat.type == ChatType.PRIVATE)
async def add_task_command(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, введите текст нового задания.")
    await state.set_state(TaskState.waiting_for_new_task)

# Обработка нового задания
@router.message(TaskState.waiting_for_new_task, F.text, F.chat.type == ChatType.PRIVATE)
async def process_new_task(message: types.Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} submitted a new task: {message.text}")
    conn = create_connection()
    try:
        add_task(conn, message.text)
        await message.reply("Задание успешно добавлено.")
        logging.info(f"Task '{message.text}' added successfully.")
    except Exception as e:
        logging.error(f"Error adding task: {e}")
        await message.reply("Произошла ошибка при добавлении задания.")
    finally:
        conn.close()
        await state.clear()
        
# Команда /deletetask (только для администраторов в ЛС)
@router.message(Command("deletetask"), AdminFilter(), F.chat.type == ChatType.PRIVATE)
async def delete_task_command(message: types.Message, state: FSMContext):
    await show_tasks_for_deletion(message.from_user.id, 0)
    await state.set_state(TaskState.waiting_for_task_to_delete)

# Функция для отображения задач с кнопками для удаления
async def show_tasks_for_deletion(user_id: int, page: int):
    conn = create_connection()
    tasks = get_all_tasks(conn)

    tasks_per_page = 10
    total_pages = (len(tasks) + tasks_per_page - 1) // tasks_per_page
    start_index = page * tasks_per_page
    end_index = start_index + tasks_per_page

    # Создаем список кнопок для текущей страницы
    buttons = []
    for task in tasks[start_index:end_index]:
        task_id, task_text = task
        buttons.append([InlineKeyboardButton(text=task_text[:10], callback_data=f"delete_task:{task_id}")])

    # Создаем кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"delete_page:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед", callback_data=f"delete_page:{page + 1}"))

    # Добавляем кнопки навигации в список кнопок
    if nav_buttons:
        buttons.append(nav_buttons)

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.send_message(user_id, "Выберите задание для удаления:", reply_markup=keyboard)
    conn.close()

# Обработка нажатий кнопок для удаления заданий
@router.callback_query(lambda c: c.data.startswith(('delete_task:', 'delete_page:')))
async def process_delete_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, data = callback_query.data.split(":")

    if action == "delete_task":
        task_id = int(data)
        conn = create_connection()
        task_text = get_task_by_id(conn, task_id)

        if task_text:
            delete_task(conn, task_id)
            await callback_query.answer(f"Задание '{task_text}' успешно удалено.")
        else:
            await callback_query.answer("Задание с таким ID не найдено.")

        conn.close()
        await show_tasks_for_deletion(callback_query.from_user.id, 0)  # Обновляем список заданий

    elif action == "delete_page":
        page = int(data)
        await show_tasks_for_deletion(callback_query.from_user.id, page)
        await callback_query.answer()


@router.message(Command("accept"), AdminFilter(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def accept_task(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть вызвана в ответ на сообщение пользователя.")
        return
    
    user_id = message.reply_to_message.from_user.id
    conn = create_connection()
    
    # Получаем активное задание пользователя
    active_task = get_active_task(conn, user_id)
    if not active_task:
        await message.reply("У пользователя нет активного задания.")
        conn.close()
        return
    
    # Обновляем статистику пользователя (+1 к выполненным заданиям)
    update_user_stats(conn, user_id, 1)
    
    # Удаляем задание из активных
    delete_task_from_user(conn, user_id)
    
    await message.reply(f"Задание зачтено. Пользователь {message.reply_to_message.from_user.first_name} получил +1 к выполненным заданиям.")
    await bot.send_message(user_id, "Ваше задание зачтено. Статистика обновлена.")
    
    conn.close()
    
    
# Команда /stats
@router.message(Command("stats"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def stats_command(message: types.Message):
    
    user_id = message.from_user.id
    conn = create_connection()
    
    # Личная статистика
    completed_tasks = get_user_stats(conn, user_id)
    personal_stats = f"Ваша статистика: {completed_tasks} выполненных заданий.\n\n"
    
    # Общая статистика (топ-10)
    top_users = get_top_users(conn)
    if top_users:
        top_stats = "Топ-10 пользователей:\n"
        for idx, (user_id, tasks) in enumerate(top_users, start=1):
            try:
                user = await bot.get_chat(user_id)
                username = user.username if user.username else user.first_name
                top_stats += f"{idx}. {username}: {tasks} заданий\n"
            except Exception as e:
                logging.error(f"Ошибка при получении информации о пользователе {user_id}: {e}")
                top_stats += f"{idx}. Пользователь @{user_id}: {tasks} заданий\n"
    else:
        top_stats = "Топ пользователей пока пуст.\n"
    
    await message.reply(personal_stats + top_stats)
    
    conn.close()


@router.message(Command("decline"), AdminFilter(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def decline_task(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть вызвана в ответ на сообщение пользователя.")
        return
    
    user_id = message.reply_to_message.from_user.id
    conn = create_connection()
    
    # Получаем активное задание пользователя
    active_task = get_active_task(conn, user_id)
    if not active_task:
        await message.reply("У пользователя нет активного задания.")
        conn.close()
        return
    
    update_user_stats(conn, user_id, -1)
    # Убираем активное задание
    delete_task_from_user(conn, user_id)
    
    await message.reply(f"Задание не зачтено. Пользователь {message.reply_to_message.from_user.first_name} получает -1 балл.")
    await bot.send_message(user_id, "Ваше задание не зачтено.")
    
    conn.close()
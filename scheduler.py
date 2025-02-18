import asyncio
from aiogram import Bot

from config import CHATS

async def daily_task(bot: Bot):
    """
    Выполняет ежедневную рассылку заданий в указанные чаты.

    Каждые 6 часов отправляет фотографию с заданием и инструкцией
    в каждый чат из списка CHATS.

    :param bot: Экземпляр бота Aiogram.
    """
    while True:
        for chat_id in CHATS:
            try:
                await bot.send_photo(chat_id=str(chat_id), photo="https://i.imgur.com/qWg3vWs.png", caption="По команде /task можно получить задание. Чтобы задание дублировалось тебе в лс - напиши боту @bastet_task_bot команду /start")
            except Exception as e:
                print(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
        await asyncio.sleep(6 * 60 * 60)  # Пауза в 6 часов (6 * 60 * 60 секунд)

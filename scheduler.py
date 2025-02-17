import asyncio
from datetime import datetime, time, timedelta

from aiogram import Bot
from config import CHATS

async def daily_task(bot: Bot):
    # now = datetime.now()
    # target_time = time(12, 0)  # 12:00
    # print(123)
    # # Вычисляем время до следующего запуска
    # if now.time() > target_time:
    #     target_time = datetime.combine(now.date() + timedelta(days=1), target_time).time()
    
    # next_run = datetime.combine(now.date(), target_time)
    # wait_seconds = (next_run - now).total_seconds()
    # print(123)

    # await asyncio.sleep(wait_seconds)
    while True:
        for chat_id in CHATS:
            await bot.send_photo(chat_id=str(chat_id), photo="https://i.imgur.com/qWg3vWs.png", caption="По команде /task можно получить задание. Чтобы задание дублировалось тебе в лс - напиши боту @bastet_task_bot команду /start")
        await asyncio.sleep(6 * 60 * 60)  # 

import asyncio
from datetime import datetime, time, timedelta

from aiogram import Bot
from config import CHAT_ID

async def daily_task(bot: Bot):
    now = datetime.now()
    target_time = time(12, 0)  # 12:00
    
    # Вычисляем время до следующего запуска
    if now.time() > target_time:
        target_time = datetime.combine(now.date() + timedelta(days=1), target_time).time()
    
    next_run = datetime.combine(now.date(), target_time)
    wait_seconds = (next_run - now).total_seconds()
    
    await asyncio.sleep(wait_seconds)
    
    while True:
        await bot.send_message(CHAT_ID, "По команде /task можно получить задание.")
        
        await asyncio.sleep(24 * 60 * 60)  # 

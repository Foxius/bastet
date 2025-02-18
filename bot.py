from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging

from database import create_connection, create_tables
from handlers import router
from scheduler import daily_task
from loader import bot 

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(router)

async def on_startup(dp: Dispatcher):
    """
    Функция, выполняемая при запуске бота.

    Эта функция создает соединение с базой данных, 
    создает необходимые таблицы и запускает 
    запланированную задачу.
    
    :param dp: Диспетчер Aiogram.
    """
    conn = create_connection()
    create_tables(conn)
    conn.close()

    asyncio.create_task(daily_task(bot))

async def main():
    """
    Основная функция, запускающая бота.

    Эта функция вызывает функцию on_startup и 
    начинает опрос бота для получения обновлений.
    """
    await on_startup(dp)
    await dp.start_polling(bot) 

if __name__ == '__main__':
    asyncio.run(main())

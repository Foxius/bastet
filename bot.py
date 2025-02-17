from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging

from database import create_connection, create_tables
from handlers import router  # Import the router from handlers
from scheduler import daily_task
from loader import bot  # Ensure this imports a properly configured Bot instance

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize storage and dispatcher
storage = MemoryStorage()
dp = Dispatcher(storage=storage)  # Correct initialization of Dispatcher

# Include the router in the dispatcher
dp.include_router(router)

async def on_startup(dp: Dispatcher):
    # Initialize database
    conn = create_connection()
    create_tables(conn)
    conn.close()

    # Start the daily task
    asyncio.create_task(daily_task(bot))

async def main():
    await on_startup(dp)
    await dp.start_polling(bot)  # Pass the bot instance to start_polling

if __name__ == '__main__':
    asyncio.run(main())
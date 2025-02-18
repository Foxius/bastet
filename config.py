import os
import dotenv
dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHATS = os.getenv("CHATS")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMIN_IDS = os.getenv("ADMIN_IDS")
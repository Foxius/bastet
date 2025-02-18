import os
import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHATS = [int(chat_id) for chat_id in os.getenv("CHATS").strip("[]").split(",")]
DATABASE_NAME = os.getenv("DATABASE_NAME")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS").strip("[]").split(",")]

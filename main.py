import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN, DATABASE_URL
from db import Database
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, AVAILABLE_CARS_COMMAND, DELETE_CAR_COMMAND, RENT_CAR_COMMAND
from handlers.user_handlers import UserHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.startup_handlers import StartupHandlers
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    db = Database(DATABASE_URL)
    await db.connect()

    startupHandlers = StartupHandlers(db, bot)
    dp.message.register(startupHandlers.send_welcome, Command("start"))

    userHandlers = UserHandlers(db, bot)
    dp.message.register(userHandlers.rent_car, lambda msg: RENT_CAR_COMMAND in msg.text)
    dp.message.register(userHandlers.available_cars, lambda msg: AVAILABLE_CARS_COMMAND in msg.text)

    adminHandlers = AdminHandlers(db, bot)
    dp.message.register(adminHandlers.add_car, lambda msg: ADD_CAR_COMMAND in msg.text)
    dp.message.register(adminHandlers.delete_car, lambda msg: DELETE_CAR_COMMAND in msg.text)
    dp.message.register(adminHandlers.view_cars, lambda msg: ALL_CARS_COMMAND in msg.text)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

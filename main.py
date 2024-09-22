import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN, DATABASE_URL
from db import Database
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, ALL_CARS_TEXT, AVAILABLE_CARS_COMMAND, DELETE_CAR_COMMAND, MENU_COMMAND, RENT_CAR_COMMAND, SHOW_FLEET_COMMAND
from handlers.user_handlers import UserHandlers
from handlers.admin_handlers import AddCarStates, AdminHandlers, CarClass, DeleteCarStates
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
    dp.callback_query.register(startupHandlers.menu, lambda c: MENU_COMMAND in c.data)

    # пользовательские функции 
    userHandlers = UserHandlers(db, bot)
    # dp.message.register(userHandlers.rent_car, lambda msg: RENT_CAR_COMMAND in msg.text)
    # dp.callback_query.register(userHandlers.available_cars, lambda c: ALL_CARS_COMMAND in c.data)
    dp.callback_query.register(userHandlers.show_fleet, lambda c: c.data == SHOW_FLEET_COMMAND)
    dp.callback_query.register(userHandlers.show_cars_by_class, lambda c: c.data in ["car_class_econom", "car_class_comfort", "car_class_business"])


    # административные функции 
    admin_handlers = AdminHandlers(db, bot)
    dp.message.register(admin_handlers.start_add_car, lambda msg: ADD_CAR_COMMAND in msg.text)
    dp.message.register(admin_handlers.car_brand_entered, AddCarStates.waiting_for_brand)
    dp.message.register(admin_handlers.car_model_entered, AddCarStates.waiting_for_model)
    dp.callback_query.register(admin_handlers.car_class_entered, lambda c: c.data in [CarClass.ECONOM, CarClass.COMFORT, CarClass.BUSINESS])
    dp.message.register(admin_handlers.car_photos_entered, AddCarStates.waiting_for_photo_urls)

    dp.message.register(admin_handlers.start_delete_car, lambda msg: DELETE_CAR_COMMAND in msg.text)
    dp.message.register(admin_handlers.confirm_delete_car, DeleteCarStates.waiting_for_car_id)

    dp.message.register(admin_handlers.view_cars, lambda msg: ALL_CARS_TEXT in msg.text)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

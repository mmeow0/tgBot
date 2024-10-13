import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN, DATABASE_URL
from aiogram.types import BotCommand
from aiogram_calendar import SimpleCalendarCallback
from db import Database
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, DELETE_CAR_COMMAND, MENU_COMMAND, SHOW_CONTACTS_COMMAND, SHOW_FLEET_COMMAND, SHOW_RENTAL_TERMS_COMMAND
from handlers.user_handlers import SelectDatesStates, UserHandlers
from handlers.admin_handlers import AddCarStates, AdminHandlers, CarClass, CarTransmission, DeleteCarStates
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
    dp.message.register(startupHandlers.send_welcome, Command("menu"))
    dp.message.register(startupHandlers.send_welcome, lambda msg: MENU_COMMAND in msg.text)

    # пользовательские функции 
    userHandlers = UserHandlers(db, bot)
    dp.callback_query.register(userHandlers.show_fleet, lambda c: c.data == SHOW_FLEET_COMMAND)
    dp.callback_query.register(userHandlers.show_cars_by_class, lambda c: c.data in ["car_class_econom", "car_class_comfort", "car_class_business"])
    dp.callback_query.register(userHandlers.page, lambda c: 'page' in c.data )
    dp.callback_query.register(userHandlers.start_date_selection, lambda c: c.data == "select_dates")
    dp.callback_query.register(userHandlers.process_date_selection, SelectDatesStates.waiting_for_start_date, SimpleCalendarCallback.filter())
    dp.callback_query.register(userHandlers.process_end_date_selection, SelectDatesStates.waiting_for_end_date, SimpleCalendarCallback.filter())
    dp.callback_query.register(userHandlers.handle_show_contacts, lambda c: c.data == SHOW_CONTACTS_COMMAND)
    dp.callback_query.register(userHandlers.handle_show_rental_terms, lambda c: c.data == SHOW_RENTAL_TERMS_COMMAND)


    # административные функции 
    admin_handlers = AdminHandlers(db, bot)
    dp.callback_query.register(admin_handlers.start_add_car, lambda c: c.data == ADD_CAR_COMMAND)
    dp.message.register(admin_handlers.car_brand_entered, AddCarStates.waiting_for_brand)
    dp.message.register(admin_handlers.car_model_entered, AddCarStates.waiting_for_model)
    dp.callback_query.register(admin_handlers.car_class_entered, lambda c: c.data in [CarClass.ECONOM, CarClass.COMFORT, CarClass.BUSINESS])
    dp.callback_query.register(admin_handlers.car_transmission_entered, lambda c: c.data in [CarTransmission.AUTO, CarTransmission.MECANIC])
    dp.message.register(admin_handlers.car_year_entered, AddCarStates.waiting_for_year)
    dp.message.register(admin_handlers.car_price_entered, AddCarStates.waiting_for_price)
    dp.message.register(admin_handlers.car_doors_entered, AddCarStates.waiting_for_doors)
    dp.message.register(admin_handlers.car_photos_entered, AddCarStates.waiting_for_photo_urls)
    dp.callback_query.register(admin_handlers.confirm_booking, lambda c: "confirm_booking" in c.data)

    dp.callback_query.register(admin_handlers.start_delete_car, lambda c: c.data == DELETE_CAR_COMMAND)
    dp.message.register(admin_handlers.confirm_delete_car, DeleteCarStates.waiting_for_car_id)

    dp.callback_query.register(admin_handlers.view_cars, lambda c: ALL_CARS_COMMAND in c.data)

    main_menu_commands = [
            BotCommand(command='/menu',
                    description='Меню'),
        ]

    await bot.set_my_commands(main_menu_commands)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

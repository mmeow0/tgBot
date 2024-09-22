from aiogram import types
import logging

from config import ADMIN_ID
from handlers.admin_handlers import CarClass

logger = logging.getLogger(__name__)

class UserHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def show_fleet(self, callback_query: types.CallbackQuery):
        # Создаем кнопки для выбора класса автомобиля
        kb = [
            [
                types.InlineKeyboardButton(text="Эконом", callback_data="car_class_econom"),
                types.InlineKeyboardButton(text="Комфорт", callback_data="car_class_comfort"),
                types.InlineKeyboardButton(text="Бизнес", callback_data="car_class_business"),
            ],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await callback_query.message.answer("Выберите класс автомобиля:", reply_markup=keyboard)


    async def show_cars_by_class(self, callback_query: types.CallbackQuery):
        car_class_map = {
            "car_class_econom": CarClass.ECONOM,
            "car_class_comfort": CarClass.COMFORT,
            "car_class_business": CarClass.BUSINESS,
        }

        selected_class = callback_query.data
        class_name = car_class_map.get(selected_class)

        # Получаем автомобили по классу
        cars = await self.db.get_cars_by_class(class_name)

        if cars:
            car_list = "\n".join([f"{car['brand']} {car['model']} (ID: {car['id']})" for car in cars])
            await callback_query.message.answer(f'Доступные автомобили класса {class_name}:\n{car_list}')
        else:
            await callback_query.message.answer(f"Нет доступных автомобилей класса {class_name}.")

    async def rent_car(self, callback_query: types.CallbackQuery):
        command_parts = callback_query.message.text.split()
        
        if len(command_parts) < 4:
            await callback_query.message.reply("Пожалуйста, введите ID автомобиля и даты (начало и конец) в формате: /rent_car <ID> <начало> <конец>.")
            return
        
        try:
            car_id = int(command_parts[1])
            start_time = command_parts[2]
            end_time = command_parts[3]

            available = await self.db.is_car_available(car_id, start_time, end_time)
            if not available:
                await callback_query.message.reply("Автомобиль недоступен на выбранное время.")
                return

            await self.db.rent_car(car_id, callback_query.message.from_user.id, start_time, end_time)
            await callback_query.message.reply("Аренда успешно оформлена.")
        except ValueError:
            await callback_query.message.reply("ID автомобиля должен быть числом.")
        except Exception as e:
            await callback_query.message.reply(f"Произошла ошибка: {str(e)}")
            logger.error(f"Ошибка при аренде автомобиля: {e}")

    async def available_cars(self, callback_query: types.CallbackQuery):
        cars = await self.db.get_all_cars()
        if cars:
            car_list = "\n".join([f"{car['brand']} {car['model']} (Класс: {car['car_class']})" for car in cars])
            await callback_query.message.reply(f'Доступные автомобили:\n{car_list}')
        else:
            await callback_query.message.reply("Нет доступных автомобилей.")

from aiogram import types
import logging

from config import ADMIN_ID

logger = logging.getLogger(__name__)

class UserHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def rent_car(self, message: types.Message):
        command_parts = message.text.split()
        car_id, start_time, end_time = int(command_parts[1]), command_parts[2], command_parts[3]

        available = await self.db.is_car_available(car_id, start_time, end_time)
        if not available:
            await message.reply("Автомобиль недоступен на выбранное время.")
            return

        await self.db.rent_car(car_id, message.from_user.id, start_time, end_time)
        await message.reply("Аренда успешно оформлена.")

    async def available_cars(self, message: types.Message):
        cars = await self.db.get_available_cars()
        if cars:
            car_list = "\n".join([f"{car['brand']} {car['model']} (Класс: {car['car_class']})" for car in cars])
            await message.reply(f'Доступные автомобили:\n{car_list}')
        else:
            await message.reply("Нет доступных автомобилей.")
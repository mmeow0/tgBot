from aiogram import types
import logging

from config import ADMIN_ID

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def add_car(self, message: types.Message):
        logger.info(f"Пользователь {message.from_user.id} пытается добавить автомобиль")
        if str(message.from_user.id) == ADMIN_ID:
            try:
                command_parts = message.text.split()
                if len(command_parts) < 5:
                    await message.reply("Используйте команду в формате: добавить автомобиль <brand> <model> <class> <photo_urls>")
                    return
                
                brand, model, car_class = command_parts[2], command_parts[3], command_parts[4]
                photo_urls = command_parts[5:]

                await self.db.add_car(brand, model, car_class, photo_urls)
                await message.reply(f'Автомобиль {brand} {model} добавлен в класс {car_class}.')
                logger.info(f"Автомобиль {brand} {model} успешно добавлен.")
            except Exception as e:
                await message.reply(f'Ошибка: {str(e)}')
                logger.error(f"Ошибка при добавлении автомобиля: {e}")
        else:
            await message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")

    async def view_cars(self, message: types.Message):
        if str(message.from_user.id) == ADMIN_ID:
            cars = await self.db.get_all_cars()
            if cars:
                car_list = "\n".join([f"ID: {car['id']}, {car['brand']} {car['model']} (Класс: {car['car_class']})" for car in cars])
                await message.reply(f'Все автомобили:\n{car_list}')
            else:
                await message.reply("Нет добавленных автомобилей.")
        else:
            await message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")
        
    async def rent_car(self, message: types.Message):
        command_parts = message.text.split()
        car_id, start_time, end_time = int(command_parts[1]), command_parts[2], command_parts[3]

        available = await self.db.is_car_available(car_id, start_time, end_time)
        if not available:
            await message.reply("Автомобиль недоступен на выбранное время.")
            return

        await self.db.rent_car(car_id, message.from_user.id, start_time, end_time)
        await message.reply("Аренда успешно оформлена.")
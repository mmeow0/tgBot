from aiogram import types
import logging

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
                types.InlineKeyboardButton(text="Комфорт +", callback_data="car_class_business"),
            ],
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await callback_query.message.answer("🚗 Выберите класс автомобиля:", reply_markup=keyboard)


    def construct_keyboard(self, length: int, page: int, selected_class: str) -> types.InlineKeyboardMarkup:
            kb={'inline_keyboard': []}
            buttons=[]
            if page > 1:
                buttons.append({'text':'<-', 'callback_data':f'page:{page-1}:{selected_class}'})
            #adding a neat page number
            buttons.append({'text':f'{page}/{length}', 'callback_data':'none'})
            if page < length: #preventing going out of range
                buttons.append({'text':'->', 'callback_data':f'page:{page+1}:{selected_class}'}) 
            kb['inline_keyboard'].append(buttons)
            return kb

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
        if len(cars) > 0:
            car=cars[0]
            await callback_query.message.answer_photo(
                photo=car['photos'][0],
                caption=f"{car['brand']} {car['model']} {car['year']} от {car['price']}р./день",
                reply_markup=self.construct_keyboard(len(cars),1, selected_class)
            )
        else:
            await callback_query.message.answer(f"Нет доступных автомобилей класса {class_name}.")

    async def page(self, callback_query: types.CallbackQuery):
        page=int(callback_query.data.split(':')[1])
        selected_class=callback_query.data.split(':')[2]
        
        car_class_map = {
            "car_class_econom": CarClass.ECONOM,
            "car_class_comfort": CarClass.COMFORT,
            "car_class_business": CarClass.BUSINESS,
        }

        class_name = car_class_map.get(selected_class)
        # Получаем автомобили по классу
        cars = await self.db.get_cars_by_class(class_name)
        car = cars[page-1]
        file = types.InputMediaPhoto(media=car['photos'][0], caption=f"{car['brand']} {car['model']} {car['year']} от {car['price']}р./день")
        await callback_query.message.edit_media(
                file,
                reply_markup=self.construct_keyboard(len(cars), page, selected_class)
            )

                         
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

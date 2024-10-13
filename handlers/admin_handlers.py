from datetime import datetime
from aiogram import types
import logging
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID

logger = logging.getLogger(__name__)

class DeleteCarStates(StatesGroup):
    waiting_for_car_id = State()

class AddCarStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_class = State()
    waiting_for_transmission = State()
    waiting_for_year = State()
    waiting_for_price = State()
    waiting_for_doors = State()
    waiting_for_photo_urls = State()

class CarClass:
    ECONOM = 'эконом'
    COMFORT = 'комфорт'
    BUSINESS = 'комфорт +'

class CarTransmission:
    MECANIC = 'механическая'
    AUTO = 'автомат'

class AdminHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def start_add_car(self, callback_query: types.CallbackQuery, state: FSMContext):
        logger.info(f"Пользователь {callback_query.message.from_user.id} пытается добавить автомобиль")
        if str(callback_query.from_user.id) == ADMIN_ID:
            await callback_query.message.reply("Введите марку автомобиля:")
            await state.set_state(AddCarStates.waiting_for_brand)
        else:
            await callback_query.message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {callback_query.message.from_user.id} попытался выполнить команду без прав администратора.")

    async def car_brand_entered(self, message: types.Message, state: FSMContext):
        await state.update_data(brand=message.text)
        await message.reply("Введите модель автомобиля:")
        await state.set_state(AddCarStates.waiting_for_model)

    async def car_model_entered(self, message: types.Message, state: FSMContext):
        await state.update_data(model=message.text)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Эконом", callback_data=CarClass.ECONOM),
                types.InlineKeyboardButton(text="Комфорт", callback_data=CarClass.COMFORT),
                types.InlineKeyboardButton(text="Комфорт +", callback_data=CarClass.BUSINESS),
            ]
        ])
        await message.reply("Выберите класс автомобиля:", reply_markup=keyboard)
        await state.set_state(AddCarStates.waiting_for_class)

    async def car_class_entered(self, callback_query: types.CallbackQuery, state: FSMContext):
        car_class = callback_query.data
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="автомат", callback_data=CarTransmission.AUTO),
                types.InlineKeyboardButton(text="механическая", callback_data=CarTransmission.MECANIC),
            ]
        ])
        await state.update_data(car_class=car_class)
        await callback_query.message.reply("Выберете тип коробки передач:", reply_markup=keyboard)
        await state.set_state(AddCarStates.waiting_for_transmission)

    async def car_transmission_entered(self, callback_query: types.CallbackQuery, state: FSMContext):
        await state.update_data(transmission=callback_query.data)
        await callback_query.message.reply("Введите год выпуска автомобиля:")
        await state.set_state(AddCarStates.waiting_for_year)

    async def car_year_entered(self, message: types.Message, state: FSMContext):
        car_year = message.text
        await state.update_data(year=car_year)
        await message.reply("Введите начальную цену р./день:")
        await state.set_state(AddCarStates.waiting_for_price)

    async def car_price_entered(self, message: types.Message, state: FSMContext):
        car_price = message.text
        await state.update_data(price=car_price)
        await message.reply("Введите количество дверей у автомобиля:")
        await state.set_state(AddCarStates.waiting_for_doors)

    async def car_doors_entered(self, message: types.Message, state: FSMContext):
        car_doors = message.text
        await state.update_data(doors=car_doors)
        await message.reply("Введите URL фотографии автомобиля:")
        await state.set_state(AddCarStates.waiting_for_photo_urls)

    async def car_photos_entered(self, message: types.Message, state: FSMContext):
        photo_urls = message.text.split()
        data = await state.get_data()
        print(data)

        brand = data['brand']
        model = data['model']
        car_class = data['car_class']
        transmission = data['transmission']
        year = int(data['year'])
        price = int(data['price'])
        doors = int(data['doors'])

        # Добавляем автомобиль в базу данных
        try:
            await self.db.add_car(brand, model, car_class, transmission, year, price, doors, photo_urls)
            await message.reply(f'Автомобиль {brand} {model} добавлен в класс {car_class}.')
            logger.info(f"Автомобиль {brand} {model} успешно добавлен.")
        except Exception as e:
            await message.reply(f'Ошибка: {str(e)}')
            logger.error(f"Ошибка при добавлении автомобиля: {e}")
        
        # Сбрасываем состояние
        await state.clear()

    async def start_delete_car(self, callback_query: types.CallbackQuery, state: FSMContext):
        if str(callback_query.from_user.id) == ADMIN_ID:
            await callback_query.message.reply("Введите ID автомобиля для удаления:")
            await state.set_state(DeleteCarStates.waiting_for_car_id)
        else:
            await callback_query.message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {callback_query.message.from_user.id} попытался выполнить команду без прав администратора.")

    async def confirm_delete_car(self, message: types.Message, state: FSMContext):
        if str(message.from_user.id) == ADMIN_ID:
            try:
                car_id = int(message.text)
                logger.info(f"Пользователь {message.from_user.id} запрашивает удаление автомобиля с ID {car_id}")

                existing_car = await self.db.get_car_by_id(car_id)
                if not existing_car:
                    await message.reply(f"Автомобиль с ID {car_id} не найден.")
                    logger.warning(f"Попытка удалить несуществующий автомобиль с ID {car_id}.")
                    await state.clear()
                    return

                success = await self.db.delete_car(car_id)

                if success:
                    await message.reply(f"Автомобиль с ID {car_id} был успешно удалён.")
                    logger.info(f"Автомобиль с ID {car_id} был успешно удалён.")
                else:
                    await message.reply(f"Не удалось удалить автомобиль с ID {car_id}.")
                    logger.warning(f"Ошибка при удалении автомобиля с ID {car_id}.")
            except ValueError:
                await message.reply("ID автомобиля должен быть числом.")
                logger.error("Некорректный ID автомобиля.")
            except Exception as e:
                await message.reply(f'Ошибка: {str(e)}')
                logger.error(f"Ошибка при удалении автомобиля: {e}")
            finally:
                await state.clear()
        else:
            await message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")

    async def view_cars(self, callback_query: types.CallbackQuery):
        if str(callback_query.from_user.id) == ADMIN_ID:
            cars = await self.db.get_all_cars()
            if cars:
                car_list = "\n".join([f"ID: {car['id']}, {car['brand']} {car['model']} {car['year']} от {car['price']}р./день (Класс: {car['car_class']})" for car in cars])
                await callback_query.message.reply(f'Все автомобили:\n{car_list}')
            else:
                await callback_query.message.reply("Нет добавленных автомобилей.")
        else:
            await callback_query.message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {callback_query.message.from_user.id} попытался выполнить команду без прав администратора.")
    
    async def confirm_booking(self, callback_query: types.CallbackQuery):
        if str(callback_query.from_user.id) == ADMIN_ID:
            _, user_id, car_id, start_date, end_date = callback_query.data.split(":")

            start_date = datetime.strptime(start_date, '%d.%m.%Y')
            end_date = datetime.strptime(end_date, '%d.%m.%Y')

            user_id = int(user_id) 
            car_id = int(car_id)

            is_available = await self.db.is_car_available(car_id, start_date, end_date)
            
            if is_available:
                await self.db.rent_car(car_id, user_id, start_date, end_date)

                await callback_query.answer("Бронирование подтверждено!")

                await self.bot.send_message(
                    user_id,
                    f"Ваше бронирование автомобиля с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')} подтверждено!"
                )
            else:
                await callback_query.answer("Извините, автомобиль недоступен в эти даты.")
            
            await callback_query.message.delete()
        else:
            await callback_query.message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {callback_query.message.from_user.id} попытался выполнить команду без прав администратора.")

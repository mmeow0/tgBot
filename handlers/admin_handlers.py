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
    waiting_for_photo_urls = State()

class AdminHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def start_add_car(self, message: types.Message, state: FSMContext):
        logger.info(f"Пользователь {message.from_user.id} пытается добавить автомобиль")
        if str(message.from_user.id) == ADMIN_ID:
            await message.reply("Введите марку автомобиля:")
            await state.set_state(AddCarStates.waiting_for_brand)
        else:
            await message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")

    # Получение марки автомобиля и запрос модели
    async def car_brand_entered(self, message: types.Message, state: FSMContext):
        await state.update_data(brand=message.text)
        await message.reply("Введите модель автомобиля:")
        await state.set_state(AddCarStates.waiting_for_model)

    # Получение модели автомобиля и запрос класса
    async def car_model_entered(self, message: types.Message, state: FSMContext):
        await state.update_data(model=message.text)
        await message.reply("Введите класс автомобиля:")
        await state.set_state(AddCarStates.waiting_for_class)

    async def car_class_entered(self, message: types.Message, state: FSMContext):
        await state.update_data(car_class=message.text)
        await message.reply("Введите URL фотографий автомобиля через пробел:")
        await state.set_state(AddCarStates.waiting_for_photo_urls)

    # Получение фото и завершение добавления автомобиля
    async def car_photos_entered(self, message: types.Message, state: FSMContext):
        photo_urls = message.text.split()
        data = await state.get_data()

        brand = data['brand']
        model = data['model']
        car_class = data['car_class']

        # Добавляем автомобиль в базу данных
        try:
            await self.db.add_car(brand, model, car_class, photo_urls)
            await message.reply(f'Автомобиль {brand} {model} добавлен в класс {car_class}.')
            logger.info(f"Автомобиль {brand} {model} успешно добавлен.")
        except Exception as e:
            await message.reply(f'Ошибка: {str(e)}')
            logger.error(f"Ошибка при добавлении автомобиля: {e}")
        
        # Сбрасываем состояние
        await state.clear()


    async def start_delete_car(self, message: types.Message, state: FSMContext):
        if str(message.from_user.id) == ADMIN_ID:
            await message.reply("Введите ID автомобиля для удаления:")
            await state.set_state(DeleteCarStates.waiting_for_car_id)
        else:
            await message.reply("У вас нет прав на выполнение этой команды.")
            logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")


    async def confirm_delete_car(self, message: types.Message, state: FSMContext):
        if str(message.from_user.id) == ADMIN_ID:
            try:
                car_id = int(message.text)
                logger.info(f"Пользователь {message.from_user.id} запрашивает удаление автомобиля с ID {car_id}")

                # Проверяем, существует ли автомобиль перед удалением
                existing_car = await self.db.get_car_by_id(car_id)
                if not existing_car:
                    await message.reply(f"Автомобиль с ID {car_id} не найден.")
                    logger.warning(f"Попытка удалить несуществующий автомобиль с ID {car_id}.")
                    await state.clear()
                    return

                # Удаляем автомобиль
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
                await state.clear()  # Очистка состояния после завершения
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
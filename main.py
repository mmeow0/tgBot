import logging
import asyncpg
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_ID, DATABASE_URL
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Подключение к базе данных
async def create_db_pool():
    try:
        return await asyncpg.create_pool(DATABASE_URL)
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise e

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db_pool = None

# Команда для добавления автомобиля
@dp.message(F.text.lower() == "добавить автомобиль")
async def add_car(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} пытается добавить автомобиль")
    if str(message.from_user.id) == ADMIN_ID:
        try:
            command_parts = message.text.split()
            if len(command_parts) < 4:
                await message.reply("Используйте команду в формате: /add_car <brand> <model> <class> <photo_urls>")
                return
            
            brand, model, car_class = command_parts[1], command_parts[2], command_parts[3]
            photo_urls = command_parts[4:]

            async with db_pool.acquire() as connection:
                await connection.execute(
                    'INSERT INTO cars (brand, model, car_class, photos) VALUES ($1, $2, $3, $4)',
                    brand, model, car_class, photo_urls
                )
            await message.reply(f'Автомобиль {brand} {model} добавлен в класс {car_class}.')
            logger.info(f"Автомобиль {brand} {model} успешно добавлен.")
        except Exception as e:
            await message.reply(f'Ошибка: {str(e)}')
            logger.error(f"Ошибка при добавлении автомобиля: {e}")
    else:
        await message.reply("У вас нет прав на выполнение этой команды.")
        logger.warning(f"Пользователь {message.from_user.id} попытался выполнить команду без прав администратора.")

# Команда для аренды автомобиля
async def is_car_available(car_id, start_time, end_time):
    try:
        async with db_pool.acquire() as connection:
            conflicts = await connection.fetch(
                'SELECT * FROM rentals WHERE car_id = $1 AND status = $2 AND (start_time, end_time) OVERLAPS ($3, $4)',
                car_id, 'active', start_time, end_time)
            return len(conflicts) == 0
    except Exception as e:
        logger.error(f"Ошибка проверки доступности автомобиля: {e}")
        raise e

@dp.message(Command('rent_car'))
async def rent_car(message: types.Message):
    try:
        logger.info(f"Пользователь {message.from_user.id} пытается арендовать автомобиль")
        command_parts = message.text.split()
        if len(command_parts) < 4:
            await message.reply("Используйте команду в формате: /rent_car <car_id> <start_time> <end_time>")
            return
        
        car_id = int(command_parts[1])
        start_time = command_parts[2]
        end_time = command_parts[3]

        available = await is_car_available(car_id, start_time, end_time)
        if not available:
            await message.reply("Автомобиль недоступен на выбранное время.")
            logger.info(f"Автомобиль {car_id} недоступен для аренды на указанное время.")
            return

        async with db_pool.acquire() as connection:
            await connection.execute(
                'INSERT INTO rentals (car_id, user_id, start_time, end_time) VALUES ($1, $2, $3, $4)',
                car_id, message.from_user.id, start_time, end_time
            )
        await message.reply("Аренда успешно оформлена.")
        logger.info(f"Пользователь {message.from_user.id} успешно арендовал автомобиль {car_id}.")
    except Exception as e:
        await message.reply(f'Ошибка: {str(e)}')
        logger.error(f"Ошибка при аренде автомобиля: {e}")

# Команда для просмотра доступных автомобилей
@dp.message(F.text.lower() == "доступные автомобили")
async def available_cars(message: types.Message):
    try:
        logger.info(f"Пользователь {message.from_user.id} запрашивает доступные автомобили")
        async with db_pool.acquire() as connection:
            cars = await connection.fetch('SELECT * FROM cars WHERE status = $1', 'available')
            if cars:
                car_list = ""
                for car in cars:
                    car_list += f"{car['brand']} {car['model']} (Класс: {car['car_class']})\n"
                    car_list += f"Фотографии: {', '.join(car['photos'])}\n\n"
                await message.reply(f'Доступные автомобили:\n{car_list}')
            else:
                await message.reply("Нет доступных автомобилей.")
                logger.info("Нет доступных автомобилей.")
    except Exception as e:
        await message.reply(f'Ошибка: {str(e)}')
        logger.error(f"Ошибка при запросе доступных автомобилей: {e}")

# Команда для просмотра доступных автомобилей
@dp.message(F.text.lower() == "все автомобили")
async def view_cars(message: types.Message):
    try:
        async with db_pool.acquire() as connection:
            cars = await connection.fetch('SELECT * FROM cars')
            if cars:
                car_list = ""
                for car in cars:
                    car_list += f"ID: {car['id']}, {car['brand']} {car['model']} (Класс: {car['car_class']})\n"
                await message.reply(f'Все автомобили:\n{car_list}')
            else:
                await message.reply("Нет добавленных автомобилей.")
    except Exception as e:
        await message.reply(f'Ошибка: {str(e)}')

async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) == ADMIN_ID:
        kb = [
            [
                types.KeyboardButton(text="Все автомобили"),
                types.KeyboardButton(text="Добавить автомобиль")
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите команду"
        )
        await message.answer("Добро пожаловать, администратор!", reply_markup=keyboard)
    else:
        kb = [
            [
                types.KeyboardButton(text="Арендовать автомобиль"),
                types.KeyboardButton(text="Доступные автомобили")
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите команду"
        )
        await message.answer("Добро пожаловать, пользователь!", reply_markup=keyboard)

dp.message.register(send_welcome, Command("start"))

# Основная функция для запуска бота
async def main():
    global db_pool
    try:
        db_pool = await create_db_pool()
        logger.info("Подключение к базе данных успешно установлено")
        
        # Запуск поллинга
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Ошибка при запуске бота: {e}")
        exit(1)

if __name__ == '__main__':
    logger.info("Запуск бота")
    asyncio.run(main())

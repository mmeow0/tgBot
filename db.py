import asyncpg
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url):
        self.db_url = db_url
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise e

    async def add_car(self, brand, model, car_class, photo_urls):
        async with self.pool.acquire() as connection:
            await connection.execute(
                'INSERT INTO cars (brand, model, car_class, photos) VALUES ($1, $2, $3, $4)',
                brand, model, car_class, photo_urls
            )

    async def delete_car(self, car_id):
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                'DELETE FROM cars WHERE id = $1', car_id
            )
            # Проверяем, был ли удален автомобиль
            return result == 'DELETE 1'  # Возвращает True, если автомобиль был удален
    
    async def get_car_by_id(self, car_id):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow('SELECT * FROM cars WHERE id = $1', car_id)

    async def is_car_available(self, car_id, start_time, end_time):
        async with self.pool.acquire() as connection:
            conflicts = await connection.fetch(
                'SELECT * FROM rentals WHERE car_id = $1 AND status = $2 AND (start_time, end_time) OVERLAPS ($3, $4)',
                car_id, 'active', start_time, end_time
            )
            return len(conflicts) == 0

    async def rent_car(self, car_id, user_id, start_time, end_time):
        async with self.pool.acquire() as connection:
            await connection.execute(
                'INSERT INTO rentals (car_id, user_id, start_time, end_time) VALUES ($1, $2, $3, $4)',
                car_id, user_id, start_time, end_time
            )

    async def get_available_cars(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch('SELECT * FROM cars WHERE status = $1', 'available')

    async def get_all_cars(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch('SELECT * FROM cars')

    async def get_cars_by_class(self, car_class):
        async with self.pool.acquire() as connection:
            query = "SELECT * FROM cars WHERE car_class = $1"
            return await connection.fetch(query, car_class)
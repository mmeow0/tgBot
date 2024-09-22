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

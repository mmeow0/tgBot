from aiogram import types
import logging

from config import ADMIN_ID
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, DELETE_CAR_COMMAND, RENT_CAR_COMMAND, SHOW_FLEET_COMMAND, WELCOME_ADMIN, WELCOME_USER

logger = logging.getLogger(__name__)

class StartupHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def send_welcome(self, message: types.Message):
        user_id = message.from_user.id
        if str(user_id) == ADMIN_ID:
            kb = [
                    [types.InlineKeyboardButton(text="🚗 Список автомобилей", callback_data=ALL_CARS_COMMAND)],
                    [types.InlineKeyboardButton(text="➕ Добавить автомобиль", callback_data=ADD_CAR_COMMAND)],
                    [types.InlineKeyboardButton(text="➖ Удалить автомобиль", callback_data=DELETE_CAR_COMMAND)]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await message.answer(WELCOME_ADMIN, reply_markup=keyboard)
        else:
            kb = [
                [types.InlineKeyboardButton(text="🚗 Автопарк", callback_data=SHOW_FLEET_COMMAND)],
                [types.InlineKeyboardButton(text="📝 Условия аренды", callback_data=SHOW_FLEET_COMMAND)],
                [types.InlineKeyboardButton(text="📞 Наши контакты", callback_data=SHOW_FLEET_COMMAND)],
                [types.InlineKeyboardButton(text="🙋‍♂️ Написать менеджеру", callback_data=SHOW_FLEET_COMMAND)],
                [types.InlineKeyboardButton(text=RENT_CAR_COMMAND, callback_data='rent_car')]
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await message.answer_photo(
                    photo='https://static.tildacdn.com/tild3038-6531-4936-a434-316262633261/2111.png', 
                    caption=WELCOME_USER, 
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
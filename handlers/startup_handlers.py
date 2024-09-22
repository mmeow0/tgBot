from aiogram import types
import logging

from config import ADMIN_ID
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, AVAILABLE_CARS_COMMAND, DELETE_CAR_COMMAND, RENT_CAR_COMMAND, WELCOME_ADMIN, WELCOME_USER

logger = logging.getLogger(__name__)

class StartupHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def send_welcome(self, message: types.Message):
        user_id = message.from_user.id
        if str(user_id) == ADMIN_ID:
            kb = [
                [
                    types.KeyboardButton(text=ALL_CARS_COMMAND),
                    types.KeyboardButton(text=ADD_CAR_COMMAND),
                    types.KeyboardButton(text=DELETE_CAR_COMMAND)
                ],
            ]
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
                input_field_placeholder="Выберите команду"
            )
            await message.answer(WELCOME_ADMIN, reply_markup=keyboard)
        else:
            kb = [
                [
                    types.KeyboardButton(text=RENT_CAR_COMMAND),
                    types.KeyboardButton(text=AVAILABLE_CARS_COMMAND)
                ],
            ]
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
                input_field_placeholder="Выберите команду"
            )
            await message.answer(WELCOME_USER, reply_markup=keyboard)

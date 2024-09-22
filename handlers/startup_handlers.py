from aiogram import types
import logging

from config import ADMIN_ID
from handlers.messages import ADD_CAR_COMMAND, ALL_CARS_COMMAND, ALL_CARS_TEXT, AVAILABLE_CARS_COMMAND, CARS_PARK, DELETE_CAR_COMMAND, MENU_COMMAND, MENU_USER, RENT_CAR_COMMAND, SHOW_FLEET_COMMAND, WELCOME_ADMIN, WELCOME_USER

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
                    types.InlineKeyboardButton(text="Меню", callback_data=MENU_COMMAND)
                ],
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await message.answer(WELCOME_ADMIN, reply_markup=keyboard)
        else:
            kb = [
                [
                    types.InlineKeyboardButton(text="Меню", callback_data=MENU_COMMAND)
                ],
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await message.answer(WELCOME_USER, reply_markup=keyboard)

    async def menu(self, callback_query: types.CallbackQuery):
        user_id = callback_query.message.from_user.id
        if str(user_id) == ADMIN_ID:
            kb = [
                [
                    types.InlineKeyboardButton(text=ALL_CARS_TEXT, callback_data='all_cars'),
                    types.InlineKeyboardButton(text=ADD_CAR_COMMAND, callback_data='add_car'),
                    types.InlineKeyboardButton(text=DELETE_CAR_COMMAND, callback_data='delete_car')
                ],
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await callback_query.message.answer(MENU_USER, reply_markup=keyboard)
        else:
            kb = [
                [
                    types.InlineKeyboardButton(text=RENT_CAR_COMMAND, callback_data='rent_car'),
                    types.InlineKeyboardButton(text=CARS_PARK, callback_data=SHOW_FLEET_COMMAND)
                ],
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await callback_query.message.answer(MENU_USER, reply_markup=keyboard)
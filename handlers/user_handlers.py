from aiogram import types
from aiogram_calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback
from aiogram.filters.callback_data import CallbackData
import logging
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from handlers.admin_handlers import CarClass

logger = logging.getLogger(__name__)
ADMIN_CHAT_ID = 00000  # ID администратора, сюда отправляются уведомления

class SelectDatesStates(StatesGroup):
    waiting_car_id = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()

class UserHandlers:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def show_fleet(self, callback_query: types.CallbackQuery):
        # Кнопки для выбора класса автомобиля
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
        kb = {'inline_keyboard': []}
        buttons = []

        if page > 1:
            buttons.append({'text': '<-', 'callback_data': f'page:{page-1}:{selected_class}'})

        buttons.append({'text': f'{page}/{length}', 'callback_data': 'none'})

        if page < length:
            buttons.append({'text': '->', 'callback_data': f'page:{page+1}:{selected_class}'})

        kb['inline_keyboard'].append(buttons)
        kb['inline_keyboard'].append([{'text': 'Назад к выбору класса', 'callback_data': 'show_fleet'}])
        kb['inline_keyboard'].append([{'text': 'Выбрать даты', 'callback_data': 'select_dates'}])  # Кнопка для выбора дат

        return kb

    async def show_cars_by_class(self, callback_query: types.CallbackQuery, state: FSMContext):
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
            car = cars[0]
            await callback_query.message.answer_photo(
                photo=car['photos'][0],
                caption=f"{car['brand']} {car['model']} {car['year']} от {car['price']}р./день",
                reply_markup=self.construct_keyboard(len(cars), 1, selected_class)
            )
            await state.update_data(car_id=car['id'])
        else:
            await callback_query.message.answer(f"Нет доступных автомобилей класса {class_name}.")

    async def page(self, callback_query: types.CallbackQuery, state: FSMContext):
        page = int(callback_query.data.split(':')[1])
        selected_class = callback_query.data.split(':')[2]
        
        car_class_map = {
            "car_class_econom": CarClass.ECONOM,
            "car_class_comfort": CarClass.COMFORT,
            "car_class_business": CarClass.BUSINESS,
        }

        class_name = car_class_map.get(selected_class)
        # Получаем автомобили по классу
        cars = await self.db.get_cars_by_class(class_name)
        car = cars[page - 1]
        file = types.InputMediaPhoto(media=car['photos'][0], caption=f"{car['brand']} {car['model']} {car['year']} от {car['price']}р./день")
        await state.update_data(car_id=car['id'])
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

    async def start_date_selection(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Запуск выбора даты начала аренды с помощью календаря"""
        reply_markup=await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).start_calendar()
        await callback_query.message.answer("Выберите дату начала аренды:", reply_markup=reply_markup)
        
        # Установка состояния ожидания даты начала
        await state.set_state(SelectDatesStates.waiting_for_start_date)

    async def nav_cal_handler_date(self, message: types.Message):
        calendar = SimpleCalendar(
            locale=await get_user_locale(message.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        await message.answer(
            "Calendar opened on feb 2023. Please select a date: ",
            reply_markup=await calendar.start_calendar(year=2023, month=2)
        )

    async def process_date_selection(self, callback_query: types.CallbackQuery, state: FSMContext, callback_data: CallbackData):
        """Обработка выбора даты начала аренды с помощью календаря"""
        # Извлечение данных из callback_data
        calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        selected, date = await calendar.process_selection(callback_query, callback_data)
        if selected:
               # Сохраняем выбранную дату начала аренды в состояние
            await state.update_data(start_date=date)
            reply_markup = await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).start_calendar()
            await callback_query.message.answer(f"Дата начала аренды: {date.strftime('%Y-%m-%d')}. Теперь выберете дату окончания аренды", reply_markup=reply_markup)

            # Установка состояния ожидания даты окончания
            await state.set_state(SelectDatesStates.waiting_for_end_date)

    async def process_end_date_selection(self, callback_query: types.CallbackQuery, state: FSMContext, callback_data: CallbackData):
        """Обработка выбора даты окончания аренды с помощью календаря"""
        # Извлечение данных из callback_data
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback_query.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
        selected, end_date = await calendar.process_selection(callback_query, callback_data)

        if selected:
            # Получаем дату начала и информацию об автомобиле из состояния
            user_data = await state.get_data()
            start_date = user_data.get("start_date")
            car_id = user_data.get("car_id")  # Получаем ID автомобиля из состояния

            if start_date and car_id:
                # Получаем информацию об автомобиле из базы данных
                car_info = await self.db.get_car_by_id(car_id)  # Метод получения автомобиля по ID
                if car_info:
                    car_details = f"{car_info['brand']} {car_info['model']} ({car_info['car_class']})"
                else:
                    car_details = "Неизвестный автомобиль"

                await callback_query.message.answer(f"Вы выбрали дату окончания аренды: {end_date.strftime('%Y-%m-%d')}")
                
                # Сообщаем пользователю, что запрос на аренду отправлен
                await callback_query.message.answer("Ваш запрос на аренду отправлен администратору. Ожидайте подтверждения.")

                kb = [
                        [
                            types.InlineKeyboardButton(text="Подтвердить бронирование", callback_data=f"confirm_booking:{callback_query.from_user.id}:{car_id}:{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}")
                        ],
                    ]
                confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

                # Отправка информации администратору
                await self.bot.send_message(
                    ADMIN_CHAT_ID,
                    f"Пользователь {callback_query.from_user.full_name} (ID: {callback_query.from_user.id}, Никнейм: @{callback_query.from_user.username}) "
                    f"сделал запрос на аренду автомобиля {car_details} (ID: {car_id}) с {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}.\n"
                    f"Свяжитесь с ним для подтверждения бронирования.", reply_markup=confirm_keyboard
                )
            else:
                await callback_query.message.answer("Ошибка: не удалось получить дату начала аренды или информацию об автомобиле.")


    async def available_cars(self, callback_query: types.CallbackQuery):
        cars = await self.db.get_all_cars()
        if cars:
            car_list = "\n".join([f"{car['brand']} {car['model']} (Класс: {car['car_class']})" for car in cars])
            await callback_query.message.reply(f'Доступные автомобили:\n{car_list}')
        else:
            await callback_query.message.reply("Нет доступных автомобилей.")

from aiogram import types
from aiogram_calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback
from aiogram.filters.callback_data import CallbackData
import logging
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from config import ADMIN_ID
from handlers.admin_handlers import CarClass
from handlers.messages import SHOW_FLEET_COMMAND

logger = logging.getLogger(__name__)

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
        kb['inline_keyboard'].append([{'text': 'Назад к выбору класса', 'callback_data': SHOW_FLEET_COMMAND}])
        kb['inline_keyboard'].append([{'text': 'Выбрать даты', 'callback_data': 'select_dates'}])
        return kb

    async def show_cars_by_class(self, callback_query: types.CallbackQuery, state: FSMContext):
        car_class_map = {
            "car_class_econom": CarClass.ECONOM,
            "car_class_comfort": CarClass.COMFORT,
            "car_class_business": CarClass.BUSINESS,
        }

        selected_class = callback_query.data
        class_name = car_class_map.get(selected_class)

        cars = await self.db.get_cars_by_class(class_name)
        if len(cars) > 0:
            car = cars[0]
            await callback_query.message.answer_photo(
                photo=car['photos'][0],
                caption=f"{car['brand']} {car['model']} {car['year']} от {car['price']}р./день",
                reply_markup=self.construct_keyboard(len(cars), 1, selected_class)
            )
            await state.update_data(car_id=car['id'])
            await callback_query.message.delete()
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

    async def start_date_selection(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Запуск выбора даты начала аренды с помощью календаря"""
        calendar = SimpleCalendar(locale=await get_user_locale(callback_query.from_user))
        calendar.set_dates_range(datetime.today(), (datetime.today() + relativedelta(months=6)))
        await callback_query.message.answer("Выберите дату начала аренды:", reply_markup=await calendar.start_calendar())
        
        # Установка состояния ожидания даты начала
        await state.set_state(SelectDatesStates.waiting_for_start_date)

    async def nav_cal_handler_date(self, message: types.Message):
        calendar = SimpleCalendar(
            locale=await get_user_locale(message.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime.today(), (datetime.today() + relativedelta(months=6)))
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
        calendar.set_dates_range(datetime.today(), (datetime.today() + relativedelta(months=6)))
        selected, date = await calendar.process_selection(callback_query, callback_data)
        if selected:
               # Сохраняем выбранную дату начала аренды в состояние
            await state.update_data(start_date=date)
            reply_markup = await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).start_calendar()
            await callback_query.message.edit_text(f"Дата начала аренды: {date.strftime('%d.%m.%Y')}. Теперь выберете дату окончания аренды", reply_markup=reply_markup)

            # Установка состояния ожидания даты окончания
            await state.set_state(SelectDatesStates.waiting_for_end_date)

    async def get_available_dates(self, car_id: int):
        # Получаем занятые даты
        busy_periods = await self.get_busy_dates(car_id)

        # Определяем доступные даты (например, на ближайшие 30 дней)
        today = datetime.today().date()
        available_dates = []
        
        for i in range(30):  # проверка на ближайшие 30 дней
            check_date = today + timedelta(days=i)
            is_available = True
            
            # Проверяем, есть ли занятые периоды, перекрывающиеся с текущей датой
            for start, end in busy_periods:
                if start <= check_date <= end:
                    is_available = False
                    break
            
            if is_available:
                available_dates.append(check_date.strftime('%d.%m.%Y'))

        return available_dates
    
    async def process_end_date_selection(self, callback_query: types.CallbackQuery, state: FSMContext, callback_data: CallbackData):
        """Обработка выбора даты окончания аренды с помощью календаря"""
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback_query.from_user), show_alerts=True
        )
        selected, end_date = await calendar.process_selection(callback_query, callback_data)

        if selected:
            user_data = await state.get_data()
            start_date = user_data.get("start_date")
            car_id = user_data.get("car_id")  # Получаем ID автомобиля из состояния

            if start_date and car_id:
                # Проверяем доступность автомобиля
                available = await self.db.is_car_available(car_id, start_date, end_date)
                if not available:
                    # Получаем все занятые даты для данного автомобиля
                    busy_periods = await self.db.get_busy_dates(car_id)
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="Выбрать другой период", callback_data="select_dates")],
                        [types.InlineKeyboardButton(text="Написать менеджеру", url=f"tg://user?id={ADMIN_ID}")]
                    ])
                    # Формируем сообщение о занятости автомобиля
                    busy_periods_str = "\n".join(f"{start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}" for start, end in busy_periods)
                    await callback_query.message.edit_text(f"Невозможно арендовать автомобиль с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}. "
                                                        f"Автомобиль занят на эти даты: \n{busy_periods_str}.", reply_markup=keyboard)
                    return
                
                # Получаем информацию об автомобиле из базы данных
                car_info = await self.db.get_car_by_id(car_id)
                if car_info:
                    car_details = f"{car_info['brand']} {car_info['model']} ({car_info['car_class']})"
                else:
                    car_details = "Неизвестный автомобиль"

                await callback_query.message.edit_text(f"Выбранный период аренды: {start_date.strftime('%d.%m.%Y')}-{end_date.strftime('%d.%m.%Y')} для {car_details}.\nВаш запрос на аренду отправлен администратору. Ожидайте подтверждения.")

                kb = [
                    [
                        types.InlineKeyboardButton(text="Подтвердить бронирование", callback_data=f"confirm_booking:{callback_query.from_user.id}:{car_id}:{start_date.strftime('%d.%m.%Y')}:{end_date.strftime('%d.%m.%Y')}")
                    ],
                ]
                confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

                # Отправка информации администратору
                await self.bot.send_message(
                    ADMIN_ID,
                    f"Пользователь {callback_query.from_user.full_name} (ID: {callback_query.from_user.id}, Никнейм: @{callback_query.from_user.username}) "
                    f"сделал запрос на аренду автомобиля {car_details} (ID: {car_id}) с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}.\n"
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

    async def handle_show_rental_terms(self, callback_query: types.CallbackQuery):
        rental_terms = (
                "🏢 **Условия работы:**\n"
                "1. Вам **23-55 лет**\n"
                "2. У вас гражданство: **РФ, Беларусь, Киргизия**\n"
                "3. У вас есть права **категории В**\n"
                "4. Вы — **вежливый и аккуратный**\n"
                "5. Ваш опыт вождения — **не менее 5 лет**\n"
                "6. Вы готовы к **долговременному сотрудничеству**\n\n"
                "✍️ **Отправьте нам заявку**\n"
                "Мы одобрим вашу заявку за **1 день**\n\n"
                "📜 **Заключим договор**\n"
                "Вы приступите к **работе**."
            )

        await callback_query.message.answer(rental_terms, parse_mode='Markdown')

    async def handle_show_contacts(self, callback_query: types.CallbackQuery):
        contact_info = (
            "📞 **Связаться с нами:**\n"
            "🏢 **Адрес:**\n"
            "г. Балашиха, мкр. Кучино, ул. Южная д.1, пом. 24\n\n"
            "🕒 **Время работы:**\n"
            "Мы работаем ежедневно с **8:00 до 20:00**\n\n"
            "📱 **Телефоны:**\n"
            "📞 +7 (910) 004-50-09\n"
            "📞 +7 (495) 215-04-84\n"
            "📞 +7 (495) 374-91-49\n\n"
            "✉️ **Email:**\n"
            "sprint-taxi01@mail.ru"
        )

        await callback_query.message.answer(contact_info, parse_mode='Markdown')

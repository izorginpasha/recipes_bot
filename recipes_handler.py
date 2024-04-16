import aiohttp
from googletrans import Translator
from random import choices
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.formatting import (
    Bold, as_list, as_marked_section
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types

router = Router()


class OrderWeather(StatesGroup):
    waiting_for_forecast = State()



async def categories(session):
    async with session.get(
            url=f'https://www.themealdb.com/api/json/v1/1/list.php?c=list',
    ) as resp:
        data = await resp.json()
        print(data['meals'])
        data_dates = [item['strCategory'] for item in data['meals']]
        print(data_dates)

    return data_dates


async def list_recipes(session, category, i):
    async with session.get(
            url=f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}',
    ) as resp:
        data = await resp.json()
        print(data)
        data = choices(data['meals'], k=i)
        print(data)


    return data


@router.message(Command("category_search_random"))
async def weather_time(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        await message.answer(
            "Ошибка: не переданы аргументы"
        )
        return
    async with aiohttp.ClientSession() as session:
        data = await categories(session)

        await state.set_data({'count': command.args, 'data_recip': data})
        builder = ReplyKeyboardBuilder()
        for date_item in data:
            builder.add(types.KeyboardButton(text=date_item))
        builder.adjust(4)
        await message.answer(
            f"Выберите категорию:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
        await state.set_state(OrderWeather.waiting_for_forecast.state)


@router.message(OrderWeather.waiting_for_forecast)
async def weather_by_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiohttp.ClientSession() as session:
        list = await list_recipes(session, message.text, data['count'])
    await message.answer(
        f"Погода в городе {data['count']} в {message.text}:  "

    )

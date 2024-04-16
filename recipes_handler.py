import asyncio
import aiohttp
from googletrans import Translator
from random import choices
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types

router = Router()
translator = Translator()


class OrderWeather(StatesGroup):
    waiting_for_forecast = State()
    waiting = State()


async def categories(session):
    async with session.get(
            url=f'https://www.themealdb.com/api/json/v1/1/list.php?c=list',
    ) as resp:
        data = await resp.json()

        data_dates = [item['strCategory'] for item in data['meals']]

    return data_dates


async def list_recipes(session, category, i):
    async with session.get(
            url=f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}',
    ) as resp:
        data = await resp.json()

        data = choices(data['meals'], k=int(i))

    return data


async def list_recipes_txt(session, id):
    async with session.get(
            url=f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}',
    ) as resp:
        data = await resp.json()

    return data['meals']


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
    await state.set_data({'list': list})
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Покажи рецепты"))

    builder.adjust(4)

    await message.answer(

        f"Как вам такие варианты: {[translator.translate(item['strMeal'], dest='ru').text for item in list]} "
        f"из {translator.translate(message.text, dest='ru').text}:  ",
        reply_markup=builder.as_markup(resize_keyboard=True),

    )
    await state.set_state(OrderWeather.waiting.state)


@router.message(OrderWeather.waiting)
async def mess(message: types.Message, state: FSMContext):
    data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        for meal in data['list']:
            instructions = await asyncio.gather(list_recipes_txt(session, int(meal['idMeal'])))

            await message.answer(
                f"Рецепт : {translator.translate(instructions[0][0]['strMeal'], dest='ru').text} "
                f"                                                         "
                f" {translator.translate(instructions[0][0]['strInstructions'], dest='ru').text}"
                f"                                                         "
                f" Ингредиенты : {[translator.translate(instructions[0][0][f'strIngredient{i + 1}'], dest='ru').text for i in range(20) if instructions[0][0][f'strIngredient{i + 1}'] != '']} ",

            )

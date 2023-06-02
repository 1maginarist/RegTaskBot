from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters import Text

import aiohttp
import re
import os
from dotenv import load_dotenv


from tgbot.states import Registration
from tgbot.keyboards import create_region_keyboard
from tgbot.keyboards import create_locals_keyboard
from tgbot.keyboards.callback_datas import regions_callback
from tgbot.keyboards.callback_datas import locals_callback
from tgbot.keyboards.inline_task_buttons import confirm_keyboard


# Taking values from .env
load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")


# Start handler (making request to check if user in database/Greetings if true, start registration if false)
async def command_start(message: types.Message):

    params = {
        "login": message.from_user.username,
        "chat_id": message.from_user.id
    }

    header = {
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(f'{host}/api/user/check', params=params) as resp:
            response = await resp.json()
            if response.get("ok"):
                await message.answer("Привет и добро пожаловать в нашего бота!")
            else:
                await message.answer("Привет! Для начала тебе нужно пройти регистрацию.\n"
                                     "Вы можете в любой момент прервать регистрацию командой /cancel\n"
                                     "Введите свое имя:")
                await Registration.name.set()


# Handler for any messages that can be sent to bot while in waiting mode
async def basic_text(message: types.Message):
    await message.answer("Ожидайте, бот сам вам напишет, когда для вас появятся задачи")


async def set_name(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data["name"] = message.text
        data['username'] = message.from_user.username
    await message.answer("Введите фамилию:")
    await Registration.surname.set()


async def set_surname(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data["surname"] = message.text
    await message.answer("Введите отчество:")
    await Registration.middle_name.set()


async def set_middle_name(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data["middle_name"] = message.text
    await message.answer("Введите телефон:")
    await Registration.phone_number.set()


async def set_phone_number(message: types.Message, state: FSMContext):
    phone_regexp = r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$'

    if re.match(phone_regexp, message.text):
        async with state.proxy() as data:
            data["phone_number"] = message.text
        await message.answer("Введите email:")
        await Registration.email.set()
    else:
        await message.answer("Номер телефона неверный, повторите попытку")


async def set_email(message: types.Message, state: FSMContext):
    email_regex = r'[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+'

    if re.match(email_regex, message.text):
        async with state.proxy() as data:
            data["email"] = message.text
        keyboard = await create_region_keyboard()
        await message.answer("Выберите ваш регион:", reply_markup=keyboard)
        await Registration.region.set()
    else:
        await message.answer("Email неверный, повторите попытку")


async def set_region(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data['region'] = callback_data.get("id")

        keyboard = await create_locals_keyboard(data['region'])
    await call.message.edit_text("Выберите ваш пункт:", reply_markup=keyboard)
    await Registration.city.set()


async def set_local(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data['city'] = callback_data.get('id')

        await call.message.answer(f"Проверьте правильность введенных данных:\n"
                                  f"Имя: {data['name']}\n"
                                  f"Фамилия: {data['surname']}\n"
                                  f"Отчество: {data['middle_name']}\n"
                                  f"Номер телефона: {data['phone_number']}\n"
                                  f"Email: {data['email']}\n"
                                  f"Регион: {data['region']}\n"
                                  f"Область: {data['city']}", reply_markup=confirm_keyboard)
    await Registration.confirm.set()


async def confirm(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:

        header = {
            'Content-Type': 'application/json',
            'Authorization-Token': '123asd'
        }

        params = {
            'username': f"@{data['username']}",
            'chat_id': call.message.chat.id,
            'name': data['name'],
            'surname': data['surname'],
            'middle_name': data['middle_name'],
            'phone_number': data['phone_number'],
            'email': data['email'],
            'region': data['region'],
            'local': data['city']
        }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(f'{host}/api/user/create', params=params) as resp:
            response = await resp.json()

            print(response)

    await call.message.edit_text(f"Благодарим за регистрацию!\n"
                                 "Ожидайте, бот свяжется с вами")

    await state.finish()


async def cancel_handler(msg: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await msg.answer('Ok')


def register_start(dp: Dispatcher):
    dp.register_message_handler(command_start, CommandStart())
    dp.register_message_handler(basic_text, content_types=['text'])
    dp.register_message_handler(cancel_handler, state="*", commands=['Cancel'])
    dp.register_message_handler(cancel_handler, Text(equals='Cancel', ignore_case=True), state="*")
    dp.register_message_handler(set_name, state=Registration.name)
    dp.register_message_handler(set_surname, state=Registration.surname)
    dp.register_message_handler(set_middle_name, state=Registration.middle_name)
    dp.register_message_handler(set_phone_number, state=Registration.phone_number)
    dp.register_message_handler(set_email, state=Registration.email)
    dp.register_callback_query_handler(set_region, regions_callback.filter(type="region"), state=Registration.region)
    dp.register_callback_query_handler(set_local, locals_callback.filter(type="local"), state=Registration.city)
    dp.register_callback_query_handler(confirm, Text("confirm"), state=Registration.confirm)

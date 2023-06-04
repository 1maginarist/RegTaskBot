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
from tgbot.handlers.tasks import send_message_api


# Taking values from .env
load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")


# Start handler (making request to check if user in database/Greetings if true, start registration if false)
async def command_start(message: types.Message):

    await send_message_api(message.from_user.id, message.message_id)

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
                temp_mess = await message.answer("Привет и добро пожаловать в нашего бота!")
                await send_message_api(temp_mess.chat.id, temp_mess.message_id)
                print(temp_mess.message_id)
            else:
                temp_mess = await message.answer("Привет! Для начала тебе нужно пройти регистрацию.\n"
                                     "Вы можете в любой момент прервать регистрацию командой /cancel\n"
                                     "Введите свое имя:")

                await send_message_api(temp_mess.chat.id, temp_mess.message_id)
                await Registration.name.set()


# Handler for any messages that can be sent to bot while in waiting mode
async def basic_text(message: types.Message):
    await send_message_api(message.from_user.id, message.message_id)

    temp_mess = await message.answer("Ожидайте, бот сам вам напишет, когда для вас появятся задачи")
    await send_message_api(temp_mess.chat.id, temp_mess.message_id)


async def set_name(message: types.Message, state: FSMContext):

    await send_message_api(message.from_user.id, message.message_id)

    async with state.proxy() as data:
        data["name"] = message.text
        data['username'] = message.from_user.username
    temp_mess = await message.answer("Введите фамилию:")

    await send_message_api(temp_mess.chat.id, temp_mess.message_id)
    await Registration.surname.set()


async def set_surname(message: types.Message, state: FSMContext):
    await send_message_api(message.from_user.id, message.message_id)

    async with state.proxy() as data:
        data["surname"] = message.text
    temp_mess = await message.answer("Введите отчество:")

    await send_message_api(temp_mess.chat.id, temp_mess.message_id)
    await Registration.middle_name.set()


async def set_middle_name(message: types.Message, state: FSMContext):
    await send_message_api(message.from_user.id, message.message_id)

    async with state.proxy() as data:
        data["middle_name"] = message.text
    temp_mess = await message.answer("Введите телефон:")

    await send_message_api(temp_mess.chat.id, temp_mess.message_id)
    await Registration.phone_number.set()


async def set_phone_number(message: types.Message, state: FSMContext):
    phone_regexp = r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$'
    await send_message_api(message.from_user.id, message.message_id)

    if re.match(phone_regexp, message.text):
        async with state.proxy() as data:
            data["phone_number"] = message.text
        temp_mess = await message.answer("Введите email:")
        await send_message_api(temp_mess.chat.id, temp_mess.message_id)
        await Registration.email.set()
    else:
        temp_mess = await message.answer("Номер телефона неверный, повторите попытку")
        await send_message_api(temp_mess.chat.id, temp_mess.message_id)


async def set_email(message: types.Message, state: FSMContext):
    email_regex = r'[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+'
    await send_message_api(message.from_user.id, message.message_id)

    if re.match(email_regex, message.text):
        async with state.proxy() as data:
            data["email"] = message.text
        keyboard = await create_region_keyboard()
        temp_mess = await message.answer("Выберите ваш регион:", reply_markup=keyboard)
        await send_message_api(temp_mess.chat.id, temp_mess.message_id)
        await Registration.region.set()
    else:
        temp_mess = await message.answer("Email неверный, повторите попытку")
        await send_message_api(temp_mess.chat.id, temp_mess.message_id)


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

        await call.message.edit_text(f"Проверьте правильность введенных данных:\n"
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
    await send_message_api(msg.from_user.id, msg.message_id)

    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    temp_mess = await msg.answer('Ok')
    await send_message_api(temp_mess.chat.id, temp_mess.message_id)


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

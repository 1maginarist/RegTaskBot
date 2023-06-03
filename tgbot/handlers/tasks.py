from aiogram.dispatcher.storage import FSMContext
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from tgbot.states import Tasks
from tgbot.keyboards.inline_task_buttons import end_task_keyboard
import aiohttp
import os
import asyncio
from dotenv import load_dotenv
from aiogram.utils.exceptions import BotBlocked
from tgbot.keyboards.inline_task_buttons import start_task_keyboard, reset_task_keyboard
from aiogram import Bot
from tgbot.config import load_config
from aiogram.contrib.fsm_storage.memory import MemoryStorage


load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

user_task_id = {}


async def accept_delete(chat_id, message_ids: dict):
    for message in message_ids:
        await bot.delete_message(chat_id=chat_id, message_id=message)


# Function to execute endpoint for confirmation in app.py
async def confirmation_user(chat_id, task_id, confirmation):
    blocked_users = []

    if confirmation:
        for user_id in chat_id:
            try:
                await bot.send_message(chat_id=user_id, text=f"Ваша задача - {task_id} была одобрена")

            except BotBlocked as err:
                blocked_users.append(user_id)
        return {
            "code": True,
            "blocked_users": blocked_users
        }

    else:
        for user_id in chat_id:
            try:
                await bot.send_message(chat_id=user_id, text="Ваша задача была отклонена\n"
                                                             "Пожалуйста, приcтупите к выполнению задачи снова",
                                       reply_markup=reset_task_keyboard)

                state = dp.current_state(chat=user_id)
                await state.set_state(Tasks.chat_id)

            except BotBlocked as err:
                blocked_users.append(user_id)
        return {
            "code": False,
            "blocked_users": blocked_users
        }


async def send_message(chat_id, message_id):
    params = {
        "message_id": message_id,
        "chat_id": chat_id
    }

    header = {
        'Content-Type': 'application/json',
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(f'{host}/api/task/message', params=params) as resp:
            response = await resp.text()


# Function to execute tasks sending in app.py
async def set_user_task(chat_id, task_id, text, documents):
    blocked_users = []

    try:
        for user_id in chat_id:
            try:
                await bot.send_message(chat_id=user_id, text=text)

                for doc in documents:
                    await bot.send_document(chat_id=user_id, document=doc)
                await asyncio.sleep(1)

                await bot.send_message(chat_id=user_id, text='Когда готовы нажмите "Приступить"',
                                       reply_markup=start_task_keyboard)

                await Tasks.task_id.set()
                state = dp.current_state(chat=user_id)
                await state.update_data(task_id=task_id)
                await state.set_state(Tasks.chat_id.state)

            except BotBlocked as err:
                blocked_users.append(user_id)

        return {
            "code": True,
            "blocked_users": blocked_users
        }

    except Exception as err:
        return {
            "code": False,
            "error": err
        }


# Handler for button start for task
async def start_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data["chat_id"] = call.from_user.id
        data["buffer"] = ''
    await call.message.edit_text("Пришлите результат выполнения задачи текстом\n"
                                 "Или начните загружать файлы по 1 за раз\n"
                                 "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)

    params = {
        "chat_id": f"{call.from_user.id}",
        #"task_id": state.get_data()
    }

    header = {
        'Content-Type': 'text/html',
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(f'{host}/api/task/approve', params=params) as resp:
            response = await resp.text()
    await Tasks.step_1.set()


# if the task is incorrect, restarts task process
async def reset_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data["chat_id"] = call.from_user.id
        data["buffer"] = ''
    await call.message.edit_text("Пришлите результат выполнения задачи текстом\n"
                                 "Или начните загружать файлы по 1 за раз\n"
                                 "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)
    await Tasks.step_1.set()


# Listening for documents to upload
async def step1_doc(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.document.file_id}'
        except AttributeError as err:
            await message.answer("Не удалось обработать ваш файл")


# Listening for photos upload
async def step1_photo(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.photo[0].file_id}'
            if 'caption' in message:
                data['buffer'] = data['buffer'] + f'***{message.caption}'
        except AttributeError as err:
            await message.answer("Не удалось обработать ваш файл")


# Listening for text to be sent
async def step1_text(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.text}'
        except Exception as err:
            await message.answer("Не удалось обработать ваш текст")


# Handles end of task then end button pressed
async def end_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    data = await state.get_data()
    await call.message.answer(f"****{data}****")

    async with state.proxy() as data:
        await call.message.answer(f"{data['buffer']}, {data['chat_id']}")

        header = {
            'Content-Type': 'text/html',
            'Authorization-Token': auth_token
        }

        params = {
            'chat_id': f"{data['chat_id']}",
            'data': f'{data["buffer"]}',
            #'task_id':
        }

        try:
            async with aiohttp.ClientSession(headers=header) as session:
                async with session.post(f'{host}/api/task/result', params=params) as resp:
                    response = await resp.text()

                    await call.message.edit_text("Благодарим за выполнение задания\n"
                                                 "Как только мы его проверим, вам придет сообщение")

        except Exception as err:
            await call.message.edit_text("Ошибка при отправке ответа, обратитесь к менеджеру")

    await state.finish()


def register_tasks(dp: Dispatcher):
    dp.register_callback_query_handler(start_task, Text("start_task"))
    dp.register_callback_query_handler(reset_task, Text("reset"))
    dp.register_message_handler(step1_doc, content_types=["document"], state='*')
    dp.register_message_handler(step1_photo, content_types=["photo"], state='*')
    dp.register_message_handler(step1_text, content_types=["text"], state='*')
    dp.register_callback_query_handler(end_task, Text("end_task"), state='*')

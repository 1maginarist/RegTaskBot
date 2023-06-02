from flask import Flask, request
from flask_restful import Api
from aiogram import types, Dispatcher
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
from tgbot.config import load_config
from pyrogram import Client
from pyrogram.raw import functions
import secrets
from aiogram.utils.exceptions import BotBlocked
from tgbot.keyboards.inline_task_buttons import start_task_keyboard, reset_task_keyboard
from tgbot.states import Tasks


app = Flask(__name__)
api = Api()
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Endpoint to confirm that user completed the task/
# If the task is completed successfully, we inform the person about it. If not, we ask them to retry the task.
@app.post('/bot.site.ru/confirmed')
async def confirmed_user():
    blocked_users = []

    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        task_id = data.get('task_id')
        confirmation = data.get('confirmation')

        if confirmation:
            for user_id in chat_id:
                try:
                    await bot.send_message(chat_id=user_id, text=f"Ваша задача - {task_id} была одобрена")
                except BotBlocked as err:
                    blocked_users.append(user_id)

            return {
                "Status": "Success",
                "Code": 200,
                "BlockedUsers": blocked_users
            }

        else:
            for user_id in chat_id:
                try:
                    await bot.send_message(chat_id=user_id, text="Ваша задача была отклонена\n"
                                                                 "Пожалуйста,приcтупите к выполнению задачи снова",
                                           reply_markup=reset_task_keyboard)

                    state = dp.current_state(chat=user_id)
                    await state.set_state(Tasks.chat_id)

                except BotBlocked as err:
                    blocked_users.append(user_id)

            return {
                "Status": "Success",
                "Code": 200,
                "BlockedUsers": blocked_users
            }

    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to send user a new task
@app.post('/bot.site.ru/writeUser')
async def write_user():
    blocked_users = []

    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        task_id = data.get('task_id')
        text = data.get('text')
        documents = data.get('documents')

        for user_id in chat_id:
            try:
                await bot.send_message(chat_id=user_id, text=text)
                for doc in documents:
                    await bot.send_document(chat_id=user_id, document=doc)
                await asyncio.sleep(1)

                await bot.send_message(chat_id=user_id, text='Когда готовы нажмите "Приступить"',
                                       reply_markup=start_task_keyboard)

                state = dp.current_state(chat=user_id)
                await state.set_state(Tasks.chat_id)

            except BotBlocked as err:
                blocked_users.append(user_id)

        return {
            "Status": "Success",
            "Code": 200,
            "BlockedUsers": blocked_users
        }

    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to authorize a new telegram account
@app.post("/bot.site.ru/authorize")
async def authorize():
    try:
        data = request.get_json()
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        token = secrets.token_hex(16)
        async with Client(f'{token}', api_id, api_hash) as application:
            await application.send_message('me', "Ваш аккаунт был авторизован")
        return {
            "Status": "Success",
            "Token": token
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to send messages from authorized account
@app.post("/bot.site.ru/sendMessage")
async def send_message():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        user = data.get('user')
        message = data.get('message')
        btn = data.get('btn')
        link = data.get('link')
        async with Client(f"{auth_token}") as application:
            await application.send_message(user, f'{message}\n{btn}: {link}')
        return {
            "Status": "Success",
            "Code": 200
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to create groups from authorized account
@app.post("/bot.site.ru/createGroup")
async def create_group():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        group_name = data.get('group_name')
        users = data.get('users')
        message = data.get('message')
        async with Client(f"{auth_token}") as application:
            group = await application.create_group(group_name, users)
            await application.send_message(group.id, f'{message}')
            supergroup = await application.invoke(functions.messages.MigrateChat(chat_id=abs(group.id)))
        return {
            "Status": "Success",
            "Code": 200,
            "Group_id": supergroup.updates[0].channel_id
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Endpoint to delete group created earlier
@app.post("/bot.site.ru/deleteGroup")
async def delete_group():
    try:
        data = request.get_json()
        auth_token = request.headers.get('Authorization')
        group_id = data.get('group_id')
        group_id = int('-100' + str(group_id))
        async with Client(f'{auth_token}') as application:
            await application.delete_supergroup(group_id)
        return {
            "Status": "Success",
            "Code": 200,
        }
    except Exception as err:
        return {
            "Status": "Error",
            "Code": 400,
            "Error": f'{err}'
        }


# Running flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0')
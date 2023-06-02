from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import os
from dotenv import load_dotenv

from tgbot.keyboards.callback_datas import locals_callback


load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")


# Creating keyboard for locals depending on region choice
async def create_locals_keyboard(id):

    header = {
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(f'{host}/api/locals/{id}') as resp:

            local_resp = await resp.json()

    local_keyboard = InlineKeyboardMarkup(row_width=2)

    for local in local_resp:
        button = InlineKeyboardButton(text=f"{local['name']}", callback_data=locals_callback.new(type="local", id=local['id']))
        local_keyboard.insert(button)

    return local_keyboard

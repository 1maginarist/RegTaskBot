from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import os
from dotenv import load_dotenv

from tgbot.keyboards.callback_datas import regions_callback

load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")


# Creating a regions keyboard for registration
async def create_region_keyboard():
    header = {
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(f'{host}/api/regions') as resp:
            regions = await resp.json()

    region_keyboard = InlineKeyboardMarkup(row_width=2)

    for region in regions:
        button = InlineKeyboardButton(text=f"{region['name']}", callback_data=regions_callback.new(type="region", id=region['id']))
        region_keyboard.insert(button)

    return region_keyboard

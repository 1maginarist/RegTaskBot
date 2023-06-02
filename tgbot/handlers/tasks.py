from aiogram.dispatcher.storage import FSMContext
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from tgbot.states import Tasks
from tgbot.keyboards.inline_task_buttons import end_task_keyboard
import aiohttp
import os
from dotenv import load_dotenv


load_dotenv()
host = os.getenv("HOST")
auth_token = os.getenv("AUTH_TOKEN")


async def start_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data["chat_id"] = call.from_user.id
        data["buffer"] = ''
    await call.message.edit_text("Пришлите результат выполнения задачи текстом\n"
                                 "Или начните загружать файлы по 1 за раз\n"
                                 "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)

    params = {
        "chat_id": f"{call.from_user.id}"
        #"task_id":
        #"timestamp":
    }

    header = {
        'Content-Type': 'application/json',
        "Authorization-Token": auth_token
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(f'{host}/api/task/approve', params=params) as resp:
            response = await resp.json()
    await Tasks.step_1.set()


async def reset_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        data["chat_id"] = call.from_user.id
        data["buffer"] = ''
    await call.message.edit_text("Пришлите результат выполнения задачи текстом\n"
                                 "Или начните загружать файлы по 1 за раз\n"
                                 "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)
    await Tasks.step_1.set()


async def step1_doc(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.document.file_id}'
        except AttributeError as err:
            await message.answer("Не удалось обработать ваш файл")

    '''await message.answer("Вы можете продолжить загрузку\n"
                         "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)'''


async def step1_photo(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.photo[0].file_id}'
        except AttributeError as err:
            await message.answer("Не удалось обработать ваш файл")

    '''await message.answer("Вы можете продолжить загрузку\n"
                         "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)'''


async def step1_text(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        try:
            data['buffer'] = data['buffer'] + f'***{message.text}'
        except Exception as err:
            await message.answer("Не удалось обработать ваш текст")

    '''await message.answer("Вы можете продолжить загрузку\n"
                         "Когда закончите, нажмите 'Завершить'", reply_markup=end_task_keyboard)'''


async def end_task(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    async with state.proxy() as data:
        print(data)
        await call.message.answer(f"{data['buffer']}, {data['chat_id']}")
        header = {
            'Content-Type': 'application/json',
            'Authorization-Token': auth_token
        }

        params = {
            'chat_id': f"{data['chat_id']}",
            'data': f'{data["buffer"]}'
        }

        async with aiohttp.ClientSession(headers=header) as session:
            async with session.post(f'{host}/api/task/result', params=params) as resp:
                response = await resp.json()

                if response:
                    await call.message.edit_text("Благодарим за выполнение задания\n"
                                                 "Как только мы его проверим, вам придет сообщение")

    await state.finish()


def register_tasks(dp: Dispatcher):
    dp.register_callback_query_handler(start_task, Text("start_task"))
    dp.register_callback_query_handler(reset_task, Text("reset"))
    dp.register_message_handler(step1_doc, content_types=["document"], state='*')
    dp.register_message_handler(step1_photo, content_types=["photo"], state='*')
    dp.register_message_handler(step1_text, content_types=["text"], state='*')
    dp.register_callback_query_handler(end_task, Text("end_task"), state='*')

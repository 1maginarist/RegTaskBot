from aiogram.dispatcher.filters.state import State, StatesGroup


# Class for tasks distribution algorithm
class Tasks(StatesGroup):
    task_id = State()
    chat_id = State()
    messages = State()
    buffer = State()
    step_1 = State()

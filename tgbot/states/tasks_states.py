from aiogram.dispatcher.filters.state import State, StatesGroup


# Class for tasks distribution algorithm
class Tasks(StatesGroup):
    chat_id = State()
    buffer = State()
    step_1 = State()

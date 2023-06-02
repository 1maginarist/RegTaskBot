from aiogram.dispatcher.filters.state import State, StatesGroup


# States for registration
class Registration(StatesGroup):
    name = State()
    username = State()
    surname = State()
    middle_name = State()
    phone_number = State()
    email = State()
    region = State()
    city = State()
    confirm = State()

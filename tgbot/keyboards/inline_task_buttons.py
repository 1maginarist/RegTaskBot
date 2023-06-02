from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Starting task delegated to user
start_button = InlineKeyboardButton('Приступить', callback_data='start_task')
start_task_keyboard = InlineKeyboardMarkup().add(start_button)

# Reset task if not confirmed by admin
reset_button = InlineKeyboardButton('Переделать', callback_data='reset')
reset_task_keyboard = InlineKeyboardMarkup().add(reset_button)

# End task
end_button = InlineKeyboardButton('Завершить', callback_data='end_task')
end_task_keyboard = InlineKeyboardMarkup().add(end_button)

# Confirm that bio is correct then registering
confirm_butt = InlineKeyboardButton('Все верно', callback_data='confirm')
confirm_keyboard = InlineKeyboardMarkup().add(confirm_butt)


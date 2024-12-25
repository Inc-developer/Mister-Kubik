from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='⚙️ Профиль'), KeyboardButton(text='🎲 Играть')],
    [KeyboardButton(text='❗Правила')]
                                    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите раздел меню')

profile_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пополнить баланс', callback_data='balance_deposit'),
     InlineKeyboardButton(text='Вывести средства', callback_data='balance_withdraw')],
     [InlineKeyboardButton(text='История выводов', callback_data='show_withdraws'), 
      InlineKeyboardButton(text='Помощь', url='t.me/helper_kubiki')]
])

game_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔒 Создать', callback_data='new_game'),
     InlineKeyboardButton(text='🔥 Комнаты', callback_data='show_games')],
     [InlineKeyboardButton(text='🌟 Присоединиться', callback_data='game_join'), 
      InlineKeyboardButton(text='🧨 Удалить', callback_data='game_delete')]
])

select_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выбрать", callback_data='choose_num')]
])
from Addons.config import TELEGRAM_TOKEN, YANDEX_TOKEN, YANDEX_CARD
from Addons.database import Database
from Addons.bot_keyboards import *
from aiogram import Bot, Dispatcher, F
from aiogram.enums import DiceEmoji
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from yoomoney import Client, Quickpay
from uuid import uuid4

import asyncio
import logging


database = Database()
client = Client(YANDEX_TOKEN)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

class MoneyAmount(StatesGroup):
    amount = State()

class MoneyWithdraw(StatesGroup):
    amount = State()
    w_adress = State()

class GetRoomNumber(StatesGroup):
    game_id = State()

class CreateGame(StatesGroup):
    game_id = State()
    bet_amount = State()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if database.user_exists(user_id) == False:
        database.add_user(user_id)
    await message.answer('* Добро пожаловать в самую лучшую версию кубов во всем снг * \
                         \n\n* 1. Игра длится 6 минут, после чего побеждает тот, кто набрал большее кол-во очков. * \
                         \n\n* 2. Игра может завершиться досрочно, если один из игроков набирает 3 очка. *\
                         \n\n* 3. Минимальная сумма игры - 10 рублей. * \
                         \n\n* 4. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                         \n\n* 5. Необходимо угадать число, которое выпадет на кости. * \
                         \n\n* 6. Комиссия от выигрыша составляет - 10% \
                         \n\n* Удачной игры! *', reply_markup=main_kb)


@dp.message(F.text == '❗Правила')
async def rules(message: Message):
    await message.reply('* Добро пожаловать в самую лучшую версию кубов во всем снг * \
                         \n\n* 1. Игра длится 6 минут, после чего побеждает тот, кто набрал большее кол-во очков. * \
                         \n\n* 2. Игра может завершиться досрочно, если один из игроков набирает 3 очка. *\
                         \n\n* 3. Минимальная сумма игры - 10 рублей. * \
                         \n\n* 4. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                         \n\n* 5. Необходимо угадать число, которое выпадет на кости. * \
                         \n\n* 6. Комиссия от выигрыша составляет - 10% \
                         \n\n* Удачной игры! *', reply_markup=main_kb)
    

@dp.message(F.text == '⚙️ Профиль')
async def show_profile(message: Message):
    user_id = message.from_user.id
    if database.user_exists(user_id) == False:
        database.add_user(user_id)
    await message.reply(f'* Ваш баланс: {database.check_balance(user_id)} руб *', reply_markup=profile_kb)


@dp.message(F.text == '🎲 Играть')
async def game_button(message: Message):
    user_id = message.from_user.id
    if database.user_exists(user_id) == False:
        database.add_user(user_id)
    await message.reply("Выберите действие", reply_markup=game_kb)


@dp.callback_query(F.data == 'show_games')
async def show_games(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer('Выполняется поиск')
    await callback.message.edit_text(database.game_get(user_id), reply_markup=game_kb)

@dp.callback_query(F.data == 'game_delete')
async def game_delete_first(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer('Ожидайте')
    await state.set_state(GetRoomNumber.game_id)
    await bot.send_message(user_id, "Введите номер комнаты ->")


@dp.message(GetRoomNumber.game_id)
async def game_delete_main(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(game_id=message.text)
    data = await state.get_data()
    if database.game_exists(data["game_id"]) == True and database.game_status(data["game_id"]) == 1:
        await state.clear()
        return await bot.send_message(user_id, database.game_delete(user_id, data["game_id"]))
    

@dp.callback_query(F.data == 'show_withdraws')
async def show_withdraws(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer('Выполняется поиск')
    await callback.message.edit_text(database.withdraws_get(user_id), reply_markup=profile_kb)


@dp.callback_query(F.data == 'new_game')
async def new_game_first(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer('Ожидайте')
    if database.check_player_in_game(user_id):
        return await bot.send_message(user_id, "Вы уже создали комнату либо находитесь в игре")
    await state.set_state(CreateGame.game_id)
    await bot.send_message(user_id, "Введите номер комнаты от 1 до 99 ->")


@dp.message(CreateGame.game_id)
async def new_game_second(message: Message, state: FSMContext):
    await state.update_data(game_id=message.text)
    await state.set_state(CreateGame.bet_amount)
    await message.reply("Введите сумму ставки (минимум - 10 руб) ->")


@dp.message(CreateGame.bet_amount)
async def new_game_main(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(bet_amount=message.text)
    data = await state.get_data()
    balance_amount = database.check_balance(user_id)
    if int(data["game_id"]) < 1 or int(data["game_id"]) > 99:
        return await bot.send_message(user_id, "Неверный номер комнаты")
    if database.game_exists(int(data["game_id"])):
        return await bot.send_message(user_id, "Комната с таким номером уже существует")
    if int(data["bet_amount"]) < 10 or int(data["bet_amount"]) > balance_amount:
        return await bot.send_message(user_id, "Ставка слишком маленькая / на балансе недостаточно средств")
    database.game_create(int(data["game_id"]), user_id, int(data["bet_amount"]))
    await state.clear()
    return await message.reply("Комната успешно создана!")
    


@dp.callback_query(F.data == 'balance_deposit')
async def balance_deposit(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer('Загрузка')
    await state.set_state(MoneyAmount.amount)
    await bot.send_message(user_id, 'Введите сумму пополнения ниже')


@dp.message(MoneyAmount.amount)
async def main_balance_deposit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(amount=message.text)
    data = await state.get_data()
    if int(data["amount"]) < 10:
        await bot.send_message(user_id, "Сумма пополнения должна быть больше 10 рублей.")
    else:
        label = str(uuid4())
        quickpay = Quickpay(
            receiver = YANDEX_CARD,
            quickpay_form = "shop",
            targets = "Кубик",
            paymentType = "SB",
            sum = int(data["amount"]),
            label = label
        )
        await bot.send_message(user_id, f"Ваша ссылка на оплату (срок действия - 45 секунд): {quickpay.redirected_url}")
        await bot.send_message(user_id, "⚜️Проверка платежа может занять до 2-ух минут.")
        await asyncio.sleep(90)
        try:
            history = client.operation_history(label=str(label))
            if history.operations == []:
                await bot.send_message(user_id, "⚜️Сожалеем но платеж не был обнаружен...")
                await state.clear()
            else:
                for operation in history.operations:
                    if operation.status == 'success':
                        database.add_balance(user_id, int(data["amount"]))
                        await bot.send_message(user_id, "⚜️Баланс успешно пополнен. Приятной игры!")
                        await state.clear()
        except Exception as e:
            print(e)


@dp.callback_query(F.data == 'balance_withdraw')
async def balance_withdraw_first(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer('Загрузка')
    await state.set_state(MoneyWithdraw.amount)
    await bot.send_message(user_id, 'Введите сумму вывода ->')


@dp.message(MoneyWithdraw.amount)
async def balance_withdraw_second(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(MoneyWithdraw.w_adress)
    await message.reply("Введите номер карты(телефона) для вывода средств ->")


@dp.message(MoneyWithdraw.w_adress)
async def main_balance_withdraw(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(w_adress=message.text)
    data = await state.get_data()
    balance_amount = database.check_balance(user_id)
    if int(data["amount"]) < 50:
        return await bot.send_message(user_id, "Сумма вывода должна быть больше 49 рублей.")
    if int(data["amount"]) <= balance_amount:
        database.remove_balance(user_id, int(data["amount"]))
        database.withdraw_add(user_id, data["w_adress"], int(data['amount']))
        await message.reply("Заявка на вывод успешно создана!")
        await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(filename='logs/logs.log',
            filemode='a',
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
            level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Done')

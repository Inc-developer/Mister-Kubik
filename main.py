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

class GetRoomNumberDel(StatesGroup):
    game_id = State()

class GetRoomNumberJoin(StatesGroup):
    game_id = State()

class CreateGame(StatesGroup):
    game_id = State()
    bet_amount = State()

class ChooseNumber(StatesGroup):
    chosen_number = State()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if database.user_exists(user_id) == False:
        database.add_user(user_id)
    await message.answer('* Добро пожаловать в самую лучшую версию кубов во всем снг * \
                         \n\n* 1. Игра длится пока один из игроков не наберет 2 очка. *\
                         \n\n* 2. Минимальная сумма игры - 10 рублей. * \
                         \n\n* 3. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                         \n\n* 4. Необходимо угадать число, которое выпадет на кости. * \
                         \n\n* 5. Комиссия от выигрыша составляет - 10% \
                         \n\n* Удачной игры! *', reply_markup=main_kb)


@dp.message(F.text == '❗Правила')
async def rules(message: Message):
    await message.reply('* Добро пожаловать в самую лучшую версию кубов во всем снг * \
                         \n\n* 1. Игра длится пока один из игроков не наберет 2 очка. *\
                         \n\n* 2. Минимальная сумма игры - 10 рублей. * \
                         \n\n* 3. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                         \n\n* 4. Необходимо угадать число, которое выпадет на кости. * \
                         \n\n* 5. Комиссия от выигрыша составляет - 10% \
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
    await state.set_state(GetRoomNumberDel.game_id)
    await bot.send_message(user_id, "Введите номер комнаты ->")


@dp.message(GetRoomNumberDel.game_id)
async def game_delete_main(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(game_id=message.text)
    data = await state.get_data()
    if database.game_exists(data["game_id"]) == True and database.game_status(data["game_id"]) == 1:
        await state.clear()
        return await bot.send_message(user_id, database.game_delete(user_id, data["game_id"]))
    else:
        await state.clear()
        return await bot.send_message(user_id, "Такой комнаты не существует или она находится в процессе игры")


@dp.callback_query(F.data == 'game_join')
async def game_join_first(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer('Ожидайте')
    await state.set_state(GetRoomNumberJoin.game_id)
    await bot.send_message(user_id, "Введите номер комнаты ->")


async def start_timer(user_id):
    global is_running
    is_running = True
    n = 30
    while is_running:
        n -= 1
        await asyncio.sleep(1)
        if n == 0:
            game_id = database.get_game_id(user_id)
            game_bet = database.check_game_bet_amount(game_id)
            is_running = False
            if database.check_which_num_user(user_id) == "first_user_id":
                second_user_id = database.check_second_user_id(game_id)
                await bot.send_message(user_id, "🔴Время на ход закончилось, вы проиграли🔴")
                await bot.send_message(second_user_id,"🍀Вы выиграли, у противника закончилось время на ход🍀")
                database.user_won(second_user_id, game_bet)
                database.user_lose(user_id, game_bet)
                database.game_done(second_user_id, user_id, second_user_id, game_bet)
                database.game_done_del(game_id)
                return is_running
            if database.check_which_num_user(user_id) == "second_user_id":
                first_user_id = database.check_first_user_id(game_id)
                await bot.send_message(user_id, "🔴Время на ход закончилось, вы проиграли🔴")
                await bot.send_message(first_user_id,"🍀Вы выиграли, у противника закончилось время на ход🍀" )
                database.user_won(first_user_id, game_bet)
                database.user_lose(user_id, game_bet)
                database.game_done(first_user_id, first_user_id, user_id, game_bet)
                database.game_done_del(game_id)
                return is_running


async def stop_timer():
    global is_running
    is_running = False
    return is_running


@dp.message(GetRoomNumberJoin.game_id)
async def game_join_main(message: Message, state: FSMContext):
    second_user_id = message.from_user.id
    player_balance = database.check_balance(second_user_id)
    await state.update_data(game_id=message.text)
    data = await state.get_data()
    if database.check_player_in_game(second_user_id) == True:
        await state.clear()
        return await message.reply("Вы уже находитесь в игре или у вас создана комната")
    if database.game_exists(data["game_id"]) == False:
        await state.clear()
        return await message.reply("Такой комнаты не существует")
    if player_balance < database.check_game_bet_amount(data["game_id"]):
        await state.clear()
        return await message.reply("У вас недостаточно средств")
    database.game_join(data["game_id"], second_user_id)
    first_user_id = database.check_first_user_id(data["game_id"])
    await bot.send_message(first_user_id, "❗В вашу комнату зашел игрок❗\n\n\n \
                         \n\n* 1. Игра длится пока один из игроков не наберет 2 очка. *\
                         \n\n* 2. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                         \n\n* 3. Необходимо написать и угадать число (1-9), которое выпадет на кости (её кидает бот). * \
                         \n\n* 4. Когда бот сообщит о вашем ходе, необходите нажать на кнопку 'Выбрать' под его сообщением * \
                         \n\n\n❗Бот сообщит о вашем ходе❗")
    await bot.send_message(second_user_id, "❗Вы успешно зашли в комнату❗\n\n\n \
                        \n\n* 1. Игра длится пока один из игроков не наберет 2 очка. *\
                        \n\n* 2. Время на ход для каждого игрока - 30 секунд, после чего игрок автоматически проигрывает. * \
                        \n\n* 3. Необходимо написать и угадать число (1-9), которое выпадет на кости (её кидает бот). * \
                        \n\n* 4. Когда бот сообщит о вашем ходе, необходите нажать на кнопку 'Выбрать' под его сообщением * \
                        \n\n\n❗Бот сообщит о вашем ходе❗")
    await bot.send_message(first_user_id, "❗Ваш ход❗", reply_markup=select_kb)
    game_id = database.get_game_id(first_user_id)
    database.set_turn_id(game_id, first_user_id)
    await state.clear()
    return await start_timer(first_user_id)


@dp.callback_query(F.data == 'choose_num')
async def game_choose_number_fist(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.set_state(ChooseNumber.chosen_number)
    await bot.send_message(user_id, "Введите ваше число ->")


@dp.message(ChooseNumber.chosen_number)
async def game_choose_number(message: Message, state: FSMContext):
    await state.update_data(chosen_number=message.text)
    data = await state.get_data()
    user_msg = data["chosen_number"]
    user_id = message.from_user.id
    if database.check_player_in_active_game(user_id) == False:
        await state.clear()
        return await message.reply("Неизвестная команда")
    game_id = database.get_game_id(user_id)
    if database.check_which_turn(game_id) != user_id:
        await state.clear()
        return await message.reply("❗Не ваша очередь ходить❗")
    if int(user_msg) not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        await state.clear()
        return await message.reply("❗Необходимо указать число от 1 до 9❗")
    else:
        await stop_timer()
        game_id = database.get_game_id(user_id)
        user_num_choose = int(user_msg)
        game_bet = database.check_game_bet_amount(game_id)
        msg = await bot.send_dice(user_id, protect_content=None)
        msg_id = int(msg.message_id)
        dice_value = int(msg.dice.value)

        if user_num_choose == dice_value:
            if database.check_which_num_user(user_id) == "first_user_id":
                second_user_id = database.check_second_user_id(game_id)
                await bot.send_message(second_user_id, f"Оппонент: {user_num_choose}")
                await bot.forward_message(second_user_id, user_id, msg_id)
                await asyncio.sleep(4)
                database.game_update_score(user_id)
                await bot.send_message(user_id, f"🍀Вы угадали🍀, Ваш счёт: {database.game_check_score(user_id)}")
                await bot.send_message(second_user_id, f"🔴Ваш оппонент угадал🔴, Его счёт: {database.game_check_score(user_id)}")
                if database.check_score_end(user_id) == True:
                    await bot.send_message(user_id, "🍀Вы выиграли, игра закончена🍀")
                    await bot.send_message(second_user_id,"🔴Вы проиграли, игра закончена🔴" )
                    database.user_won(user_id, game_bet)
                    database.user_lose(second_user_id, game_bet)
                    database.game_done(user_id, user_id, second_user_id, game_bet)
                    await state.clear()
                    return database.game_done_del(game_id)
                else:
                    database.set_turn_id(game_id, second_user_id)
                    await state.clear()
                    await bot.send_message(second_user_id, "❗Ваш ход❗", reply_markup=select_kb)
                    return await start_timer(second_user_id)
                
            if database.check_which_num_user(user_id) == "second_user_id":
                first_user_id = database.check_first_user_id(game_id)
                await bot.send_message(first_user_id, f"Оппонент: {user_num_choose}")
                await bot.forward_message(first_user_id, user_id, msg_id)
                await asyncio.sleep(4)
                database.game_update_score(user_id)
                await bot.send_message(user_id, f"🍀Вы угадали🍀, Ваш счёт: {database.game_check_score(user_id)}")
                await bot.send_message(first_user_id, f"🔴Ваш оппонент угадал🔴, Его счёт: {database.game_check_score(user_id)}")
                if database.check_score_end(user_id) == True:
                    await bot.send_message(user_id, "🍀Вы выиграли, игра закончена🍀")
                    await bot.send_message(first_user_id,"🔴Вы проиграли, игра закончена🔴")
                    database.user_won(user_id, game_bet)
                    database.user_lose(first_user_id, game_bet)
                    database.game_done(user_id, first_user_id, user_id, game_bet)
                    await state.clear()
                    return database.game_done_del(game_id)
                else:
                    database.set_turn_id(game_id, first_user_id)
                    await state.clear()
                    await bot.send_message(first_user_id,"❗Ваш ход❗", reply_markup=select_kb)
                    return await start_timer(first_user_id)
        else:
            if database.check_which_num_user(user_id) == "first_user_id":
                second_user_id = database.check_second_user_id(game_id)
                await bot.send_message(second_user_id, f"Оппонент: {user_num_choose}")
                await bot.forward_message(second_user_id, user_id, msg_id)
                await asyncio.sleep(4)
                await bot.send_message(user_id, "🔴Вы не угадали🔴")
                await bot.send_message(second_user_id, "🍀Ваш оппонент не угадал🍀")
                database.set_turn_id(game_id, second_user_id)
                await state.clear()
                await bot.send_message(second_user_id,"❗Ваш ход❗", reply_markup=select_kb)
                return await start_timer(second_user_id)

            if database.check_which_num_user(user_id) == "second_user_id":
                first_user_id = database.check_first_user_id(game_id)
                await bot.send_message(first_user_id, f"Оппонент: {user_num_choose}")
                await bot.forward_message(first_user_id, user_id, msg_id)
                await asyncio.sleep(4)
                await bot.send_message(user_id, "🔴Вы не угадали🔴")
                await bot.send_message(first_user_id, "🍀Ваш оппонент не угадал🍀")
                database.set_turn_id(game_id, first_user_id)
                await state.clear()
                await bot.send_message(first_user_id,"❗Ваш ход❗", reply_markup=select_kb)
                return await start_timer(first_user_id)


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

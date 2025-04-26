from Addons.config import POSTGRE_HOST, POSTGRE_DB_NAME, POSTGRE_USERNAME, \
    POSTGRE_PASSWORD, POSTGRE_PORT

import psycopg2
import datetime



class Database:
    def __init__(self):
        self.connection = psycopg2.connect(
            host=POSTGRE_HOST,
            dbname=POSTGRE_DB_NAME,
            user=POSTGRE_USERNAME,
            password=POSTGRE_PASSWORD,
            port=POSTGRE_PORT
            )
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.users WHERE \
                                 user_id = '{user_id}'")
            if self.cursor.fetchone():
                return True
            else:
                return False

    def check_balance(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM kubik.users WHERE \
                                user_id = '{user_id}'")
            balance = 0
            for i in self.cursor.fetchone():
                balance += i
            return balance

    def add_balance(self, user_id, amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM kubik.users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance += (amount - (amount * 0.06))
            return self.cursor.execute("""UPDATE kubik.users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def remove_balance(self, user_id, amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM kubik.users WHERE \
                                user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance -= amount
            return self.cursor.execute("""UPDATE kubik.users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"INSERT INTO kubik.users (user_id, balance) \
                                VALUES ('{user_id}', 0)")

    def user_won(self, user_id, win_amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM kubik.users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance += (win_amount - (win_amount * 0.1))
            return self.cursor.execute("""UPDATE kubik.users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def user_lose(self, user_id, lose_amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM kubik.users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance -= lose_amount
            return self.cursor.execute("""UPDATE kubik.users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def game_done(self, user_winner_id, first_user_id,
                  second_user_id, bet_amount):
        game_date = str(datetime.datetime.now().replace(microsecond=0))
        with self.connection:
            self.cursor.execute("SELECT id FROM kubik.games")
            last_id = 0
            for i in self.cursor.fetchall():
                last_id += 1
            last_id += 1
            return self.cursor.execute("""INSERT INTO kubik.games
                (id, date_end, winner_id, user1_id, user2_id, bet)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                        (last_id, game_date, user_winner_id, first_user_id, second_user_id, bet_amount))

    def withdraw_add(self, user_id, w_adress, amount):
        w_date = str(datetime.datetime.now().replace(microsecond=0))
        w_status = "Process"
        with self.connection:
            self.cursor.execute("SELECT id FROM kubik.withdraws")
            last_id = 0
            for i in self.cursor.fetchall():
                last_id += 1
            last_id += 1
            return self.cursor.execute("""INSERT INTO kubik.withdraws
                (id, user_id, w_adress, amount, w_date, w_status)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                        (last_id, user_id, w_adress, amount, w_date, w_status))

    def withdraws_get(self, user_id):
        withdraws_data = ""
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.withdraws WHERE \
                                user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                withdraws_data += f"\n\nНомер счёта: {i[2]}, Сумма: {i[3]}, Дата: {i[4]}, Статус: {i[5]}"
            if withdraws_data == "":
                return "У вас нет выводов"
            return withdraws_data

    def game_exists(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                    game_id = '{game_id}'")
            if self.cursor.fetchone():
                return True
            else:
                return False

    def game_status(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT game_status FROM kubik.game WHERE \
                    game_id = '{game_id}'")
            game_status = 0
            for i in self.cursor.fetchone():
                game_status += i
            return game_status

    def game_create(self, game_id, user_id, bet_amount):
        turn_id = 0
        game_status = 1
        score = 0
        with self.connection:
            return self.cursor.execute("""INSERT INTO kubik.game
                (game_id, first_user_id, bet_amount, game_status, first_user_score, second_user_score, turn_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (game_id, user_id, bet_amount, game_status, score, score, turn_id))

    def game_join(self, game_id, user_id):
        with self.connection:
            return self.cursor.execute("""UPDATE kubik.game SET second_user_id = %s, game_status = 2
                    WHERE game_id = %s""", (user_id, game_id))

    def game_done_del(self, game_id):
        with self.connection:
            return self.cursor.execute(f"DELETE FROM kubik.game WHERE \
                                       game_id = '{game_id}'")

    def game_get(self, user_id):
        games_data = ""
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game")
            for i in self.cursor.fetchall():
                if_person = ""
                if int(i[4]) == 1:
                    if i[1] == user_id:
                        if_person = "(Моя)"
                    games_data += f"\n\nНомер комнаты: {i[0]}, Сумма ставки: {i[3]} {if_person}"
            if games_data == "":
                return "Нет активных игр"
            return games_data

    def game_delete(self, user_id, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' AND game_id = '{game_id}'")
            if self.cursor.fetchone():
                self.cursor.execute(f"DELETE FROM kubik.game WHERE \
                                    game_id = '{game_id}'")
                return "Комната успешно удалена!"
            return "У вас нет прав на эту комнату!"

    def check_player_in_game(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            if self.cursor.fetchone():
                return True
            return False

    def check_player_in_active_game(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}' AND game_status = 2")
            if self.cursor.fetchone():
                return True
            return False

    def check_game_bet_amount(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT bet_amount FROM kubik.game WHERE \
                    game_id = '{game_id}'")
            bet_amount = 0
            for i in self.cursor.fetchone():
                bet_amount += i
            return bet_amount

    def check_first_user_id(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT first_user_id FROM kubik.game WHERE \
                    game_id = '{game_id}'")
            first_user_id = 0
            for i in self.cursor.fetchone():
                first_user_id += i
            return first_user_id

    def check_second_user_id(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT second_user_id FROM kubik.game WHERE \
                    game_id = '{game_id}'")
            first_user_id = 0
            for i in self.cursor.fetchone():
                first_user_id += i
            return first_user_id

    def check_which_num_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                    first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                if int(i[1]) == user_id:
                    return "first_user_id"
            return "second_user_id"

    def check_which_turn(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT turn_id FROM kubik.game WHERE \
                                game_id = '{game_id}'")
            turn_id = 0
            for i in self.cursor.fetchone():
                turn_id += i
            return turn_id

    def get_game_id(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT game_id FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            game_id = 0
            for i in self.cursor.fetchone():
                game_id += i
            return game_id

    def set_turn_id(self, game_id, user_id):
        with self.connection:
            return self.cursor.execute("""UPDATE kubik.game SET turn_id = %s
                WHERE game_id = %s""", (user_id, game_id))

    def game_update_score(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                if int(i[1]) == user_id:
                    score = int(i[5]) + 1
                    return self.cursor.execute("""UPDATE kubik.game SET first_user_score = %s
                WHERE first_user_id = %s""", (score, user_id))
                if int(i[2]) == user_id:
                    score = int(i[6]) + 1
                    return self.cursor.execute("""UPDATE kubik.game SET second_user_score = %s
                WHERE second_user_id = %s""", (score, user_id))

    def game_check_score(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                if int(i[1]) == user_id:
                    return int(i[5])
                if int(i[2]) == user_id:
                    return int(i[6])

    def game_can_move_check(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT can_move FROM kubik.game WHERE \
                                game_id = '{game_id}'")
            can_move = 0
            for i in self.cursor.fetchone():
                can_move += i
            return can_move

    def game_can_move_set(self, game_id, move_status):
        with self.connection:
            return self.cursor.execute("""UPDATE kubik.game SET can_move = %s
                    WHERE game_id = %s""", (move_status, game_id))

    def game_join(self, game_id, user_id):
        with self.connection:
            return self.cursor.execute("""UPDATE kubik.game SET second_user_id = %s, game_status = 2
                    WHERE game_id = %s""", (user_id, game_id))

    def check_score_end(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM kubik.game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                if int(i[5]) == 2 or int(i[6]) == 2:
                    return True
            return False

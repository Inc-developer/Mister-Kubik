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
            self.cursor.execute(f"SELECT * FROM users WHERE \
                                 user_id = '{user_id}'")
            if self.cursor.fetchone():
                return True
            else:
                return False

    def check_balance(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM users WHERE \
                                user_id = '{user_id}'")
            balance = 0
            for i in self.cursor.fetchone():
                balance += i
            return balance

    def add_balance(self, user_id, amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance += (amount - (amount * 0.06))
            return self.cursor.execute("""UPDATE users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def remove_balance(self, user_id, amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM users WHERE \
                                user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance -= amount
            return self.cursor.execute("""UPDATE users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"INSERT INTO users (user_id, balance) \
                                VALUES ('{user_id}', 0)")

    def user_won(self, user_id, win_amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance += (win_amount - (win_amount * 0.1))
            return self.cursor.execute("""UPDATE users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def user_lose(self, user_id, lose_amount):
        with self.connection:
            self.cursor.execute(f"SELECT balance FROM users \
                                WHERE user_id = '{user_id}'")
            new_balance = 0
            for i in self.cursor.fetchone():
                new_balance += i
            new_balance -= lose_amount
            return self.cursor.execute("""UPDATE users SET balance = %s
                                WHERE user_id = %s""", (new_balance, user_id))

    def game_done(self, user_winner_id, first_user_id,
                  second_user_id, bet_amount):
        game_date = str(datetime.datetime.now().replace(microsecond=0))
        with self.connection:
            self.cursor.execute("SELECT id FROM games")
            last_id = 0
            for i in self.cursor.fetchall():
                last_id += 1
            last_id += 1
            return self.cursor.execute("""INSERT INTO games
                (id, date_end, winner_id, user1_id, user2_id, bet)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                        (last_id, game_date, user_winner_id, first_user_id, second_user_id, bet_amount))

    def withdraw_add(self, user_id, w_adress, amount):
        w_date = str(datetime.datetime.now().replace(microsecond=0))
        w_status = "Process"
        with self.connection:
            self.cursor.execute("SELECT id FROM withdraws")
            last_id = 0
            for i in self.cursor.fetchall():
                last_id += 1
            last_id += 1
            return self.cursor.execute("""INSERT INTO withdraws
                (id, user_id, w_adress, amount, w_date, w_status)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                        (last_id, user_id, w_adress, amount, w_date, w_status))
        
    def withdraws_get(self, user_id):
        withdraws_data = ""
        with self.connection:
            self.cursor.execute(f"SELECT * FROM withdraws WHERE \
                                user_id = '{user_id}'")
            for i in self.cursor.fetchall():
                withdraws_data += f"\n\nНомер счёта: {i[2]}, Сумма: {i[3]}, Дата: {i[4]}, Статус: {i[5]}"
            if withdraws_data == "":
                return "У вас нет выводов"
            return withdraws_data
    
    def game_exists(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM game WHERE \
                    game_id = '{game_id}'")
            if self.cursor.fetchone():
                return True
            else:
                return False
    
    def game_status(self, game_id):
        with self.connection:
            self.cursor.execute(f"SELECT game_status FROM game WHERE \
                    game_id = '{game_id}'")
            game_status = 0
            for i in self.cursor.fetchone():
                game_status += i
            return game_status

    def game_create(self, game_id, user_id, bet_amount):
        game_status = 1
        score = 0
        with self.connection:
            return self.cursor.execute("""INSERT INTO game
                (game_id, first_user_id, bet_amount, game_status, first_user_score, second_user_score)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                        (game_id, user_id, bet_amount, game_status, score, score))
        
    def game_join(self, game_id, user_id):
        with self.connection:
            return self.cursor.execute("""UPDATE game SET second_user_id = %s, game_status = 2
                    WHERE game_id = %s""", (user_id, game_id))
    
    def game_done(self, game_id):
        with self.connection:
            return self.cursor.execute(f"DELETE FROM game WHERE \
                                       game_id = '{game_id}'")

    def game_get(self, user_id):
        games_data = ""
        with self.connection:
            self.cursor.execute(f"SELECT * FROM game")
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
            self.cursor.execute(f"SELECT * FROM game WHERE \
                                first_user_id = '{user_id}' AND game_id = '{game_id}'")
            if self.cursor.fetchone():
                self.cursor.execute(f"DELETE FROM game WHERE \
                                    game_id = '{game_id}'")
                return "Комната успешно удалена!"
            return "У вас нет прав на эту комнату!"
    
    def check_player_in_game(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT * FROM game WHERE \
                                first_user_id = '{user_id}' OR second_user_id = '{user_id}'")
            if self.cursor.fetchone():
                return True
            return False

from datetime import date, time

import psycopg2
from psycopg2 import extras
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT

db_config = {'host': DB_HOST,
             'dbname': DB_NAME,
             'user': DB_USER,
             'password': DB_PASS,
             'port': DB_PORT}


class MarketBotData:
    @staticmethod
    def add_tg_user(tg_id: int, tg_username: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (tg_id, tg_username)
            insert_script = '''INSERT INTO tg_user (tg_id, username)
                                VALUES (%s, %s)
                                ON CONFLICT (tg_id)
                                DO UPDATE SET username = Excluded.username;'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()

    @staticmethod
    def add_superadmin(tg_id: int) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (tg_id,)
            insert_script = '''INSERT INTO superadmin (tg_id) VALUES (%s)
                            ON CONFLICT (tg_id) DO NOTHING;'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()

    @staticmethod
    def get_active_gameuser_id(tg_id: int) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT game_user.gameuser_id
                                FROM game_user
                                WHERE game_user.tg_id = %s
                                AND game_user.is_active = TRUE;'''
            cursor.execute(select_script, (tg_id,))
            active_gameuser, = cursor.fetchone()
        connection.commit()
        connection.close()
        return active_gameuser

    @staticmethod
    def get_superadmin_ids() -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT superadmin.tg_id FROM superadmin ;'''
            cursor.execute(select_script)
            id_list = cursor.fetchall()
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]

    @staticmethod
    def get_game_id_by_game_key(game_key: str) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT game.game_id FROM game WHERE game_key = %s;'''
            cursor.execute(select_script, (game_key,))
            fetchone_return = cursor.fetchone()
            if fetchone_return:
                game_id, = fetchone_return
            else:
                game_id = None
        connection.commit()
        connection.close()
        return game_id

    @staticmethod
    def get_game_ids() -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT game.game_id FROM game;'''
            cursor.execute(select_script)
            id_list = cursor.fetchall()
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]


class TgUserData:
    def __init__(self, tg_id: int):
        self._tg_id = tg_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''SELECT tg_user.username
                                FROM tg_user
                                WHERE tg_id = %s;'''
            cursor.execute(select_script, (tg_id,))
            select_username, = cursor.fetchone()
        connection.commit()
        connection.close()

        self._tg_username = select_username

    def get_tg_id(self) -> int:
        return self._tg_id

    def get_tg_username(self) -> str:
        return self._tg_username


class SuperAdminData:
    def __init__(self, admin_id: int):
        self._admin_id = admin_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT superadmin.tg_id FROM superadmin
                WHERE admin_id = %s;'''
            cursor.execute(select_script, (admin_id,))
            select_tg_id, = cursor.fetchone()
        connection.commit()
        connection.close()

        self._tg_id = select_tg_id

    @staticmethod
    def create_new_game() -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_script = '''INSERT INTO game (game_name)
                                VALUES (%s) RETURNING game_id;'''
            cursor.execute(insert_script, ('new game',))
            select_game_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return select_game_id


class GameUserData:
    def __init__(self, gameuser_id: int):
        self._gameuser_id = gameuser_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT game_user.tg_id,
                    game_user.first_name,
                    game_user.last_name,
                    game_user.nickname,
                    game_user.game,
                    game_user.cash,
                    game_user.is_active
                FROM game_user WHERE gameuser_id = %s;'''
            cursor.execute(select_script, (gameuser_id,))
            tg_id, first_name, last_name, nickname, \
                game, cash, is_active = cursor.fetchone()
        connection.commit()
        connection.close()

        self._tg_id = tg_id
        self._first_name = first_name
        self._last_name = last_name
        self._nickname = nickname
        self._game = game
        self._cash = cash
        self._is_active = is_active

    def get_tg_id(self) -> int:
        return self._tg_id

    def get_first_name(self) -> str:
        return self._first_name

    def get_last_name(self) -> str:
        return self._last_name

    def get_nickname(self) -> str:
        return self._nickname

    def get_game(self) -> int:
        return self._game

    def get_cash(self) -> float:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT game_user.cash
                FROM game_user WHERE gameuser_id = %s;'''
            cursor.execute(select_script, (self._gameuser_id,))
            cash, = cursor.fetchone()
        connection.commit()
        connection.close()
        return cash

    def is_active(self) -> bool:
        return self._is_active()

    def change_first_name(self, new_first_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_first_name, self._gameuser_id)
            update_script = '''UPDATE game_user
                                SET first_name = %s
                                WHERE gameuser_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_last_name(self, new_last_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_last_name, self._gameuser_id)
            update_script = '''UPDATE game_user
                                SET last_name = %s
                                WHERE gameuser_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_nickname(self, new_nickname: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_nickname, self._gameuser_id)
            update_script = '''UPDATE game_user
                                SET nickname = %s
                                WHERE gameuser_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_cash(self, new_cash: float) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_cash, self._gameuser_id)
            update_script = '''
                UPDATE game_user SET cash = %s
                WHERE gameuser_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def activate(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    '''UPDATE game_user
                    SET is_active = FALSE
                    WHERE tg_id = %s;''',
                    (self._tg_id,))
            except Exception as e:
                print(e)
            update_script = '''
                UPDATE game_user
                SET is_active = TRUE
                WHERE gameuser_id = %s;'''
            cursor.execute(update_script, (self._gameuser_id,))
        connection.commit()
        connection.close()

    # ??
    @staticmethod
    def is_nickname_unique(nickname: str) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
            SELECT EXISTS(
               SELECT *
               FROM game_user
               WHERE nickname = %s);'''
            cursor.execute(select_script, (nickname,))
            exists, = cursor.fetchone()
        connection.commit()
        connection.close()
        return not exists

    def get_id_list_of_shares(self, company_id: int = None) -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor(cursor_factory=extras.DictCursor) as cursor:
            if company_id:
                select_script = '''
                    SELECT share.share_id FROM share
                    WHERE share.owner = %s AND share.company = %s;'''
                values = (self._gameuser_id, company_id)
            else:
                select_script = '''
                    SELECT share.share_id FROM share
                    WHERE share.owner = %s;'''
                values = (self._gameuser_id,)
            cursor.execute(select_script, values)
            id_list = cursor.fetchall()
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]


class CompanyData:
    def __init__(self, company_id: int):
        self._company_id = company_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                        SELECT company.game,
                            company.company_name,
                            company.company_ticker,
                            company.price,
                            company.effect
                        FROM company WHERE company_id = %s;'''
            cursor.execute(select_script, (company_id,))
            game, company_name, company_ticker, \
                price, effect = cursor.fetchone()
        connection.commit()
        connection.close()

        self._game = game
        self._company_name = company_name
        self._company_ticker = company_ticker

    def get_id(self) -> int:
        return self._company_id

    def get_game(self) -> int:
        return self._game

    def get_company_name(self) -> str:
        return self._company_name

    def get_ticker(self) -> str:
        return self._company_ticker

    def get_price(self) -> float:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                        SELECT company.price
                        FROM company WHERE company_id = %s;'''
            cursor.execute(select_script, (self._company_id,))
            price, = cursor.fetchone()
        connection.commit()
        connection.close()
        return price

    def get_effect(self) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT company.effect
                FROM company WHERE company_id = %s;'''
            cursor.execute(select_script, (self._company_id,))
            effect, = cursor.fetchone()
        connection.commit()
        connection.close()
        return effect

    def change_price(self, new_price: float) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_price, self._company_id)
            update_script = '''UPDATE company
                                SET price = %s
                                WHERE company_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_effect(self, new_effect: int) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_effect, self._company_id)
            update_script = '''
                UPDATE company SET effect = %s
                WHERE company_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()


class GameData:
    def __init__(self, game_id: int):
        self._game_id = game_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
            SELECT game.game_key,
               game.game_name,
               game.gs_link,
               game.timezone,
               game.start_day,
               game.end_day,
               game.open_time,
               game.close_time,
               game.is_market_open,
               game.start_price,
               game.start_cash,
               game.max_percentage,
               game.sell_factor,
               game.buy_factor,
               game.admin_contact,
               game.chart_link
            FROM game WHERE game_id = %s;'''
            cursor.execute(select_script, (game_id,))
            game_key, game_name, gs_link, timezone, start_day, end_day, \
                open_time, close_time, is_market_open, start_price, \
                start_cash, max_percentage, sell_factor, buy_factor, \
                admin_contact, chart_link = cursor.fetchone()
        connection.commit()
        connection.close()

        self._game_key = game_key
        self._game_name = game_name
        self._gs_link = gs_link
        self._timezone = timezone
        self._start_day = start_day
        self._end_day = end_day
        self._open_time = open_time
        self._close_time = close_time
        self._start_price = start_price
        self._start_cash = start_cash
        self._max_percentage = max_percentage
        self._sell_factor = sell_factor
        self._buy_factor = buy_factor
        self._admin_contact = admin_contact
        self._chart_link = chart_link

    def get_id(self) -> int:
        return self._game_id

    def get_key(self) -> str:
        return self._game_key

    def get_name(self) -> str:
        return self._game_name

    def get_gs_link(self) -> str:
        return self._gs_link

    def get_timezone(self) -> int:
        return self._timezone

    def get_start_day(self) -> date:
        return self._start_day

    def get_end_day(self) -> date:
        return self._end_day

    def get_open_time(self) -> time:
        return self._open_time

    def get_close_time(self) -> time:
        return self._close_time

    def is_market_open(self) -> bool:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT game.is_market_open
                FROM game WHERE game_id = %s;'''
            cursor.execute(select_script, (self._game_id,))
            is_market_open, = cursor.fetchone()
        connection.commit()
        connection.close()
        return is_market_open

    def get_start_price(self) -> int:
        return self._start_price

    def get_start_cash(self) -> int:
        return self._start_cash

    def get_max_percentage(self) -> float:
        return self._max_percentage

    def get_sell_factor(self) -> float:
        return self._sell_factor

    def get_buy_factor(self) -> float:
        return self._buy_factor

    def get_admin_contact(self) -> str:
        return self._admin_contact

    def get_chart_link(self) -> str:
        return self._chart_link

    def change_game_key(self, game_key: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (game_key, self._game_id)
            update_script = '''UPDATE game
                                SET game_key = %s
                                WHERE game_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_name(self, new_name: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (new_name, self._game_id)
            update_script = '''
                UPDATE game SET game_name = %s
                WHERE game_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def change_gslink(self, gs_link: str) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (gs_link, self._game_id)
            update_script = '''UPDATE game
                                SET gs_link = %s
                                WHERE game_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def open_market(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (True, self._game_id)
            update_script = '''UPDATE game
                                SET is_market_open = %s
                                WHERE game_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def close_market(self) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (False, self._game_id)
            update_script = '''
                UPDATE game SET is_market_open = %s
                WHERE game_id = %s;'''
            cursor.execute(update_script, insert_values)
        connection.commit()
        connection.close()

    def add_gameuser(self, tg_id: int) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (tg_id, self._game_id)
            insert_script = '''
                INSERT INTO game_user (tg_id, game) VALUES (%s, %s)
                RETURNING gameuser_id;'''
            cursor.execute(insert_script, insert_values)
            gameuser_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return gameuser_id

    def get_gameuser_ids(self) -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor(cursor_factory=extras.DictCursor) as cursor:
            select_script = '''
                SELECT game_user.gameuser_id
                FROM game_user WHERE game_user.game = %s;'''
            cursor.execute(select_script, (self._game_id,))
            id_list = cursor.fetchall()
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]

    def add_company(
            self,
            company_name: str,
            company_ticker: str,
            price: int) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (
                company_name, company_ticker, price, self._game_id, 0)
            insert_script = '''
                INSERT INTO company
                (company_name, company_ticker, price, game, effect)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING company_id;'''
            cursor.execute(insert_script, insert_values)
            select_company_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return select_company_id

    def get_list_of_company_ids(self) -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor(cursor_factory=extras.DictCursor) as cursor:
            select_script = '''
                SELECT company.company_id
                FROM company
                WHERE company.game = %s;'''
            cursor.execute(select_script, (self._game_id,))
            id_list = cursor.fetchall()
        connection.commit()
        connection.close()
        return [id_tuple[0] for id_tuple in id_list]

    def fill_in_game_data(self, game_data_dict: dict) -> None:
        timezone = game_data_dict['timezone']
        start_day = game_data_dict['start_day']
        end_day = game_data_dict['end_day']
        open_time = game_data_dict['open_time']
        close_time = game_data_dict['close_time']
        start_price = game_data_dict['start_price']
        start_cash = game_data_dict['start_cash']
        max_percentage = game_data_dict['max_percentage']
        sell_factor = game_data_dict['sell_factor']
        buy_factor = game_data_dict['buy_factor']
        admin_contact = game_data_dict['admin_contact']
        chart_link = game_data_dict['chart_link']

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (
                timezone, start_day, end_day, open_time, close_time,
                start_price, start_cash, max_percentage, sell_factor,
                buy_factor, admin_contact, chart_link, self._game_id)
            insert_script = '''
                UPDATE game
                SET timezone = %s,
                    start_day = %s,
                    end_day = %s,
                    open_time = %s,
                    close_time = %s,
                    start_price = %s,
                    start_cash = %s,
                    max_percentage = %s,
                    sell_factor = %s,
                    buy_factor = %s,
                    admin_contact = %s,
                    chart_link = %s
                WHERE game_id = %s;'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()

    @staticmethod
    def create_share(company_id: int, owner_gameuser_id: int) -> int:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (company_id, owner_gameuser_id)
            insert_script = '''
                INSERT INTO share (company, owner)
                VALUES (%s, %s)
                RETURNING share_id;'''
            cursor.execute(insert_script, insert_values)
            select_share_id, = cursor.fetchone()
        connection.commit()
        connection.close()
        return select_share_id

    @staticmethod
    def delete_share(share_id: int) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            delete_script = '''DELETE FROM share WHERE share_id = %s;'''
            cursor.execute(delete_script, (share_id,))
        connection.commit()
        connection.close()

    @staticmethod
    def new_transaction(date_deal: date, subject_deal_id: int, type_deal: str,
                        company_id: int, number_of_shares: int) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (
                date_deal, subject_deal_id, type_deal,
                company_id, number_of_shares)
            insert_script = '''
                INSERT INTO transactions (
                    date_deal, subject_deal, type_deal,
                    company_id, number_of_shares)
                VALUES (%s, %s, %s, %s, %s);'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()

    @staticmethod
    def get_transactions(date_deal, type_deal, company_id) -> list:
        connection = psycopg2.connect(**db_config)
        with connection.cursor(cursor_factory=extras.DictCursor) as cursor:
            insert_values = (date_deal, type_deal, company_id)
            select_script = '''
                SELECT transaction_id, date_deal, subject_deal,
                    type_deal, company_id, number_of_shares
                FROM transactions
                WHERE date_deal = %s
                AND type_deal = %s
                AND company_id = %s;'''
            cursor.execute(select_script, insert_values)
            transaction_data = cursor.fetchall()  # -> list of tuples
        connection.commit()
        connection.close()
        cols_names = (
            'transaction_id',
            'date_deal',
            'subject_deal',
            'type_deal',
            'company_id',
            'number_of_shares'
        )
        transactions_list_of_dicts = []
        for row in transaction_data:
            row_data = dict(zip(cols_names, row))
            transactions_list_of_dicts.append(row_data)
        return transactions_list_of_dicts

    @staticmethod
    def add_company_history(
            company_id: int, date_entry: date, price: float) -> None:
        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            insert_values = (company_id, date_entry, price)
            insert_script = '''
                INSERT INTO company_history (company, date_entry, price)
                VALUES (%s, %s, %s);'''
            cursor.execute(insert_script, insert_values)
        connection.commit()
        connection.close()


class ShareData:
    def __init__(self, share_id: int):
        self._share_id = share_id

        connection = psycopg2.connect(**db_config)
        with connection.cursor() as cursor:
            select_script = '''
                SELECT share.company, share.owner FROM share
                WHERE share_id = %s;'''
            cursor.execute(select_script, (share_id,))
            select_company, select_owner = cursor.fetchone()
        connection.commit()
        connection.close()

        self._company_id = select_company
        self._owner_id = select_owner

    def get_id(self) -> int:
        return self._share_id

    def get_company_id(self) -> int:
        return self._company_id

    def get_owner_id(self) -> int:
        return self._owner_id

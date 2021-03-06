from datetime import date, datetime
from time import sleep
from pygsheets import authorize, Worksheet

from config import GSHEET_SERVICE_FILE

BASE_WS = 'База'
QA_WS = 'ЧаВо'
TIMETABLE_WS = 'Режим работы биржи'
EFFECT_WS = 'Команды'
GAMEUSERS_WS = 'Регистрации'
TRADING_VOLUME_WS = 'Объем торгов'
PRICES_WS = 'Цены компаний'
PORTFOLIO_WS = 'Портфели участников'

base_value_list = [
    'timezone',
    'start_day',
    'end_day',
    'open_time',
    'close_time',
    'start_price',
    'start_cash',
    'max_percentage',
    'diversity',
    'sell_factor',
    'buy_factor',
    'admin_contact',
    'chart_link'
]

base_value_int = [
    'timezone',
    'start_price',
    'start_cash',
    'diversity',
]

base_value_float = [
    'max_percentage',
    'sell_factor',
    'buy_factor',
]


class GameSheet():
    @staticmethod
    def is_url_correct(gs_url: str) -> bool:
        try:
            client = authorize(service_file=GSHEET_SERVICE_FILE)
            sheet = client.open_by_url(gs_url)
            worksheet = sheet.worksheet_by_title(BASE_WS)
            cell_list = worksheet.find('key', matchEntireCell=True)
            if len(cell_list) == 1:
                return True
            else:
                return False
        except Exception:
            return False

    def __init__(self, gs_link: str):
        self.gs_link = gs_link

    def get_title(self) -> str:
        client = authorize(service_file=GSHEET_SERVICE_FILE)
        sheet = client.open_by_url(self.gs_link)
        return sheet.title

    def get_worksheet(self, ws_name: str) -> Worksheet:
        client = authorize(service_file=GSHEET_SERVICE_FILE)
        sheet = client.open_by_url(self.gs_link)
        worksheet = sheet.worksheet_by_title(ws_name)
        return worksheet

    def add_game_key(self, game_key: str) -> None:
        worksheet = self.get_worksheet(BASE_WS)

        key_name_cell = worksheet.find('game_key', matchEntireCell=True)[0]
        key_address = key_name_cell.address + (0, 1)
        key_cell = worksheet.cell(key_address)
        key_cell.set_value(game_key)

    def is_base_values_ready(self) -> bool:
        worksheet = self.get_worksheet(BASE_WS)

        key_name_cell = worksheet.find('key', matchEntireCell=True)[0]
        key_address = key_name_cell.address + (0, 1)
        key_cell = worksheet.cell(key_address)
        if int(key_cell.value) == 1:
            return True
        else:
            return False

    def get_base_value(self) -> dict:
        worksheet = self.get_worksheet(BASE_WS)
        result = {}
        for variable in base_value_list:
            var_name_cell = worksheet.find(variable, matchEntireCell=True)[0]
            var_address = var_name_cell.address + (0, 1)
            var_cell = worksheet.cell(var_address)
            value = var_cell.value
            if variable in base_value_int:
                value = int(value)
            elif variable in base_value_float:
                value = float(value.replace(',', '.'))
            result[variable] = value

        return result

    def get_company_names(self) -> list:
        """return list of dicts with name of companes

        Returns:
            list: [
                {
                    'name': row[0],
                    'ticker': row[1]
                },
                {...},
            ]
        """
        worksheet = self.get_worksheet(EFFECT_WS)
        result = []
        matrix = worksheet.get_values(
            start='A3',
            end='B100',
        )
        for row in matrix:
            result.append(
                {
                    'name': row[0],
                    'ticker': row[1]
                }
            )
        return result

    def get_FAQ(self) -> list:
        """return list of dicts with qustions and answers

        Returns:
            list: [
                {
                    'question': row[0],
                    'answer': row[1]
                },
                {...},
            ]
        """
        worksheet = self.get_worksheet(QA_WS)
        result = []
        matrix = worksheet.get_values(
            start='A3',
            end='B1000',
        )
        for row in matrix:
            result.append(
                {
                    'question': row[0],
                    'answer': row[1]
                }
            )
        return result

    def get_date_and_bool_from_timetable(self) -> tuple:
        """Получить дату и значение переменной is_market_open.

        Returns:
            tuple: (date_now: date, bool_: bool)
        """
        worksheet = self.get_worksheet(TIMETABLE_WS)

        date_name_cell = worksheet.find('today_date', matchEntireCell=True)[0]
        date_address = date_name_cell.address + (0, 1)
        date_cell = worksheet.cell(date_address)
        date_now = datetime.strptime(date_cell.value, '%d.%m.%Y').date()

        bool_name_cell = worksheet.find(
            'is_market_open',
            matchEntireCell=True)[0]
        bool_address = bool_name_cell.address + (0, 1)
        bool_cell = worksheet.cell(bool_address)
        bool_ = bool(int(bool_cell.value))

        return (date_now, bool_)

    def add_gameuser(
            self,
            last_name: str,
            first_name: str,
            nickname: str,
            tg_username: str) -> None:
        worksheet = self.get_worksheet(GAMEUSERS_WS)
        values_list = [
            last_name,
            first_name,
            nickname,
            tg_username
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )

    def get_effect(self, ticker: str) -> int:
        worksheet = self.get_worksheet(EFFECT_WS)
        var_name_cell = worksheet.find(ticker, matchEntireCell=True)[0]
        var_address = var_name_cell.address + (0, 1)
        var_cell = worksheet.cell(var_address)
        effect = int(var_cell.value)
        sleep(0.25)
        return effect

    def add_trading_volume(
            self,
            date: date,
            ticker: str,
            sold: int,
            bought: int):
        worksheet = self.get_worksheet(TRADING_VOLUME_WS)
        values_list = [
            str(date), ticker, bought, sold
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )
        sleep(0.25)

    def add_company_price(
            self,
            date: date,
            ticker: str,
            price: float):
        worksheet = self.get_worksheet(PRICES_WS)
        values_list = [
            str(date), ticker, price
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )
        sleep(0.25)

    def add_portfolio(
            self,
            date: date,
            nickname: str,
            size: float):
        worksheet = self.get_worksheet(PORTFOLIO_WS)
        values_list = [
            str(date), nickname, size
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )
        sleep(0.25)

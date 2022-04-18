from datetime import date
from pygsheets import authorize, Worksheet

from config import GSHEET_SERVICE_FILE

BASE_WS = 'База'
QA_WS = 'ЧаВо'
TIMETABLE_WS = 'Режим работы биржи'
EFFECT_WS = 'Эффекты'
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


class GameSheet():
    @classmethod
    def is_url_correct(gs_url: str) -> bool:
        try:
            client = authorize(service_file=GSHEET_SERVICE_FILE)
            sheet = client.open_by_url(gs_url)
            worksheet = sheet.worksheet_by_title(BASE_WS)
            cell_list = worksheet.find('key')
            if len(cell_list) == 1:
                return True
            else:
                return False
        except:
            return False

    def __init__(self, gs_link: str):
        self.gs_link = gs_link

    def get_worksheet(self, ws_name: str) -> Worksheet:
        client = authorize(service_file=GSHEET_SERVICE_FILE)
        sheet = client.open_by_url(self.gs_url)
        worksheet = sheet.worksheet_by_title(ws_name)
        return worksheet

    def get_base_value(self) -> dict:
        worksheet = self.get_worksheet(BASE_WS)
        result = {}
        for variable in base_value_list:
            var_name_cell = worksheet.find(variable)[0]
            var_address = var_name_cell.address + (0, 1)
            var_cell = worksheet.cell(var_address)
            result[variable] = var_cell.value

        return result

    def add_gameuser(
            self,
            last_name: str,
            first_name: str,
            nikname: str,
            tg_username: str) -> None:
        worksheet = self.get_worksheet(GAMEUSERS_WS)
        values_list = [
            last_name,
            first_name,
            nikname,
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
        var_name_cell = worksheet.find(ticker)[0]
        var_address = var_name_cell.address + (0, 1)
        var_cell = worksheet.cell(var_address)
        effect = var_cell.value
        return effect

    def add_trading_volume(
            self,
            date: date,
            ticker: str,
            sold: int,
            bought: int):
        worksheet = self.get_worksheet(TRADING_VOLUME_WS)
        values_list = [
            date,
            ticker,
            sold,
            bought
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )

    def add_company_price(
            self,
            date: date,
            ticker: str,
            price: float):
        worksheet = self.get_worksheet(PRICES_WS)
        values_list = [
            date,
            ticker,
            price
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )

    def add_portfolio(
            self,
            date: date,
            nikname: str,
            size: float):
        worksheet = self.get_worksheet(PRICES_WS)
        values_list = [
            date,
            nikname,
            size
        ]
        worksheet.append_table(
            values=values_list,
            start='A2',
            end=None,
            dimension='ROWS',
            overwrite=False
        )



class GameSheet():
    def __init__(self, gs_link: str):
        pass

    def get_base_value(self) -> dict:
        pass

    def add_gameuser(
            self,
            last_name: str,
            first_name: str,
            nikname: str,
            tg_username: str) -> None:
        pass

    def get_effect(self, ticker: str) -> int:
        pass

    def add_trading_volume(
            date: date,
            ticker: str,
            sold: int,
            bought: int):
        pass

    def add_company_price(
            date: date,
            ticker: str,
            price: float):
        pass

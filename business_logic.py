from __future__ import annotations
from collections import defaultdict
import weakref


class CacheMixin(object):
    __all_objects = defaultdict(dict)

    def __init__(self, key):
        self.__all_objects[self.__class__][key] = weakref.ref(self)

    @classmethod
    def get(cls, key):
        if key in cls.__all_objects[cls]:
            object_ = cls.__all_objects[cls][key]()
            if object_ is not None:
                return object_
        return cls(key)


class MarketBot():
    def __init__(self):
        pass

    def add_tg_user(self, tg_id: int, tg_username: int) -> int:
        pass

    def add_superadmin(self) -> int:
        pass

    def get_list_of_superadmins_id(self) -> list:
        pass


class TgUser(CacheMixin):
    def __init__(self, tg_id: int):
        super(TgUser, self).__init__(key=tg_id)

    def get_username(self) -> str:
        pass


class SuperAdmin(TgUser):
    def __init__(self, tg_id: int):
        super(SuperAdmin, self).__init__(tg_id=tg_id)

    def create_new_game(self) -> int:
        pass


class GameUser(TgUser):
    def __init__(self, tg_id: int):
        super(GameUser, self).__init__(tg_id=tg_id)

    def create_new_game(self) -> int:
        pass

    def get_list_of_shares(self) -> list:
        pass

    def get_portfolio_size(self) -> float:
        pass


class Game(CacheMixin):
    def __init__(self, game_id: int):
        super(Game, self).__init__(key=game_id)

    def is_market_open_now(self) -> bool:
        pass

    def add_gameuser(self) -> None:
        pass

    def add_company(self) -> None:
        pass

    def load_base_value(self) -> None:
        pass

    def create_share(self) -> None:
        pass

    def delete_share(self) -> None:
        pass

    def buy_deal(
            self,
            buyer: GameUser,
            company: Company,
            shares_number: int) -> None:
        pass

    def sell_deal(
            self,
            seller: GameUser,
            company: Company,
            shares_number: int) -> None:
        pass

    def update_prices(self) -> None:
        pass


class Company(CacheMixin):
    def __init__(self, company_id: int):
        super(Company, self).__init__(key=company_id)

    def get_price(self) -> float:
        pass


class Share(CacheMixin):
    def __init__(self, company_id: int):
        super(Company, self).__init__(key=company_id)

    def get_price(self) -> float:
        pass

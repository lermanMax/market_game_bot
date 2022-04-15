from __future__ import annotations
from collections import defaultdict
import weakref

from gs_module import GameSheet


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
        self.market_bot_data = 0
        pass

    def add_tg_user(self, tg_id: int, tg_username: int) -> TgUser:
        # self.market_bot_data.add_tg_user(
        #   tg_id=tg_id,
        #   tg_username=tg_username)

        new_tg_user = TgUser.get(tg_id)
        return new_tg_user

    def add_superadmin(self, tg_id: int) -> SuperAdmin:
        # self.market_bot_data.add_superadmin(
        #   tg_id=tg_id,
        #   tg_username=tg_username)

        new_superadmin = SuperAdmin.get(tg_id)
        return new_superadmin

    def get_list_of_superadmins_id(self) -> list:
        # SuperAdminData.add(
        pass


class TgUser(CacheMixin):
    def __init__(self, tg_id: int):
        super(TgUser, self).__init__(key=tg_id)

    def get_tg_id(self) -> int:
        pass

    def get_username(self) -> str:
        pass


class SuperAdmin(TgUser):
    def __init__(self, tg_id: int):
        super(SuperAdmin, self).__init__(tg_id=tg_id)

        self.superadmin_data = 0

    def create_new_game(self) -> int:
        game_id = self.superadmin.create_new_game()
        return game_id

    def add_name_to_game(self, game_id: int, game_name: str) -> None:
        game = Game.get(game_id)
        game.change_name(new_name=game_name)

    def add_gslink_to_game(self, game_id: int, gs_link: str) -> None:
        game = Game.get(game_id)
        game.change_gslink(gs_link=gs_link)


class GameUser(TgUser):
    def __init__(self, tg_id: int):
        super(GameUser, self).__init__(tg_id=tg_id)
        self.gameuser_data = 0

    def get_cash(self) -> float:
        return self.gameuser_data.get_cash()

    def change_cash(self, new_cash: float):
        self.gameuser_data.change_cash(new_cash=new_cash)

    def change_last_name(self, new_last_name: str) -> None:
        self.gameuser_data.change_last_name(
            new_last_name=new_last_name
        )

    def change_first_name(self, new_first_name: str) -> None:
        self.gameuser_data.change_first_name(
            new_first_name=new_first_name
        )

    def is_nikname_unique(self, nikname: str) -> bool:
        result = self.gameuser_data.is_nikname_unique(
            nikname=nikname
        )
        return result

    def change_nikname(self, new_nikname: str) -> None:
        self.gameuser_data.change_nikname(
            new_nikname=new_nikname
        )

    def get_nikname(self) -> str:
        return self.gameuser_data.get_nikname()

    def get_list_of_shares(self, company_id: int = None) -> list:
        id_list = self.gameuser_data.get_id_list_of_shares(
            company_id=company_id
        )
        shares = [Share(share_id) for share_id in id_list]
        return shares

    def get_portfolio_size(self) -> float:
        partfolio_size = self.get_cash()
        for share in self.get_list_of_shares():
            partfolio_size += share.get_price()
        return partfolio_size


class Game(CacheMixin):
    def __init__(self, game_id: int):
        super(Game, self).__init__(key=game_id)

        self.game_data = 0
        self.gs_link = 0
        self.game_sheet = GameSheet(self.gs_link)

        self._sell_factor = 0
        self._buy_factor = 0

    def change_name(new_name: str) -> None:
        pass

    def change_gslink(gs_link: str) -> None:
        pass

    def is_market_open_now(self) -> bool:
        return self.game_data.get_is_market_open()

    def update_is_market_open(self) -> None:
        pass

    def add_gameuser(self, tg_id: int) -> None:
        self.game_data.add_gameuser(tg_id)

    def add_company(self, company_name: str, company_ticker: str) -> Company:
        company_id = self.game_data.add_company(
            company_name=company_name,
            company_ticker=company_ticker,
            price=self.game_data.get_start_price()
        )
        return Company.get(company_id)

    def load_base_value(self) -> None:
        base_value_dict = self.game_sheet.get_base_value()
        self.game_data.load_base_value(
            base_value_dict=base_value_dict
        )

    def create_share(self, company_id: int, owner_gameuser_id: int) -> Share:
        share_id = self.game_data.creat_share(
            company_id=company_id,
            owner_gameuser_id=owner_gameuser_id
        )
        return Share.get(share_id)

    def delete_share(self, share_id: int) -> None:
        self.game_data.delete_share(share_id)

    def get_today(self):
        pass

    def buy_deal(
            self,
            buyer: GameUser,
            company: Company,
            shares_number: int) -> list:
        """Сделка на покупку акций

        Args:
            buyer (GameUser): _description_
            company (Company): _description_
            shares_number (int): количество акций

        Raises:
            Exception: Исключение, если не хватает денег

        Returns:
            list: список созданных акций
        """
        sum_of_deal = company.get_price() * shares_number
        if sum_of_deal > buyer.get_cash():
            raise Exception(
                f'GameUser { buyer.get_tg_id() } doesnt have enough money')
        new_cash = buyer.get_cash() - sum_of_deal
        buyer.change_cash(
            new_cash=round(new_cash, 2)
        )
        shares_list = [
            self.create_share(company.get_id, buyer.get_tg_id)
            for _ in range(shares_number)
        ]

        self.game_data.new_transaction(
            data_deal=self.get_today(),
            subject_deal_id=buyer.get_tg_id(),
            type_deal='BUY',
            company_id=company.get_id(),
            number_of_shares=shares_number
        )
        return shares_list

    def sell_deal(
            self,
            seller: GameUser,
            company: Company,
            shares_number: int) -> None:

        shares_list = seller.get_list_of_shares(company.get_id())
        if shares_number > len(shares_list):
            shares_number = len(shares_list)

        for share in shares_list:
            self.delete_share(share_id=share.get_id())

        sum_of_deal = company.get_price() * shares_number
        new_cash = seller.get_cash() + sum_of_deal
        seller.change_cash(
            new_cash=round(new_cash, 2)
        )
        self.game_data.new_transaction(
            data_deal=self.get_today(),
            subject_deal_id=seller.get_tg_id(),
            type_deal='SELL',
            company_id=company.get_id(),
            number_of_shares=shares_number
        )
        return shares_list

    def get_list_of_companyes(self) -> list:
        id_list = self.game_data.get_list_of_companyes_id()
        list_of_comapnyes = [Company.get(comapny_id) for comapny_id in id_list]
        return list_of_comapnyes

    def update_prices(self) -> None:
        companyes_list = self.get_list_of_companyes()

        for company in companyes_list:
            company = Company()
            old_price = company.get_price()
            sell_factor = self._sell_factor
            buy_factor = self._buy_factor

            sell_transactions = self.game_data.get_transactions(
                date_deal=self.get_today(),
                type_deal='SELL',
                company_id=company.get_id()
            )
            number_of_shares_sold = sum(
                [tr['number_of_shares'] for tr in sell_transactions])

            buy_transactions = self.game_data.get_transactions(
                date_deal=self.get_today(),
                type_deal='BUY',
                company_id=company.get_id()
            )
            number_of_shares_bought = sum(
                [tr['number_of_shares'] for tr in buy_transactions])

            old_effect = company.get_effect()
            new_effect = self.game_sheet.get_effect(
                ticker=company.get_ticker()
            )

            new_price = (
                old_price
                * (
                    100
                    - (number_of_shares_sold * sell_factor)
                    + (number_of_shares_bought * buy_factor)
                    + (new_effect - old_effect)
                ) / 100
            )

            company.change_price(new_price=round(new_price, 2))
            self.game_data.add_company_history(
                company_id=company.get_id(),
                date=self.get_today(),
                price=company.get_price()
            )
        return

    def update_gs_trading_volume(self) -> None:
        companyes_list = self.get_list_of_companyes()

        for company in companyes_list:
            sell_transactions = self.game_data.get_transactions(
                date_deal=self.get_today(),
                type_deal='SELL',
                company_id=company.get_id()
            )
            number_of_shares_sold = sum(
                [tr['number_of_shares'] for tr in sell_transactions])

            buy_transactions = self.game_data.get_transactions(
                date_deal=self.get_today(),
                type_deal='BUY',
                company_id=company.get_id()
            )
            number_of_shares_bought = sum(
                [tr['number_of_shares'] for tr in buy_transactions])

            self.game_sheet.add_trading_volume(
                date=self.get_today(),
                ticker=company.get_ticker(),
                sold=number_of_shares_sold,
                bought=number_of_shares_bought
            )
        return

    def update_gs_company_prices(self) -> None:
        companyes_list = self.get_list_of_companyes()

        for company in companyes_list:
            self.game_sheet.add_company_price(
                date=self.get_today(),
                ticker=company.get_ticker(),
                price=company.get_price
            )
        return

    def get_list_of_gameusers(self) -> list:
        id_list = self.game_data.get_gamusers_id()
        gameusers = [GameUser.get(tg_id) for tg_id in id_list]
        return gameusers

    def update_gs_portfolios(self) -> None:
        gamers = self.get_list_of_gameusers()
        for gameuser in gamers:
            self.game_sheet.add_portfolio(
                date=self.get_today(),
                nikname=gameuser.get_nikname(),
                patfolio_size=gameuser.get_portfolio_size()
            )


class Company(CacheMixin):
    def __init__(self, company_id: int):
        super(Company, self).__init__(key=company_id)

        self.company_data = 0

    def get_id(self) -> int:
        pass

    def get_price(self) -> float:
        return self.company_data.get_price()

    def change_price(self, new_price) -> None:
        pass

    def get_ticker(self) -> str:
        pass

    def get_effect(self) -> int:
        pass

    def change_effect(self) -> None:
        pass


class Share(CacheMixin):
    def __init__(self, share_id: int):
        super(Share, self).__init__(key=share_id)

        self.share_data = 0

    def get_id(self) -> int:
        pass

    def get_company_id(self) -> int:
        return self.share_data.get_company_id()

    def get_company(self) -> Company:
        return Company.get(self.get_company_id)

    def get_price(self) -> float:
        return self.get_company().get_price()

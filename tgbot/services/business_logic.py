from __future__ import annotations
from collections import defaultdict
import string
import random
from datetime import date, timezone, timedelta, datetime, time
from loguru import logger
from typing import List

from tgbot.services.gs_module import GameSheet
from tgbot.services.db_managing import CompanyData, GameData, GameUserData, MarketBotData, \
    ShareData, SuperAdminData, TgUserData, DoesNotExist
from tgbot.config import TIMEZONE_SERVER
from tgbot.loader import scheduler


class NotEnoughMoney(Exception):
    pass


class DealIllegal(Exception):
    pass


class CacheMixin(object):
    __all_objects = defaultdict(dict)

    def __init__(self, key):
        self.__all_objects[self.__class__][key] = self

    @classmethod
    def get(cls, key):
        if key in cls.__all_objects[cls]:
            object_ = cls.__all_objects[cls][key]
            if object_ is not None:
                return object_
        try:
            return cls(key)
        except DoesNotExist:
            cls.__all_objects[cls][key] = None
            return None
    
    @classmethod
    def clear_cache(cls):
        cls.__all_objects = defaultdict(dict)


class MarketBot():
    def __init__(self):
        self.market_bot_data = MarketBotData()

    def add_tg_user(self, tg_id: int, tg_username: str) -> None:
        if not tg_username:
            tg_username = 'none'
        self.market_bot_data.add_tg_user(
          tg_id=tg_id,
          tg_username=tg_username
        )

    def add_superadmin(self, tg_id: int):
        self.market_bot_data.add_superadmin(
          tg_id=tg_id
        )

    def get_superadmin_tg_ids(self) -> list:
        return self.market_bot_data.get_superadmin_ids()

    def get_game_by_game_key(self, game_key: str) -> Game:
        """_summary_

        Args:
            game_key (str): _description_

        Returns:
            Game: game object
            None: if game_key is wrong
        """
        game_id = self.market_bot_data.get_game_id_by_game_key(game_key)
        if game_id:
            game = Game.get(game_id)
            return game
        else:
            return None

    def get_games(self) -> List[Game]:
        result = [
            Game.get(game_id)
            for game_id in self.market_bot_data.get_game_ids()
        ]
        return result

    def get_active_gameuser_id_for(self, tg_id: int) -> int:
        return self.market_bot_data.get_active_gameuser_id(tg_id)
    
    def create_market_schedule(self, game: Game):
        logger.info(f'create_market_schedule for game: { game.game_id }')
        open_time = game.get_open_time_in_server_tz()
        open_time_str = open_time.strftime("%H:%M")
        open_hour = open_time.strftime("%H")
        open_minute = open_time.strftime("%M")

        def open_job():
            if game.game_is_ended():
                return scheduler.remove_job(f'open_{game.game_id}')
            game.job_before_open()
        scheduler.add_job(
            func=open_job,
            trigger='cron',
            hour=open_hour,
            minute=open_minute,
            id=f'open_{game.game_id}'
        )
        # schedule.every().day.at(open_time_str).do(open_job)

        close_time = game.get_close_time_in_server_tz()
        close_time_str = close_time.strftime("%H:%M")
        close_hour = close_time.strftime("%H")
        close_minute = close_time.strftime("%M")

        def close_job():
            if game.game_is_ended():
                return scheduler.remove_job(f'close_{game.game_id}')
            game.job_after_close()
        scheduler.add_job(
            func=close_job,
            trigger='cron',
            hour=close_hour,
            minute=close_minute,
            id=f'close_{game.game_id}'
        )
        # schedule.every().day.at(close_time_str).do(close_job)
    
    def check_games_and_create_schedule(self):
        for game in MarketBot().get_games():
            if not game.game_is_ended():
                self.create_market_schedule(game)
    

    def create_load_base_schedule(self, game: Game, admin_id: int):
        """load_base_value_if_its_ready"""
        def job():
            if game.load_base_value_if_its_ready():
                logger.info(f'base values soccesful loaded in game: { game.game_id }')
                game.load_companes_from_sheet()
                MarketBot().create_market_schedule(game)
                scheduler.remove_job(f'load_{game.game_id}')

        scheduler.add_job(
            func=job,
            trigger='interval',
            seconds=20,
            id=f'load_{game.game_id}'
        )


class TgUser(CacheMixin):
    def __init__(self, tg_id: int):
        super(TgUser, self).__init__(key=tg_id)
        self.tg_id = tg_id
        self.tg_data = TgUserData(tg_id)

    def get_tg_id(self) -> int:
        return self.tg_id

    def get_username(self) -> str:
        username = self.tg_data.get_tg_username()
        if not username:
            return self.get_tg_id()
        else:
            return username

    def is_blocked(self) -> bool:
        return self.tg_data.is_blocked()

    def ban(self):
        logger.info(f'ban: {self.tg_id}')
        self.tg_data.block()

    def unban(self):
        logger.info(f'unban: {self.tg_id}')
        self.tg_data.unblock()


class SuperAdmin(TgUser):
    def __init__(self, tg_id: int):
        super(SuperAdmin, self).__init__(tg_id=tg_id)

        self.superadmin_data = SuperAdminData()

    @staticmethod
    def create_new_game() -> int:
        game_id = SuperAdminData.create_new_game()
        return game_id


class GameUser(CacheMixin):
    def __init__(self, gameuser_id: int):
        self.gameuser_id = gameuser_id
        self.gameuser_data = GameUserData(self.gameuser_id)

    def get_tg_id(self) -> int:
        return self.gameuser_data.get_tg_id()

    def get_first_name(self) -> str:
        return self.gameuser_data.get_first_name()

    def get_last_name(self) -> str:
        return self.gameuser_data.get_last_name()

    def get_nickname(self) -> str:
        return self.gameuser_data.get_nickname()

    def activate(self):
        self.gameuser_data.activate()

    def get_game(self) -> Game:
        game_id = self.gameuser_data.get_game()
        return Game.get(game_id)

    def get_cash(self) -> float:
        return self.gameuser_data.get_cash()

    def change_cash(self, new_cash: float):
        self.gameuser_data.change_cash(new_cash=new_cash)

    def change_last_name(self, new_last_name: str) -> None:
        self.gameuser_data.change_last_name(
            new_last_name=new_last_name
        )
        # update data from DB
        self.gameuser_data = GameUserData(self.gameuser_id)

    def change_first_name(self, new_first_name: str) -> None:
        self.gameuser_data.change_first_name(
            new_first_name=new_first_name
        )
        # update data from DB
        self.gameuser_data = GameUserData(self.gameuser_id)

    def is_nickname_unique(self, nickname: str) -> bool:
        result = self.gameuser_data.is_nickname_unique(
            nickname=nickname
        )
        return result

    def change_nickname(self, new_nickname: str) -> None:
        self.gameuser_data.change_nickname(
            new_nickname=new_nickname
        )
        # update data from DB
        self.gameuser_data = GameUserData(self.gameuser_id)

    def get_list_of_shares(self, company_id: int = None) -> list:
        id_list = self.gameuser_data.get_id_list_of_shares(
            company_id=company_id
        )
        shares = [Share.get(share_id) for share_id in id_list]
        return shares

    def get_portfolio_size(self) -> float:
        partfolio_size = self.get_cash()
        for share in self.get_list_of_shares():
            partfolio_size += share.get_price()
        return round(partfolio_size, 2)

    def get_total_value_of_shares(self, company_id: int = None) -> float:
        total_value = sum(
            [share.get_price()
                for share in self.get_list_of_shares(company_id)]
        )
        return total_value


class Game(CacheMixin):
    @staticmethod
    def is_url_correct(gs_url: str) -> bool:
        return GameSheet.is_url_correct(gs_url)

    @staticmethod
    def key_generator(size=5, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __init__(self, game_id: int):
        super(Game, self).__init__(key=game_id)

        self.game_data = GameData(game_id)
        self.game_id = game_id

    def get_sell_factor(self) -> float:
        return self.game_data.get_sell_factor()

    def get_buy_factor(self) -> float:
        return self.game_data.get_buy_factor()

    def get_timezone(self) -> timezone:
        return timezone(timedelta(hours=self.game_data.get_timezone()))

    def get_today(self) -> date:
        today = datetime.now(self.get_timezone()).date()
        return today

    def get_time_now(self) -> datetime:
        time_now = datetime.now(self.get_timezone)
        return time_now

    def get_gametime_in_sever_timezone(self, game_time: time) -> time:
        server_tz = TIMEZONE_SERVER
        game_tz = self.game_data.get_timezone()
        hour_in_server_tz = game_time.hour - game_tz + server_tz
        if hour_in_server_tz < 0:
            hour_in_server_tz = 23 + hour_in_server_tz
        elif hour_in_server_tz > 23:
            hour_in_server_tz = hour_in_server_tz - 23

        time_in_server_tz = time(
            hour=hour_in_server_tz,
            minute=game_time.minute
        )
        return time_in_server_tz

    def get_open_time_in_server_tz(self) -> time:
        open_time = self.game_data.get_open_time()
        server_time = self.get_gametime_in_sever_timezone(open_time)
        return server_time

    def get_close_time_in_server_tz(self) -> time:
        close_time = self.game_data.get_close_time()
        server_time = self.get_gametime_in_sever_timezone(close_time)
        return server_time

    def game_is_going(self) -> bool:
        start_day = self.game_data.get_start_day()
        end_day = self.game_data.get_end_day()
        if start_day <= self.get_today() <= end_day:
            return True
        else:
            return False

    def game_is_ended(self) -> bool:
        """Проверяет, закончилась ли игра.
        Если дата конца отсутствует, то возвращает True

        Returns:
            bool: _description_
        """
        end_day = self.game_data.get_end_day()
        if not end_day:
            return True
        if self.get_today() > end_day:
            return True
        else:
            return False
    
    def get_name(self) -> str:
        return self.game_data.get_name()

    def get_gs_link(self) -> str:
        return self.game_data.get_gs_link()

    def get_game_sheet(self) -> GameSheet:
        return GameSheet(self.get_gs_link())

    def get_admin_contact(self) -> str:
        return self.game_data.get_admin_contact()

    def get_chart_link(self) -> str:
        return self.game_data.get_chart_link()

    def change_name(self, new_name: str) -> None:
        self.game_data.change_name(new_name)
        self.game_data = GameData(self.game_id)  # update data after changes

    def change_gslink(self, gs_link: str) -> None:
        self.game_data.change_gslink(gs_link)
        self.game_data = GameData(self.game_id)  # update data after changes
        gamesheet = self.get_game_sheet()
        self.change_name(new_name=gamesheet.get_title())
        new_key = str(self.game_id) + self.key_generator()
        self.game_data.change_game_key(new_key)
        self.game_data = GameData(self.game_id)  # update data after changes
        gamesheet.add_game_key(new_key)

    def is_market_open_now(self) -> bool:
        return self.game_data.is_market_open()

    def open_market(self):
        logger.info(f'Open market game: {self.game_id}')
        self.game_data.open_market()

    def close_market(self):
        logger.info(f'Close market game: {self.game_id}')
        self.game_data.close_market()

    def is_registration_open(self) -> bool:
        return self.game_data.is_registration_open()

    def open_registration(self):
        logger.info(f'Open registration game: {self.game_id}')
        self.game_data.open_registration()

    def close_registration(self):
        logger.info(f'Close registration game: {self.game_id}')
        self.game_data.close_registration()

    def update_is_market_open(self) -> bool:
        """Проверяет должна ли сегодня открыться биржа, и открывает."""
        date_now, is_open = \
            self.get_game_sheet().get_date_and_bool_from_timetable()
        if (date_now == self.get_today()) and is_open:
            self.open_market()
            return True
        else:
            self.close_market()
            return False

    def get_max_percentage(self) -> float:
        return self.game_data.get_max_percentage()

    def get_gameuser_tg_ids(self) -> list:
        tg_ids = self.game_data.get_gameuser_tg_ids()
        return tg_ids

    def gameuser_in_game(self, tg_id: int) -> bool:
        if tg_id in self.get_gameuser_tg_ids():
            return True
        else:
            return False

    def add_gameuser(self, tg_id: int) -> GameUser:
        gameuser_id = self.game_data.add_gameuser(tg_id)
        gameuser = GameUser(gameuser_id)
        gameuser.change_cash(
            new_cash=self.game_data.get_start_cash()
        )
        return gameuser

    def add_gameuser_in_sheet(self, gameuser_id: int) -> int:
        gameuser = GameUser.get(gameuser_id)
        self.get_game_sheet().add_gameuser(
            last_name=gameuser.get_last_name(),
            first_name=gameuser.get_first_name(),
            nickname=gameuser.get_nickname(),
            tg_username=TgUser.get(gameuser.get_tg_id()).get_username(),
            tg_id=gameuser.get_tg_id()
        )

    def load_base_value(self) -> bool:
        self.clear_cache()
        try:
            base_value_dict = self.get_game_sheet().get_base_value()
            logger.info(f'Loaded base value: {base_value_dict}')

            self.game_data.fill_in_game_data(base_value_dict)
            self.game_data = GameData(self.game_id)  # update data after changes
            logger.info(f'values for game {self.game_id} was loaded')
            return True 
        except Exception as e:
            logger.error(f'values_not_correct game {self.game_id}: { e }')
            return False

    def load_base_value_if_its_ready(self) -> bool:
        if self.get_game_sheet().is_base_values_ready():
            return self.load_base_value()
        else:
            logger.info('values_not_ready')
            return False

    def add_company(self, company_name: str, company_ticker: str) -> Company:
        company_id = self.game_data.add_company(
            company_name=company_name,
            company_ticker=company_ticker,
            price=self.game_data.get_start_price()
        )
        return Company.get(company_id)

    def load_companes_from_sheet(self):
        companes_names_list = self.get_game_sheet().get_company_names()
        for company_dict in companes_names_list:
            self.add_company(
                company_name=company_dict['name'],
                company_ticker=company_dict['ticker']
            )

    def create_share(self, company_id: int, owner_gameuser_id: int) -> Share:
        share_id = self.game_data.create_share(
            company_id=company_id,
            owner_gameuser_id=owner_gameuser_id
        )
        return Share.get(share_id)

    def delete_share(self, share_id: int) -> None:
        self.game_data.delete_share(share_id)

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
            raise NotEnoughMoney(
                f'GameUser { buyer.gameuser_id } doesnt have enough money')

        full_size = buyer.get_portfolio_size()
        company_in_partfolio = \
            buyer.get_total_value_of_shares(company.get_id())
        max_persentage = self.get_max_percentage() / 100
        persentage_after_deal = \
            (company_in_partfolio + sum_of_deal) / full_size
        if persentage_after_deal > max_persentage:
            raise DealIllegal(
                f'GameUser { buyer.gameuser_id } wont to many')

        new_cash = buyer.get_cash() - sum_of_deal
        buyer.change_cash(
            new_cash=round(new_cash, 2)
        )
        shares_list = [
            self.create_share(company.get_id(), buyer.gameuser_id)
            for _ in range(shares_number)
        ]

        self.game_data.new_transaction(
            date_deal=self.get_today(),
            subject_deal_id=buyer.gameuser_id,
            type_deal='BUY',
            company_id=company.get_id(),
            number_of_shares=shares_number
        )
        return shares_list

    def sell_deal(
            self,
            seller: GameUser,
            company: Company,
            shares_number: int) -> int:
        """продажа акций

        Args:
            seller (GameUser):
            company (Company):
            shares_number (int):

        Returns:
            int: реальное количество проданных акций
        """
        shares_list = seller.get_list_of_shares(company.get_id())
        if shares_number > len(shares_list):
            shares_number = len(shares_list)

        for share in shares_list[:shares_number]:
            self.delete_share(share_id=share.get_share_id())

        sum_of_deal = company.get_price() * shares_number
        new_cash = seller.get_cash() + sum_of_deal
        seller.change_cash(
            new_cash=round(new_cash, 2)
        )
        self.game_data.new_transaction(
            date_deal=self.get_today(),
            subject_deal_id=seller.gameuser_id,
            type_deal='SELL',
            company_id=company.get_id(),
            number_of_shares=shares_number
        )
        return shares_number

    def get_list_of_companyes(self) -> List[Company]:
        id_list = self.game_data.get_list_of_company_ids()
        list_of_comapnyes = [Company.get(company_id) for company_id in id_list]
        return list_of_comapnyes

    def get_list_of_actual_companyes(self) -> List[Company]:
        list_of_companyes = [
            company for company in self.get_list_of_companyes()
            if company.get_price() != 0
        ]
        return list_of_companyes

    def liquidation_companyes(self) -> None:
        companyes_list = self.get_list_of_companyes()

        for company in companyes_list:
            if company.get_price() == 0:
                continue
            if self.get_game_sheet().get_liquidation(
                ticker=company.get_ticker()
            ):
                company.change_price(new_price=0)
                logger.info(f'Company { company.get_name() } was liquidated')

    def update_prices(self) -> None:
        logger.info(f'Updating prices for game { self.game_id }')
        companyes_list = self.get_list_of_actual_companyes()

        for company in companyes_list:
            old_price = company.get_price()
            sell_factor = self.get_sell_factor()
            buy_factor = self.get_buy_factor()

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
            new_effect = self.get_game_sheet().get_effect(
                ticker=company.get_ticker()
            )
            delta_effect_price = new_effect - old_effect

            new_price = (
                old_price
                * (
                    100
                    - (number_of_shares_sold * sell_factor)
                    + (number_of_shares_bought * buy_factor)
                ) / 100
                + delta_effect_price
            )

            company.change_price(new_price=round(new_price, 2))
            company.change_effect(new_effect=new_effect)
            self.game_data.add_company_history(
                company_id=company.get_id(),
                date_entry=self.get_today(),
                price=company.get_price()
            )
        logger.info(f'Updated prices for game { self.game_id }')
        return
    
    def give_extra_cash(self) -> None:
        extra_cash = self.game_data.get_extra_cash()
        if not extra_cash:
            return
        else: 
            gameusers = self.get_list_of_gameusers()
            for gameuser in gameusers:
                cash = gameuser.get_cash()
                gameuser.change_cash(
                    new_cash=cash+extra_cash
                )
            self.game_data.change_extra_cash(0)
            self.get_game_sheet().change_extra_cash(0)
            logger.info(f'Extra cash { extra_cash } was given to gameres { self.game_id }')

    def update_gs_trading_volume(self) -> None:
        companyes_list = self.get_list_of_actual_companyes()

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

            self.get_game_sheet().add_trading_volume(
                date=self.get_today(),
                ticker=company.get_ticker(),
                sold=number_of_shares_sold,
                bought=number_of_shares_bought
            )
        logger.info(f'Trading volume for game { self.game_id } was updated')
        return

    def update_gs_company_prices(self) -> None:
        companyes_list = self.get_list_of_actual_companyes()

        for company in companyes_list:
            self.get_game_sheet().add_company_price(
                date=self.get_today(),
                ticker=company.get_ticker(),
                price=company.get_price()
            )
        logger.info(f'Prices for game { self.game_id } was updated')
        return

    def get_list_of_gameusers(self) -> list:
        id_list = self.game_data.get_gameuser_ids()
        gameusers = [GameUser.get(tg_id) for tg_id in id_list]
        return gameusers

    def update_gs_portfolios(self) -> None:
        gamers = self.get_list_of_gameusers()
        for gameuser in gamers:
            self.get_game_sheet().add_portfolio(
                date=self.get_today(),
                nickname=gameuser.get_nickname(),
                size=gameuser.get_portfolio_size()
            )
        logger.info(f'Portfolios for game { self.game_id } was updated')

    def get_FAQ(self) -> list:
        return self.get_game_sheet().get_FAQ()

    def job_before_open(self):
        self.update_is_market_open()

    def job_after_close(self):
        self.close_market()
        self.clear_cache()
        self.liquidation_companyes()
        self.update_prices()
        self.give_extra_cash()
        self.update_gs_trading_volume()
        self.update_gs_company_prices()
        self.update_gs_portfolios()


class Company(CacheMixin):
    def __init__(self, company_id: int):
        super(Company, self).__init__(key=company_id)
        self.company_id = company_id
        self.company_data = CompanyData(company_id)

    def get_id(self) -> int:
        return self.company_id

    def get_name(self) -> str:
        return self.company_data.get_company_name()

    def get_ticker(self) -> str:
        return self.company_data.get_ticker()

    def get_price(self) -> float:
        return self.company_data.get_price()

    def change_price(self, new_price: float) -> None:
        self.company_data.change_price(new_price)

    def get_effect(self) -> int:
        return self.company_data.get_effect()

    def change_effect(self, new_effect: int) -> None:
        return self.company_data.change_effect(new_effect)


class Share(CacheMixin):
    def __init__(self, share_id: int):
        super(Share, self).__init__(key=share_id)
        self.share_id = share_id
        self.share_data = ShareData(share_id)

    def get_share_id(self) -> int:
        return self.share_id

    def get_company_id(self) -> int:
        return self.share_data.get_company_id()

    def get_company(self) -> Company:
        return Company.get(self.get_company_id())

    def get_price(self) -> float:
        return self.get_company().get_price()

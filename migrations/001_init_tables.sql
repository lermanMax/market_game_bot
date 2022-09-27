DROP TABLE IF EXISTS game, tg_user, company, game_user, share, superadmin, company_history, transactions;
DROP TYPE IF EXISTS deal_id;

CREATE TABLE tg_user (
        tg_id int8 PRIMARY KEY,
        username varchar(255) NOT NULL,
        is_blocked bool NOT NULL DEFAULT FALSE
);

CREATE TABLE game (
        game_id int generated by default as identity PRIMARY KEY,
        game_key varchar(255),
        game_name varchar(255),
        gs_link varchar(255),
        timezone int,
        start_day date,
        end_day date,
        open_time time,
        close_time time,
        is_market_open bool NOT NULL DEFAULT FALSE,
        is_registration_open bool NOT NULL DEFAULT FALSE, 
        start_price int,
        start_cash int,
        max_percentage float8,
        sell_factor float8,
        buy_factor float8,
        admin_contact varchar(255),
        chart_link varchar(255)
);

CREATE TABLE game_user (
        gameuser_id int generated by default as identity PRIMARY KEY,
        tg_id int8 REFERENCES tg_user(tg_id) ON DELETE CASCADE,
        is_active bool NOT NULL DEFAULT FALSE,
        first_name varchar(255),
        last_name varchar(255),
        nickname varchar(255),
        game int REFERENCES game(game_id) ON DELETE CASCADE,
        cash float8,
        UNIQUE(tg_id, game)
);

CREATE TABLE company (
        company_id int generated by default as identity PRIMARY KEY,
        game int REFERENCES game(game_id) ON DELETE CASCADE,
        company_name varchar(255) NOT NULL,
        company_ticker varchar(255) NOT NULL,
        price float8 NOT NULL,
        effect int NOT NULL
);

CREATE TABLE share (
        share_id int generated by default as identity PRIMARY KEY,
        company int REFERENCES company(company_id) ON DELETE CASCADE,
        owner int REFERENCES game_user(gameuser_id) ON DELETE CASCADE
);

CREATE TABLE superadmin (
        admin_id int generated by default as identity PRIMARY KEY,
        tg_id int8 UNIQUE REFERENCES tg_user(tg_id) ON DELETE CASCADE
);

CREATE TABLE company_history (
        company int REFERENCES company(company_id) ON DELETE CASCADE,
        date_entry date,
        price float8
);

CREATE TYPE deal_id AS ENUM (
    'BUY',
    'SELL'
    );

CREATE TABLE transactions (
        transaction_id int generated by default as identity PRIMARY KEY,
        date_deal date,
        subject_deal int REFERENCES game_user(gameuser_id) ON DELETE CASCADE,
        type_deal deal_id NOT NULL,
        company_id int REFERENCES company(company_id) ON DELETE CASCADE,
        number_of_shares int
);

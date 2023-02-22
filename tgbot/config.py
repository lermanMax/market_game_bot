from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.

TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')
TG_ADMINS_ID = [int(i) for i in os.getenv('TG_ADMINS_ID').split(',') if i]

GSHEET_SERVICE_FILE = os.getenv('GSHEET_SERVICE_FILE')
BOT_MAILADDRESS = os.getenv('BOT_MAILADDRESS')

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_PORT = os.getenv('DB_PORT')

SUPERADMIN_PASS = os.getenv('SUPERADMIN_PASS')

TIMEZONE_SERVER = int(os.getenv('TIMEZONE_SERVER'))

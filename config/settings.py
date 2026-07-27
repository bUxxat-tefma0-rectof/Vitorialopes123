import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
MP_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/bot.db')

DEFAULT_SETTINGS = {
    'welcome_text': '',
    'welcome_image': '',
    'support_link': '',
    'support_text': '',
    'bot_version': '1.0.0',
    'pix_expiration': '15',
    'deposit_min': '2.00',
    'deposit_max': '150.00',
    'bonus_percentage': '0',
    'bonus_min_value': '0',
    'commission_percentage': '20',
    'separator': '===',
    'maintenance_mode': 'off',
    'registration_bonus': '0.00',
    'affiliate_system': 'on',
    'affiliate_points_per_recharge': '1',
    'affiliate_min_points': '500',
    'affiliate_multiplier': '0.01',
    'about_text': '',
    'terms_text': '',
}

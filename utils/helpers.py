import re
from datetime import datetime, timedelta

def format_currency(value):
    return f"R$ {float(value):.2f}"

def format_date(date, fmt='%d/%m/%Y'):
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    return date.strftime(fmt)

def format_datetime(date, fmt='%d/%m/%Y %H:%M'):
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    return date.strftime(fmt)

def validate_phone(phone):
    phone = re.sub(r'\D', '', phone)
    return 10 <= len(phone) <= 13

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_amount(amount, min_val=0, max_val=10000):
    try:
        amount = float(amount)
        return min_val <= amount <= max_val
    except:
        return False

def truncate_text(text, max_length=100):
    if len(text) > max_length:
        return text[:max_length-3] + '...'
    return text

def generate_expiration_date(days=30):
    return datetime.now() + timedelta(days=days)

def parse_product_data(text, separator='|'):
    parts = [p.strip() for p in text.split(separator)]
    if len(parts) >= 3:
        return {
            'name': parts[0],
            'price': float(parts[1]),
            'stock': int(parts[2]),
            'category': parts[3] if len(parts) > 3 else 'Geral',
            'description': parts[4] if len(parts) > 4 else ''
        }
    return None

def parse_login_data(text, separator='|'):
    parts = [p.strip() for p in text.split(separator)]
    if len(parts) >= 3:
        return {
            'service': parts[0],
            'email': parts[1],
            'password': parts[2],
            'description': parts[3] if len(parts) > 3 else '',
            'duration': parts[4] if len(parts) > 4 else '30 dias',
            'price': float(parts[5]) if len(parts) > 5 else 0
        }
    return None

def get_medal_emoji(position):
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    return medals.get(position, f'{position}.')

def sanitize_html(text):
    return text.replace('<', '&lt;').replace('>', '&gt;')

def generate_id():
    import uuid
    return uuid.uuid4().hex[:16]

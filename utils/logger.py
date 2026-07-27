import os
from datetime import datetime

class Logger:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def _write(self, level, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        date = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(self.log_dir, f'bot_{date}.log')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
        
        print(log_line.strip())
    
    def info(self, message):
        self._write('INFO', message)
    
    def error(self, message):
        self._write('ERROR', message)
    
    def warning(self, message):
        self._write('WARNING', message)
    
    def transaction(self, user_id, action, amount):
        message = f"User: {user_id} | Action: {action} | Amount: R$ {amount:.2f}"
        self._write('TRANSACTION', message)
    
    def admin_action(self, user_id, action):
        message = f"Admin: {user_id} | Action: {action}"
        self._write('ADMIN', message)
    
    def get_logs(self, date=None):
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        log_file = os.path.join(self.log_dir, f'bot_{date}.log')
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "Nenhum log encontrado."
    
    def clean_old_logs(self, days=30):
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(self.log_dir):
            if filename.startswith('bot_') and filename.endswith('.log'):
                file_path = os.path.join(self.log_dir, filename)
                file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_date < cutoff:
                    os.remove(file_path)

logger = Logger()

import os
import shutil
from datetime import datetime

class BackupService:
    def __init__(self, db_path='database/bot.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f'backup_{timestamp}.db')
        
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_file)
            self._clean_old_backups()
            return backup_file
        return None
    
    def _clean_old_backups(self, keep=10):
        files = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('backup_')], reverse=True)
        for f in files[keep:]:
            os.remove(os.path.join(self.backup_dir, f))
    
    def restore_backup(self, backup_file):
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, self.db_path)
            return True
        return False
    
    def list_backups(self):
        if not os.path.exists(self.backup_dir):
            return []
        files = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('backup_')], reverse=True)
        return files

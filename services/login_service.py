from database.db_manager import DBManager

class LoginService:
    def __init__(self):
        self.db = DBManager()
    
    def add_login(self, service, email, password, description='', duration='30 dias', price=0):
        return self.db.add_login(service, email, password, description, duration, price)
    
    def add_bulk_logins(self, data_list):
        added = 0
        for data in data_list:
            parts = data.split('|')
            if len(parts) >= 3:
                service = parts[0].strip()
                email = parts[1].strip()
                password = parts[2].strip()
                description = parts[3].strip() if len(parts) > 3 else ''
                duration = parts[4].strip() if len(parts) > 4 else '30 dias'
                price = float(parts[5].strip()) if len(parts) > 5 else 0
                self.add_login(service, email, password, description, duration, price)
                added += 1
        return added
    
    def get_available(self, service_name):
        return self.db.get_available_login(service_name)
    
    def mark_sold(self, login_id, user_id):
        self.db.mark_login_sold(login_id, user_id)
    
    def remove_by_platform(self, service_name):
        from database.models import SessionLocal, Login
        db = SessionLocal()
        count = db.query(Login).filter_by(service_name=service_name, is_sold=False).delete()
        db.commit()
        db.close()
        return count
    
    def clear_stock(self):
        from database.models import SessionLocal, Login
        db = SessionLocal()
        count = db.query(Login).filter_by(is_sold=False).delete()
        db.commit()
        db.close()
        return count
    
    def get_stock_count(self):
        from database.models import SessionLocal, Login
        db = SessionLocal()
        count = db.query(Login).filter_by(is_sold=False).count()
        db.close()
        return count
    
    def update_price_by_service(self, service_name, new_price):
        from database.models import SessionLocal, Login
        db = SessionLocal()
        count = db.query(Login).filter_by(service_name=service_name, is_sold=False).update({'price': new_price})
        db.commit()
        db.close()
        return count
    
    def update_all_prices(self, new_price):
        from database.models import SessionLocal, Login
        db = SessionLocal()
        count = db.query(Login).filter_by(is_sold=False).update({'price': new_price})
        db.commit()
        db.close()
        return count
    
    def close(self):
        self.db.close()

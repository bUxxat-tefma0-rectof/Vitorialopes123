from sqlalchemy.orm import Session
from database.models import SessionLocal, User, Product, Purchase, PixRecharge, GiftCard, Login, Setting, Alert
from datetime import datetime, timedelta
import random, string

class DBManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def close(self):
        self.db.close()
    
    def get_user(self, telegram_id):
        return self.db.query(User).filter_by(telegram_id=telegram_id).first()
    
    def create_user(self, telegram_id, username, first_name):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        bonus = float(self.get_setting('registration_bonus', '0'))
        user = User(telegram_id=telegram_id, username=username, first_name=first_name, referral_code=code, balance=bonus)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_balance(self, telegram_id):
        user = self.get_user(telegram_id)
        return user.balance if user else 0.0
    
    def add_balance(self, telegram_id, amount):
        user = self.get_user(telegram_id)
        if user:
            user.balance += amount
            user.total_recharged += amount
            self.db.commit()
    
    def subtract_balance(self, telegram_id, amount):
        user = self.get_user(telegram_id)
        if user and user.balance >= amount:
            user.balance -= amount
            user.total_spent += amount
            user.total_purchases += 1
            self.db.commit()
            return True
        return False
    
    def get_setting(self, key, default=''):
        s = self.db.query(Setting).filter_by(key=key).first()
        return s.value if s else default
    
    def set_setting(self, key, value):
        s = self.db.query(Setting).filter_by(key=key).first()
        if s:
            s.value = str(value)
        else:
            self.db.add(Setting(key=key, value=str(value)))
        self.db.commit()
    
    def get_all_settings(self):
        return {s.key: s.value for s in self.db.query(Setting).all()}
    
    def get_products(self, category=None):
        q = self.db.query(Product).filter_by(active=True)
        if category:
            q = q.filter_by(category=category)
        return q.all()
    
    def get_product(self, product_id):
        return self.db.query(Product).filter_by(id=product_id).first()
    
    def add_product(self, name, price, stock, category='', description=''):
        p = Product(name=name, price=float(price), stock=int(stock), category=category, description=description)
        self.db.add(p)
        self.db.commit()
        return p
    
    def delete_product(self, product_id):
        p = self.get_product(product_id)
        if p:
            p.active = False
            self.db.commit()
    
    def update_product(self, product_id, **kwargs):
        p = self.get_product(product_id)
        if p:
            for k, v in kwargs.items():
                setattr(p, k, v)
            self.db.commit()
    
    def decrease_stock(self, product_id):
        p = self.get_product(product_id)
        if p and p.stock > 0:
            p.stock -= 1
            p.total_sold += 1
            self.db.commit()
            return True
        return False
    
    def create_purchase(self, user_id, product_name, amount, email='', password='', link=''):
        exp = datetime.now() + timedelta(days=30)
        p = Purchase(user_id=user_id, product_name=product_name, amount=amount, email=email, password=password, activation_link=link, expiration_date=exp)
        self.db.add(p)
        self.db.commit()
        return p
    
    def get_user_purchases(self, user_id):
        return self.db.query(Purchase).filter_by(user_id=user_id).order_by(Purchase.purchase_date.desc()).all()
    
    def create_pix(self, user_id, amount, pix_id, qr_code, copy_paste, expires_at):
        p = PixRecharge(user_id=user_id, amount=amount, pix_id=pix_id, qr_code=qr_code, copy_paste=copy_paste, expires_at=expires_at)
        self.db.add(p)
        self.db.commit()
        return p
    
    def confirm_pix(self, pix_id):
        p = self.db.query(PixRecharge).filter_by(pix_id=pix_id, status='pending').first()
        if p:
            p.status = 'completed'
            p.paid_at = datetime.now()
            bonus_pct = float(self.get_setting('bonus_percentage', '0'))
            bonus_min = float(self.get_setting('bonus_min_value', '0'))
            bonus = p.amount * (bonus_pct/100) if p.amount >= bonus_min and bonus_pct > 0 else 0
            total = p.amount + bonus
            user = self.get_user(p.user_id)
            if user:
                user.balance += total
                user.total_recharged += p.amount
            self.db.commit()
            return True, total
        return False, 0
    
    def create_gift_card(self, value):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        g = GiftCard(code=code, value=float(value))
        self.db.add(g)
        self.db.commit()
        return g
    
    def redeem_gift(self, code, user_id):
        g = self.db.query(GiftCard).filter_by(code=code, is_used=False).first()
        if g:
            g.is_used = True
            g.used_by = user_id
            g.used_at = datetime.now()
            user = self.get_user(user_id)
            if user:
                user.balance += g.value
                user.gifts_redeemed += 1
            self.db.commit()
            return True
        return False
    
    def add_login(self, service, email, password, description='', duration='30 dias', price=0):
        l = Login(service_name=service, email=email, password=password, description=description, duration=duration, price=float(price))
        self.db.add(l)
        self.db.commit()
        return l
    
    def get_available_login(self, service):
        return self.db.query(Login).filter_by(service_name=service, is_sold=False).first()
    
    def mark_login_sold(self, login_id, user_id):
        l = self.db.query(Login).filter_by(id=login_id).first()
        if l:
            l.is_sold = True
            l.sold_to = user_id
            l.sold_at = datetime.now()
            self.db.commit()
    
    def get_stats(self):
        return {
            'users': self.db.query(User).count(),
            'sales': self.db.query(Purchase).count(),
            'today_sales': self.db.query(Purchase).filter(Purchase.purchase_date >= datetime.now().date()).count(),
            'total_revenue': sum(p.amount for p in self.db.query(Purchase).all()) if self.db.query(Purchase).count() > 0 else 0,
        }
    
    def get_top_products(self, limit=10):
        return self.db.query(Product).filter_by(active=True).order_by(Product.total_sold.desc()).limit(limit).all()
    
    def get_top_rechargers(self, limit=10):
        return self.db.query(User).order_by(User.total_recharged.desc()).limit(limit).all()
    
    def get_top_buyers(self, limit=10):
        return self.db.query(User).order_by(User.total_purchases.desc()).limit(limit).all()

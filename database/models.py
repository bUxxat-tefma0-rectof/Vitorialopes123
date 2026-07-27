from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    balance = Column(Float, default=0.0)
    commission_balance = Column(Float, default=0.0)
    whatsapp = Column(String)
    referral_code = Column(String, unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'))
    total_referrals = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    total_recharged = Column(Float, default=0.0)
    gifts_redeemed = Column(Integer, default=0)
    affiliate_points = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer, default=0)
    category = Column(String)
    image = Column(String)
    active = Column(Boolean, default=True)
    total_sold = Column(Integer, default=0)

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_name = Column(String)
    amount = Column(Float)
    email = Column(String)
    password = Column(String)
    activation_link = Column(String)
    expiration_date = Column(DateTime)
    purchase_date = Column(DateTime, default=datetime.now)

class PixRecharge(Base):
    __tablename__ = 'pix_recharges'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    pix_id = Column(String, unique=True)
    qr_code = Column(Text)
    copy_paste = Column(Text)
    status = Column(String, default='pending')
    expires_at = Column(DateTime)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

class GiftCard(Base):
    __tablename__ = 'gift_cards'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    value = Column(Float)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey('users.id'))
    used_at = Column(DateTime)

class Login(Base):
    __tablename__ = 'logins'
    id = Column(Integer, primary_key=True)
    service_name = Column(String)
    email = Column(String)
    password = Column(String)
    description = Column(Text)
    duration = Column(String)
    price = Column(Float)
    is_sold = Column(Boolean, default=False)
    sold_to = Column(Integer)

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(Text)

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    active = Column(Boolean, default=True)

def init_db():
    os.makedirs('database', exist_ok=True)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        from config.settings import DEFAULT_SETTINGS
        for key, value in DEFAULT_SETTINGS.items():
            if not db.query(Setting).filter_by(key=key).first():
                db.add(Setting(key=key, value=value))
        db.commit()
    finally:
        db.close()

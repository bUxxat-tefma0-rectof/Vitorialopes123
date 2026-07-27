from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Forçar SQLite
db_url = os.environ.get('DATABASE_URL', 'sqlite:///database/bot.db')
if not db_url.startswith('sqlite'):
    db_url = 'sqlite:///database/bot.db'

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ============ USUÁRIO ============
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
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    purchases = relationship('Purchase', back_populates='user')
    recharges = relationship('PixRecharge', back_populates='user')
    referrals = relationship('User', backref='referrer', remote_side=[id])
    alerts = relationship('Alert', back_populates='user')

# ============ PRODUTO ============
class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String, default='Geral')
    image = Column(String)
    active = Column(Boolean, default=True)
    total_sold = Column(Integer, default=0)
    alert_users = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ============ COMPRA ============
class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    product_name = Column(String)
    amount = Column(Float)
    email = Column(String)
    password = Column(String)
    activation_link = Column(String)
    duration = Column(String)
    expiration_date = Column(DateTime)
    purchase_date = Column(DateTime, default=datetime.now)
    status = Column(String, default='active')
    
    user = relationship('User', back_populates='purchases')

# ============ RECARGA PIX ============
class PixRecharge(Base):
    __tablename__ = 'pix_recharges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    pix_id = Column(String, unique=True)
    qr_code = Column(Text)
    copy_paste = Column(Text)
    status = Column(String, default='pending')
    expires_at = Column(DateTime)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='recharges')

# ============ GIFT CARD ============
class GiftCard(Base):
    __tablename__ = 'gift_cards'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    value = Column(Float, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    used_at = Column(DateTime)

# ============ LOGIN/ESTOQUE ============
class Login(Base):
    __tablename__ = 'logins'
    
    id = Column(Integer, primary_key=True)
    service_name = Column(String, nullable=False)
    email = Column(String)
    password = Column(String)
    description = Column(Text)
    duration = Column(String)
    price = Column(Float)
    is_sold = Column(Boolean, default=False)
    sold_to = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    sold_at = Column(DateTime)

# ============ CONFIGURAÇÕES ============
class Setting(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ============ ALERTAS ============
class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='alerts')

# ============ LOGS ============
class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    log_type = Column(String)
    user_id = Column(Integer)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# ============ ALUGUEL DE BOT ============
class BotRental(Base):
    __tablename__ = 'bot_rentals'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    client_id = Column(Integer, ForeignKey('users.id'))
    bot_token = Column(String)
    bot_name = Column(String)
    status = Column(String, default='active')
    price = Column(Float)
    start_date = Column(DateTime, default=datetime.now)
    expiration_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

# ============ INICIALIZAR BANCO ============
def init_db():
    os.makedirs('database', exist_ok=True)
    Base.metadata.create_all(engine)
    
    db = SessionLocal()
    try:
        from config.settings import DEFAULT_SETTINGS
        
        for key, value in DEFAULT_SETTINGS.items():
            existing = db.query(Setting).filter_by(key=key).first()
            if not existing:
                db.add(Setting(key=key, value=value))
        
        db.commit()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    print("✅ Tabelas criadas!")

from functools import wraps
from config.settings import ADMIN_ID
from database.db_manager import DBManager

def admin_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        if user.id != ADMIN_ID:
            await update.message.reply_text("❌ Voce nao e administrador!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def owner_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        db = DBManager()
        db_user = db.get_user(user.id)
        db.close()
        if not db_user or not db_user.is_owner:
            await update.message.reply_text("❌ Acesso negado!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def registered_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        db = DBManager()
        db_user = db.get_user(user.id)
        if not db_user:
            db_user = db.create_user(user.id, user.username, user.first_name)
        db.close()
        return await func(update, context, *args, **kwargs)
    return wrapper

def maintenance_check(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user = update.effective_user
        db = DBManager()
        maintenance = db.get_setting('maintenance_mode', 'off')
        is_admin = user.id == ADMIN_ID
        db.close()
        
        if maintenance == 'on' and not is_admin:
            await update.message.reply_text("🔧 Bot em manutencao! Volte mais tarde.")
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

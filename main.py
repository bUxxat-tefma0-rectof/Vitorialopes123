import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN
from database.models import init_db
from database.db_manager import DBManager
from handlers.client import ClientHandlers
from handlers.admin import AdminHandlers
from handlers.callback_handler import CallbackHandler
from handlers.message_handler import MessageHandler as MsgHandler
from handlers.webhook_handler import WebhookServer
from utils.logger import logger

class Bot:
    def __init__(self):
        self.db = DBManager()
        self.client_handlers = ClientHandlers()
        self.admin_handlers = AdminHandlers()
        self.callback_handler = CallbackHandler()
        self.message_handler = MsgHandler()
        self.app = None
        self.webhook = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.db.get_user(user.id)
        if not db_user:
            db_user = self.db.create_user(user.id, user.username, user.first_name)
        
        welcome = self.db.get_setting('welcome_text', '')
        text = welcome if welcome else "Bem-vindo!"
        text += f"\n\nID: {user.id}\nSaldo: R$ {db_user.balance:.2f}"
        
        keyboard = [
            [InlineKeyboardButton(self.db.get_setting('btn1_text', 'Comprar'), callback_data='menu_products')],
            [InlineKeyboardButton(self.db.get_setting('btn2_text', 'Perfil'), callback_data='menu_profile'),
             InlineKeyboardButton(self.db.get_setting('btn3_text', 'Recarregar'), callback_data='menu_recharge')],
            [InlineKeyboardButton(self.db.get_setting('btn4_text', 'Afiliado'), callback_data='menu_affiliate')],
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text.startswith('/'):
            return
        await self.start_command(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data.startswith('buy_') or data.startswith('pix_') or data.startswith('multi_buy_'):
            await self.callback_handler.handle(update, context)
        elif data.startswith('admin_'):
            await self.admin_handlers.handle_admin_callback(update, context)
        else:
            await self.client_handlers.handle_callback(update, context)
    
    def run(self):
        print("🐕 INICIANDO BOT...")
        init_db()
        print("✅ Banco pronto!")
        
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('admin', self.admin_handlers.admin_panel))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Webhook para Mercado Pago
        self.webhook = WebhookServer(self.app.bot)
        self.webhook.run(port=5000)
        
        print("✅ Bot iniciado!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    bot = Bot()
    bot.run()

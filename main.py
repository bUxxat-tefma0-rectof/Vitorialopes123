import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
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
        text += f"\n\n💠 Seus Dados:\n├👤 ID: {user.id}\n└💰 Saldo: R$ {db_user.balance:.2f}"
        
        btn1 = self.db.get_setting('btn1_text', '🛍️ Comprar Produtos')
        btn2 = self.db.get_setting('btn2_text', '👤 Meu Perfil')
        btn3 = self.db.get_setting('btn3_text', '💰 Recarregar Saldo')
        btn4 = self.db.get_setting('btn4_text', '💼 Afiliado')
        btn5 = self.db.get_setting('btn5_text', '🏆 Top Compras')
        btn6 = self.db.get_setting('btn6_text', '🔍 Pesquisar')
        btn7 = self.db.get_setting('btn7_text', '👤 Atendimento')
        btn8 = self.db.get_setting('btn8_text', 'ℹ️ Sobre')
        
        pos1 = self.db.get_setting('btn1_pos', 'full')
        pos2 = self.db.get_setting('btn2_pos', 'left')
        pos3 = self.db.get_setting('btn3_pos', 'right')
        pos4 = self.db.get_setting('btn4_pos', 'full')
        pos5 = self.db.get_setting('btn5_pos', 'left')
        pos6 = self.db.get_setting('btn6_pos', 'right')
        pos7 = self.db.get_setting('btn7_pos', 'left')
        pos8 = self.db.get_setting('btn8_pos', 'right')
        
        keyboard = []
        
        # Linha 1 - Botão 1
        row1 = [InlineKeyboardButton(btn1, callback_data='menu_products')]
        keyboard.append(row1)
        
        # Linha 2 - Botões 2 e 3
        row2 = []
        if pos2 in ['left', 'full']:
            row2.append(InlineKeyboardButton(btn2, callback_data='menu_profile'))
        if pos3 in ['right', 'full']:
            row2.append(InlineKeyboardButton(btn3, callback_data='menu_recharge'))
        if row2:
            keyboard.append(row2)
        
        # Linha 3 - Botão 4
        row3 = [InlineKeyboardButton(btn4, callback_data='menu_affiliate')]
        keyboard.append(row3)
        
        # Linha 4 - Botões 5 e 6
        row4 = []
        if pos5 in ['left', 'full']:
            row4.append(InlineKeyboardButton(btn5, callback_data='menu_top'))
        if pos6 in ['right', 'full']:
            row4.append(InlineKeyboardButton(btn6, callback_data='menu_search'))
        if row4:
            keyboard.append(row4)
        
        # Linha 5 - Botões 7 e 8
        row5 = []
        if pos7 in ['left', 'full']:
            row5.append(InlineKeyboardButton(btn7, callback_data='menu_support'))
        if pos8 in ['right', 'full']:
            row5.append(InlineKeyboardButton(btn8, callback_data='menu_about'))
        if row5:
            keyboard.append(row5)
        
        reply = InlineKeyboardMarkup(keyboard)
        
        image = self.db.get_setting('welcome_image', '')
        if image:
            try:
                await update.message.reply_photo(photo=image, caption=text, reply_markup=reply)
            except:
                await update.message.reply_text(text, reply_markup=reply)
        else:
            await update.message.reply_text(text, reply_markup=reply)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text
        
        # Se for comando, ignora aqui (os CommandHandlers cuidam)
        if text.startswith('/'):
            return
        
        # Se for admin e tiver um estado ativo, processa como admin
        if user.id == ADMIN_ID:
            state = self.admin_handlers.admin_states.get(user.id)
            if state:
                await self.admin_handlers.handle_admin_message(update, context)
                return
        
        # Se for cliente e tiver estado ativo, processa como cliente
        state = self.message_handler.states.get(user.id)
        if state:
            await self.message_handler.handle(update, context)
            return
        
        # Senão, mostra o menu principal
        await self.start_command(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data.startswith('buy_') or data.startswith('pix_') or data.startswith('multi_buy_') or data.startswith('gift_') or data.startswith('edit_'):
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
        
        self.webhook = WebhookServer(self.app.bot)
        self.webhook.run(port=5000)
        
        print("✅ Bot iniciado!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    bot = Bot()
    bot.run()

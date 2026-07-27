import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN
from database.models import init_db
from database.db_manager import DBManager
from handlers.client import ClientHandlers
from handlers.admin import AdminHandlers
from handlers.callback_handler import CallbackHandler
from handlers.message_handler import MessageHandler
from scheduler.jobs import Scheduler
from utils.logger import logger

class Bot:
    def __init__(self):
        self.db = DBManager()
        self.client_handlers = ClientHandlers()
        self.admin_handlers = AdminHandlers()
        self.callback_handler = CallbackHandler()
        self.message_handler = MessageHandler()
        self.app = None
        self.scheduler = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info(f"User {user.id} iniciou o bot")
        
        db_user = self.db.get_user(user.id)
        if not db_user:
            db_user = self.db.create_user(user.id, user.username, user.first_name)
        
        welcome = self.db.get_setting('welcome_text', '')
        image = self.db.get_setting('welcome_image', '')
        
        text = welcome if welcome else "Bem-vindo!"
        text += f"\n\n💠 Seus Dados:\n├👤 ID: {user.id}\n└💰 Saldo: R$ {db_user.balance:.2f}"
        
        keyboard = []
        btn1 = self.db.get_setting('btn1_text', '🛍️ Comprar Produtos')
        btn2 = self.db.get_setting('btn2_text', '👤 Meu Perfil')
        btn3 = self.db.get_setting('btn3_text', '💰 Recarregar')
        btn4 = self.db.get_setting('btn4_text', '💼 Afiliado')
        pos1 = self.db.get_setting('btn1_pos', 'full')
        pos2 = self.db.get_setting('btn2_pos', 'left')
        pos3 = self.db.get_setting('btn3_pos', 'right')
        pos4 = self.db.get_setting('btn4_pos', 'full')
        
        row1 = [InlineKeyboardButton(btn1, callback_data='menu_products')]
        row2 = []
        if pos2 in ['left', 'full']:
            row2.append(InlineKeyboardButton(btn2, callback_data='menu_profile'))
        if pos3 in ['right', 'full']:
            row2.append(InlineKeyboardButton(btn3, callback_data='menu_recharge'))
        row3 = [InlineKeyboardButton(btn4, callback_data='menu_affiliate')]
        
        extra_btns = [
            InlineKeyboardButton(self.db.get_setting('btn5_text', '🏆 Top'), callback_data='menu_top'),
            InlineKeyboardButton(self.db.get_setting('btn6_text', '🔍 Pesquisar'), callback_data='menu_search')
        ]
        row4 = extra_btns
        
        support_btns = [
            InlineKeyboardButton(self.db.get_setting('btn7_text', '👤 Atendimento'), callback_data='menu_support'),
            InlineKeyboardButton(self.db.get_setting('btn8_text', 'ℹ️ Sobre'), callback_data='menu_about')
        ]
        row5 = support_btns
        
        keyboard = [r for r in [row1, row2, row3, row4, row5] if r]
        reply = InlineKeyboardMarkup(keyboard)
        
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
        
        maintenance = self.db.get_setting('maintenance_mode', 'off')
        is_admin = user.id == int(__import__('config.settings').ADMIN_ID)
        
        if maintenance == 'on' and not is_admin:
            await update.message.reply_text("🔧 Bot em manutencao! Volte mais tarde.")
            return
        
        logger.info(f"Msg de {user.id}: {text[:50]}")
        
        if text.startswith('/'):
            return
        
        db_user = self.db.get_user(user.id)
        if not db_user:
            db_user = self.db.create_user(user.id, user.username, user.first_name)
        
        state = self.message_handler.states.get(user.id)
        if state:
            await self.message_handler.handle(update, context)
            return
        
        admin_state = self.admin_handlers.admin_states.get(user.id)
        if admin_state and is_admin:
            await self.admin_handlers.handle_admin_message(update, context)
            return
        
        await self.start_command(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        user = update.effective_user
        
        logger.info(f"Callback de {user.id}: {data}")
        
        if data.startswith('buy_') or data.startswith('pix_') or data.startswith('gift_') or data.startswith('edit_') or data.startswith('alert_') or data.startswith('admin_edit_') or data.startswith('admin_toggle_'):
            await self.callback_handler.handle(update, context)
        elif data.startswith('admin_'):
            await self.admin_handlers.handle_admin_callback(update, context)
        else:
            await self.client_handlers.handle_callback(update, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.admin_panel(update, context)
    
    async def pix_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_pix(update, context)
    
    async def saldo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_saldo(update, context)
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_id(update, context)
    
    async def historico_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_historico(update, context)
    
    async def afiliados_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_afiliados(update, context)
    
    async def ranking_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_ranking(update, context)
    
    async def termos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_termos(update, context)
    
    async def alertas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.client_handlers.cmd_alertas(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Erro: {context.error}")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text("❌ Ocorreu um erro. Tente novamente.")
        except:
            pass
    
    def run(self):
        print("🐕 INICIANDO BOT...")
        print("📦 Inicializando banco de dados...")
        init_db()
        print("✅ Banco de dados pronto!")
        
        self.app = Application.builder().token(BOT_TOKEN).build()
        
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('admin', self.admin_command))
        self.app.add_handler(CommandHandler('pix', self.pix_command))
        self.app.add_handler(CommandHandler('saldo', self.saldo_command))
        self.app.add_handler(CommandHandler('id', self.id_command))
        self.app.add_handler(CommandHandler('historico', self.historico_command))
        self.app.add_handler(CommandHandler('afiliados', self.afiliados_command))
        self.app.add_handler(CommandHandler('ranking', self.ranking_command))
        self.app.add_handler(CommandHandler('termos', self.termos_command))
        self.app.add_handler(CommandHandler('alertas', self.alertas_command))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_error_handler(self.error_handler)
        
        self.scheduler = Scheduler(self.app.bot)
        self.scheduler.start()
        
        print("✅ Bot iniciado!")
        logger.info("Bot iniciado com sucesso")
        
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = Bot()
    bot.run()

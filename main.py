import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
from database.models import init_db
from database.db_manager import DBManager
from utils.logger import logger

class Bot:
    def __init__(self):
        self.db = DBManager()
        self.app = None
        self.user_states = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.db.get_user(user.id) or self.db.create_user(user.id, user.username, user.first_name)
        
        welcome = self.db.get_setting('welcome_text', 'Bem-vindo!')
        text = f"{welcome}\n\n💠 Seus Dados:\n├👤 ID: {user.id}\n└💰 Saldo: R$ {db_user.balance:.2f}"
        
        btn1 = self.db.get_setting('btn1_text', '🛍️ Comprar')
        btn2 = self.db.get_setting('btn2_text', '👤 Perfil')
        btn3 = self.db.get_setting('btn3_text', '💰 Recarregar')
        btn4 = self.db.get_setting('btn4_text', '💼 Afiliado')
        btn5 = self.db.get_setting('btn5_text', '🏆 Top')
        btn6 = self.db.get_setting('btn6_text', '🔍 Pesquisar')
        btn7 = self.db.get_setting('btn7_text', '👤 Atendimento')
        btn8 = self.db.get_setting('btn8_text', 'ℹ️ Sobre')
        
        keyboard = [
            [InlineKeyboardButton(btn1, callback_data='m1')],
            [InlineKeyboardButton(btn2, callback_data='m2'), InlineKeyboardButton(btn3, callback_data='m3')],
            [InlineKeyboardButton(btn4, callback_data='m4')],
            [InlineKeyboardButton(btn5, callback_data='m5'), InlineKeyboardButton(btn6, callback_data='m6')],
            [InlineKeyboardButton(btn7, callback_data='m7'), InlineKeyboardButton(btn8, callback_data='m8')],
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        d = q.data
        
        if d == 'm1': await q.edit_message_text("🛍️ Catálogo em breve!")
        elif d == 'm2': await q.edit_message_text("👤 Perfil em breve!")
        elif d == 'm3': await q.edit_message_text("💰 Recarregar em breve!")
        elif d == 'm4': await q.edit_message_text("💼 Afiliado em breve!")
        elif d == 'm5': await q.edit_message_text("🏆 Top em breve!")
        elif d == 'm6': await q.edit_message_text("🔍 Pesquisar em breve!")
        elif d == 'm7': await q.edit_message_text("👤 Atendimento em breve!")
        elif d == 'm8': await q.edit_message_text("ℹ️ Sobre em breve!")
    
    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text.startswith('/'):
            return
        await self.start(update, context)
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != ADMIN_ID:
            await update.message.reply_text("❌ Não é admin!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📝 Texto Boas-vindas", callback_data='adm_welcome')],
            [InlineKeyboardButton("🖼️ Imagem", callback_data='adm_image')],
            [InlineKeyboardButton("🔘 Botão 1", callback_data='adm_btn1')],
            [InlineKeyboardButton("🔘 Botão 2", callback_data='adm_btn2')],
            [InlineKeyboardButton("🔘 Botão 3", callback_data='adm_btn3')],
            [InlineKeyboardButton("🔘 Botão 4", callback_data='adm_btn4')],
            [InlineKeyboardButton("📐 Posições", callback_data='adm_pos')],
        ]
        await update.message.reply_text("👑 *PAINEL ADMIN*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        d = q.data
        user = update.effective_user
        
        if user.id != ADMIN_ID:
            return
        
        if d == 'adm_welcome':
            self.user_states[user.id] = 'welcome'
            await q.edit_message_text("📝 Envie o novo texto de boas-vindas:")
        elif d == 'adm_image':
            self.user_states[user.id] = 'image'
            await q.edit_message_text("🖼️ Envie a URL da imagem:")
        elif d == 'adm_btn1':
            self.user_states[user.id] = 'btn1'
            await q.edit_message_text("🔘 Envie o texto do Botão 1:")
        elif d == 'adm_btn2':
            self.user_states[user.id] = 'btn2'
            await q.edit_message_text("🔘 Envie o texto do Botão 2:")
        elif d == 'adm_btn3':
            self.user_states[user.id] = 'btn3'
            await q.edit_message_text("🔘 Envie o texto do Botão 3:")
        elif d == 'adm_btn4':
            self.user_states[user.id] = 'btn4'
            await q.edit_message_text("🔘 Envie o texto do Botão 4:")
        elif d == 'adm_pos':
            self.user_states[user.id] = 'pos'
            await q.edit_message_text("📐 Envie as posições (8):\nfull|left|right|full|left|right|left|right")
    
    async def admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != ADMIN_ID:
            return
        
        text = update.message.text
        state = self.user_states.get(user.id)
        
        if not state:
            return
        
        if state == 'welcome':
            self.db.set_setting('welcome_text', text)
            await update.message.reply_text("✅ Texto salvo!")
        elif state == 'image':
            self.db.set_setting('welcome_image', text)
            await update.message.reply_text("✅ Imagem salva!")
        elif state == 'btn1':
            self.db.set_setting('btn1_text', text)
            await update.message.reply_text("✅ Botão 1 salvo!")
        elif state == 'btn2':
            self.db.set_setting('btn2_text', text)
            await update.message.reply_text("✅ Botão 2 salvo!")
        elif state == 'btn3':
            self.db.set_setting('btn3_text', text)
            await update.message.reply_text("✅ Botão 3 salvo!")
        elif state == 'btn4':
            self.db.set_setting('btn4_text', text)
            await update.message.reply_text("✅ Botão 4 salvo!")
        elif state == 'pos':
            parts = text.split('|')
            for i, p in enumerate(parts[:8], 1):
                if p.strip() in ['full', 'left', 'right']:
                    self.db.set_setting(f'btn{i}_pos', p.strip())
            await update.message.reply_text("✅ Posições salvas!")
        
        self.user_states.pop(user.id, None)
    
    def run(self):
        print("🐕 INICIANDO...")
        init_db()
        print("✅ Pronto!")
        
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.app.add_handler(CommandHandler('start', self.start))
        self.app.add_handler(CommandHandler('admin', self.admin_panel))
        self.app.add_handler(CallbackQueryHandler(self.on_callback, pattern='^m'))
        self.app.add_handler(CallbackQueryHandler(self.admin_callback, pattern='^adm'))
        self.app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_message), group=1)
        self.app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND, self.on_message), group=2)
        
        print("✅ Online!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    bot = Bot()
    bot.run()

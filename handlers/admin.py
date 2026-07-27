from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database.db_manager import DBManager
from config.settings import ADMIN_ID

class AdminHandlers:
    def __init__(self):
        self.db = DBManager()
        self.admin_states = {}
    
    def register(self, app):
        app.add_handler(CommandHandler('admin', self.admin_panel))
        app.add_handler(CallbackQueryHandler(self.handle_admin_callback, pattern='^admin_'))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_message))
    
    def is_admin(self, user_id):
        return user_id == ADMIN_ID
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.is_admin(user.id):
            await update.message.reply_text("Voce nao e administrador!")
            return
        
        db = DBManager()
        stats = db.get_stats()
        version = db.get_setting('bot_version', '1.0.0')
        maintenance = db.get_setting('maintenance_mode', 'off')
        
        text = "DASHBOARD\n\n"
        text += f"Versao: {version}\n"
        text += f"Users: {stats['users']}\n"
        text += f"Vendas total: {stats['sales']}\n"
        text += f"Vendas hoje: {stats['today_sales']}\n"
        text += f"Receita total: R$ {stats['total_revenue']:.2f}\n"
        text += f"Manutencao: {maintenance}"
        
        keyboard = [
            [InlineKeyboardButton("CONFIGURACOES", callback_data='admin_config')],
            [InlineKeyboardButton("ACOES", callback_data='admin_actions')],
            [InlineKeyboardButton("TRANSACOES", callback_data='admin_transactions')],
            [InlineKeyboardButton("ATUALIZACOES", callback_data='admin_updates')]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        db.close()
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user
        
        if not self.is_admin(user.id):
            return
        
        db = DBManager()
        
        try:
            if data == 'admin_config':
                await self.show_config_menu(query)
            elif data == 'admin_config_general':
                await self.show_general_config(query, db)
            elif data == 'admin_config_admins':
                await self.show_admin_config(query, db)
            elif data == 'admin_config_affiliate':
                await self.show_affiliate_config(query, db)
            elif data == 'admin_config_users':
                await self.show_users_config(query, db)
            elif data == 'admin_config_pix':
                await self.show_pix_config(query, db)
            elif data == 'admin_config_logins':
                await self.show_logins_config(query, db)
            elif data == 'admin_actions':
                await self.show_actions_menu(query)
            elif data == 'admin_actions_add_product':
                await self.ask_product_data(query, user.id)
            elif data == 'admin_actions_broadcast':
                await self.ask_broadcast(query, user.id)
            elif data == 'admin_actions_gift':
                await self.ask_gift_value(query, user.id)
            elif data == 'admin_transactions':
                await self.show_transactions_menu(query)
            elif data == 'admin_back':
                await self.admin_panel_back(query, db)
        finally:
            db.close()
    
    async def show_config_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("Configuracoes Gerais", callback_data='admin_config_general')],
            [InlineKeyboardButton("Configurar Admins", callback_data='admin_config_admins')],
            [InlineKeyboardButton("Configurar Afiliados", callback_data='admin_config_affiliate')],
            [InlineKeyboardButton("Configurar Usuarios", callback_data='admin_config_users')],
            [InlineKeyboardButton("Configurar PIX", callback_data='admin_config_pix')],
            [InlineKeyboardButton("Configurar Logins", callback_data='admin_config_logins')],
            [InlineKeyboardButton("Voltar", callback_data='admin_back')]
        ]
        await query.edit_message_text("CONFIGURACOES:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_general_config(self, query, db):
        settings = db.get_all_settings()
        text = "CONFIGURACOES GERAIS\n\n"
        text += f"Suporte: {settings.get('support_link', '')}\n"
        text += f"Versao: {settings.get('bot_version', '')}\n"
        text += f"Manutencao: {settings.get('maintenance_mode', 'off')}"
        
        keyboard = [
            [InlineKeyboardButton("Mudar Texto Boas-vindas", callback_data='admin_edit_welcome')],
            [InlineKeyboardButton("Mudar Imagem", callback_data='admin_edit_image')],
            [InlineKeyboardButton("Mudar Suporte", callback_data='admin_edit_support')],
            [InlineKeyboardButton("Mudar Botoes", callback_data='admin_edit_buttons')],
            [InlineKeyboardButton("Ligar/Desligar Manutencao", callback_data='admin_toggle_maintenance')],
            [InlineKeyboardButton("Voltar", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_admin_config(self, query, db):
        admins = db.db.query(User).filter_by(is_admin=True).all() if hasattr(db, 'db') else []
        text = f"ADMINS: {len(admins)}\n\nComandos:\n/addadmin ID\n/removeadmin ID\n/listadmins"
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='admin_config')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_affiliate_config(self, query, db):
        settings = db.get_all_settings()
        text = "CONFIGURAR AFILIADOS\n\n"
        text += f"Sistema: {settings.get('affiliate_system', 'on')}\n"
        text += f"Comissao: {settings.get('commission_percentage', '20')}%\n"
        text += f"Pontos por recarga: {settings.get('affiliate_points_per_recharge', '1')}\n"
        text += f"Minimo pontos: {settings.get('affiliate_min_points', '500')}\n"
        text += f"Multiplicador: {settings.get('affiliate_multiplier', '0.01')}"
        
        keyboard = [
            [InlineKeyboardButton("Ligar/Desligar Sistema", callback_data='admin_toggle_affiliate')],
            [InlineKeyboardButton("Mudar Comissao", callback_data='admin_edit_commission')],
            [InlineKeyboardButton("Voltar", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_users_config(self, query, db):
        text = "CONFIGURAR USUARIOS\n\nComandos:\n/broadcast MSG\n/searchuser ID\n/setbonus VALOR"
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='admin_config')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_pix_config(self, query, db):
        settings = db.get_all_settings()
        text = "CONFIGURAR PIX\n\n"
        text += f"Token: {'Configurado' if settings.get('mp_access_token') else 'Nao configurado'}\n"
        text += f"Minimo: R$ {settings.get('deposit_min', '2.00')}\n"
        text += f"Maximo: R$ {settings.get('deposit_max', '150.00')}\n"
        text += f"Expiracao: {settings.get('pix_expiration', '15')} min\n"
        text += f"Bonus: {settings.get('bonus_percentage', '0')}%"
        
        keyboard = [
            [InlineKeyboardButton("Mudar Token", callback_data='admin_edit_mp_token')],
            [InlineKeyboardButton("Mudar Minimo", callback_data='admin_edit_deposit_min')],
            [InlineKeyboardButton("Mudar Maximo", callback_data='admin_edit_deposit_max')],
            [InlineKeyboardButton("Mudar Expiracao", callback_data='admin_edit_expiration')],
            [InlineKeyboardButton("Voltar", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_logins_config(self, query, db):
        text = "CONFIGURAR LOGINS\n\nComandos:\n/addlogin SERVICO|EMAIL|SENHA|DESCRICAO|DURACAO|PRECO\n/removelogin SERVICO|EMAIL\n/zerarestoque"
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='admin_config')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_actions_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("Adicionar Produto", callback_data='admin_actions_add_product')],
            [InlineKeyboardButton("Transmitir", callback_data='admin_actions_broadcast')],
            [InlineKeyboardButton("Criar Gift Card", callback_data='admin_actions_gift')],
            [InlineKeyboardButton("Voltar", callback_data='admin_back')]
        ]
        await query.edit_message_text("ACOES:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_product_data(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_product_data'
        await query.edit_message_text("Envie os dados do produto:\n\nFormato: NOME|PRECO|ESTOQUE|CATEGORIA|DESCRICAO\n\nExemplo: Netflix|15.00|50|Streaming|Acesso 30 dias")
    
    async def ask_broadcast(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_broadcast'
        await query.edit_message_text("Envie a mensagem para transmitir a todos os usuarios:")
    
    async def ask_gift_value(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_gift_value'
        await query.edit_message_text("Envie o valor do Gift Card:")
    
    async def show_transactions_menu(self, query):
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='admin_back')]]
        await query.edit_message_text("TRANSACOES:\n\nEm breve...", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def admin_panel_back(self, query, db):
        stats = db.get_stats()
        text = f"DASHBOARD\n\nUsers: {stats['users']}\nVendas: {stats['sales']}\nReceita: R$ {stats['total_revenue']:.2f}"
        keyboard = [
            [InlineKeyboardButton("CONFIGURACOES", callback_data='admin_config')],
            [InlineKeyboardButton("ACOES", callback_data='admin_actions')],
            [InlineKeyboardButton("TRANSACOES", callback_data='admin_transactions')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.is_admin(user.id):
            return
        
        text = update.message.text
        db = DBManager()
        
        try:
            state = self.admin_states.get(user.id)
            
            if state == 'awaiting_product_data':
                parts = text.split('|')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    price = float(parts[1].strip())
                    stock = int(parts[2].strip())
                    category = parts[3].strip() if len(parts) > 3 else 'Geral'
                    description = parts[4].strip() if len(parts) > 4 else ''
                    db.add_product(name, price, stock, category, description)
                    await update.message.reply_text(f"✅ Produto '{name}' adicionado!")
                    self.admin_states.pop(user.id, None)
                else:
                    await update.message.reply_text("Formato invalido. Use: NOME|PRECO|ESTOQUE|CATEGORIA|DESCRICAO")
            
            elif state == 'awaiting_broadcast':
                users = db.db.query(User).all() if hasattr(db, 'db') else []
                count = 0
                for u in users:
                    try:
                        await context.bot.send_message(u.telegram_id, text)
                        count += 1
                    except:
                        pass
                await update.message.reply_text(f"✅ Transmissao concluida! Enviado para {count} usuarios.")
                self.admin_states.pop(user.id, None)
            
            elif state == 'awaiting_gift_value':
                try:
                    value = float(text)
                    gift = db.create_gift_card(value)
                    await update.message.reply_text(f"✅ Gift Card criado!\nCodigo: {gift.code}\nValor: R$ {value:.2f}")
                    self.admin_states.pop(user.id, None)
                except:
                    await update.message.reply_text("Valor invalido.")
        finally:
            db.close()

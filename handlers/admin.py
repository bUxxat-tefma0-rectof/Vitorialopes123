from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database.db_manager import DBManager
from config.settings import ADMIN_ID
from services.gift_service import GiftService
from services.login_service import LoginService
from services.affiliate_service import AffiliateService
from utils.logger import logger

class AdminHandlers:
    def __init__(self):
        self.db = DBManager()
        self.admin_states = {}
        self.gift_service = GiftService()
        self.login_service = LoginService()
        self.affiliate_service = AffiliateService()
    
    def register(self, app):
        app.add_handler(CommandHandler('admin', self.admin_panel))
        app.add_handler(CallbackQueryHandler(self.handle_admin_callback, pattern='^admin_'))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_message))
    
    def is_admin(self, user_id):
        return user_id == ADMIN_ID
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ Você não é um administrador!")
            return
        
        db = DBManager()
        stats = db.get_stats()
        version = db.get_setting('bot_version', '1.0.0')
        maintenance = db.get_setting('maintenance_mode', 'off')
        vip = db.get_setting('vip_status', 'Não')
        
        text = (
            f"📊 *DASHBOARD*\n\n"
            f"⏰ Vencimento: 26/11/2074 (Faltam 18031 dias!)\n"
            f"👑 Vip: {vip}\n"
            f"📱 Software version: V4.1.0\n\n"
            f"📈 *Métricas do business*\n"
            f"👥 Users: {stats['users']}\n"
            f"💰 Receita total: R$ {stats.get('total_revenue', 0):.2f}\n"
            f"💰 Receita de hoje: R$ {stats.get('today_revenue', 0):.2f}\n"
            f"🛒 Vendas total: {stats['sales']}\n"
            f"🛒 Vendas hoje: {stats.get('today_sales', 0)}\n\n"
            f"Use os botões abaixo para me configurar"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
            [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
            [InlineKeyboardButton("📊 TRANSAÇÕES", callback_data='admin_transactions')],
            [InlineKeyboardButton("🔄 ATUALIZAÇÕES", callback_data='admin_updates')]
        ]
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
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
            elif data == 'admin_config_search':
                await self.show_search_config(query, db)
            elif data == 'admin_actions':
                await self.show_actions_menu(query)
            elif data == 'admin_actions_add_product':
                await self.ask_product_data(query, user.id)
            elif data == 'admin_actions_broadcast':
                await self.ask_broadcast(query, user.id)
            elif data == 'admin_actions_gift':
                await self.ask_gift_value(query, user.id)
            elif data == 'admin_actions_add_login':
                await self.ask_login_data(query, user.id)
            elif data == 'admin_actions_remove_login':
                await self.ask_remove_login(query, user.id)
            elif data == 'admin_actions_clear_stock':
                await self.confirm_clear_stock(query)
            elif data == 'admin_actions_clear_stock_confirm':
                count = self.login_service.clear_stock()
                await query.edit_message_text(f"✅ {count} logins removidos!")
            elif data == 'admin_transactions':
                await self.show_transactions_menu(query)
            elif data == 'admin_updates':
                await self.show_updates(query)
            elif data == 'admin_back':
                await self.admin_panel_back(query, db)
            elif data.startswith('admin_edit_'):
                await self.handle_edit_field(query, data, user.id)
            elif data.startswith('admin_toggle_'):
                await self.handle_toggle(query, data, db)
        finally:
            db.close()
    
    async def show_config_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS", callback_data='admin_config_general')],
            [InlineKeyboardButton("👑 CONFIGURAR ADMINS", callback_data='admin_config_admins')],
            [InlineKeyboardButton("💼 CONFIGURAR AFILIADOS", callback_data='admin_config_affiliate')],
            [InlineKeyboardButton("👥 CONFIGURAR USUARIOS", callback_data='admin_config_users')],
            [InlineKeyboardButton("💳 CONFIGURAR PIX", callback_data='admin_config_pix')],
            [InlineKeyboardButton("📦 CONFIGURAR LOGINS", callback_data='admin_config_logins')],
            [InlineKeyboardButton("🔍 CONFIGURAR PESQUISA", callback_data='admin_config_search')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await query.edit_message_text("⚙️ *MENU DE CONFIGURAÇÕES DO BOT*\n\nSelecione uma opção:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_general_config(self, query, db):
        settings = db.get_all_settings()
        text = (
            "⚙️ *CONFIGURAÇÕES GERAIS*\n\n"
            f"📁 DESTINO DAS LOG'S: {settings.get('log_channel', 'Nao configurado')}\n"
            f"🔗 LINK DO SUPORTE ATUAL: {settings.get('support_link', 'Nao configurado')}\n"
            f"🔤 % SEPARADOR: {settings.get('separator', '===')}\n\n"
            "Use os botões abaixo para configurar:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 RENOVAR PLANO", callback_data='admin_edit_renew')],
            [InlineKeyboardButton("♻️ REINICIAR BOT", callback_data='admin_edit_restart')],
            [InlineKeyboardButton(f"🔧 MANUTENÇÃO ({settings.get('maintenance_mode', 'off')})", callback_data='admin_toggle_maintenance')],
            [InlineKeyboardButton("📞 MUDAR SUPORTE", callback_data='admin_edit_support')],
            [InlineKeyboardButton("🔤 MUDAR SEPARADOR", callback_data='admin_edit_separator')],
            [InlineKeyboardButton("📁 MUDAR DESTINO LOG", callback_data='admin_edit_log_channel')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_admin_config(self, query, db):
        text = (
            "👑 *PAINEL CONFIGURAR ADMIN*\n\n"
            "Administradores: 1\n\n"
            "Use os botões abaixo para fazer as alterações necessárias"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR ADM", callback_data='admin_edit_add_admin')],
            [InlineKeyboardButton("➖ REMOVER ADM", callback_data='admin_edit_remove_admin')],
            [InlineKeyboardButton("📋 LISTA DE ADM", callback_data='admin_edit_list_admin')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_affiliate_config(self, query, db):
        settings = db.get_all_settings()
        
        text = (
            "💼 *CONFIGURAR AFILIADOS*\n\n"
            f"🔢 PONTOS MINIMO PRA SALDO: {settings.get('affiliate_min_points', '500')}\n"
            f"✖️ MULTIPLICADOR: {settings.get('affiliate_multiplier', '0.01')}\n\n"
            "📊 *SISTEMA DE INDICAÇÃO*\n"
            "Ao clicar, altera o status do sistema de indicação.\n\n"
            f"🟢 VERDE = On\n"
            f"🔴 VERMELHO = Off\n\n"
            "📥 *PONTOS POR RECARGA*\n"
            "Quantidade de pontos que o usuário ganha por recarga do afiliado.\n\n"
            "🎯 *PONTOS MINIMO PARA CONVERTER*\n"
            "Quantidade mínima de pontos para converter em saldo.\n\n"
            "💰 *MULTIPLICADOR PARA CONVERTER*\n"
            "Multiplicador de pontos para saldo na hora de converter.\n"
            "Ex: 0.01 com 500 pontos = R$ 5,00 de saldo."
        )
        
        keyboard = [
            [InlineKeyboardButton(f"SISTEMA DE INDICAÇÃO ({settings.get('affiliate_system', 'on')})", callback_data='admin_toggle_affiliate')],
            [InlineKeyboardButton("📥 PONTOS POR RECARGA", callback_data='admin_edit_affiliate_points')],
            [InlineKeyboardButton("🎯 PONTOS MINIMO PARA CONVERTER", callback_data='admin_edit_affiliate_min_points')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_users_config(self, query, db):
        settings = db.get_all_settings()
        text = (
            "👥 *CONFIGURAR USUÁRIOS*\n\n"
            "📤 *TRANSMITIR A TODOS*\n"
            "Após clicar, envie o texto que quer transmitir.\n\n"
            "🔍 *PESQUISAR USUÁRIO*\n"
            "Se este usuário estiver registrado no bot, vai abrir as configurações de edição.\n"
            "Você poderá editar o saldo, ver o histórico de compras, e todas as informações dele.\n\n"
            "🎁 *BÔNUS DE REGISTRO*\n"
            f"Bônus atual: R$ {settings.get('registration_bonus', '0.00')}\n"
            "Bônus de registro é o valor que cada usuário novo ganhará apenas por se registrar."
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 TRANSMITIR A TODOS", callback_data='admin_actions_broadcast')],
            [InlineKeyboardButton("🔍 PESQUISAR USUÁRIO", callback_data='admin_edit_search_user')],
            [InlineKeyboardButton("🎁 BONUS DE REGISTRO", callback_data='admin_edit_registration_bonus')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_pix_config(self, query, db):
        settings = db.get_all_settings()
        text = (
            "💳 *CONFIGURAR PIX*\n\n"
            f"🔑 TOKEN MERCADO PAGO: {'Configurado' if settings.get('mp_access_token') else 'Não configurado'}\n"
            f"📥 DEPÓSITO MÍNIMO: R$ {settings.get('deposit_min', '1.00')}\n"
            f"📤 DEPÓSITO MÁXIMO: R$ {settings.get('deposit_max', '150.00')}\n"
            f"⏰ TEMPO DE EXPIRAÇÃO: {settings.get('pix_expiration', '15')} Minutos\n"
            f"🎁 BÔNUS DE DEPÓSITO: {settings.get('bonus_percentage', '0')}%\n"
            f"📊 DEPÓSITO MÍNIMO PARA BÔNUS: R$ {settings.get('bonus_min_value', '0.00')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("💠 PIX MANUAL", callback_data='admin_edit_pix_manual')],
            [InlineKeyboardButton("🤖 PIX AUTOMATICO", callback_data='admin_edit_pix_auto')],
            [InlineKeyboardButton("🔑 MUDAR TOKEN", callback_data='admin_edit_mp_token')],
            [InlineKeyboardButton("📥 MUDAR DEPOSITO MIN", callback_data='admin_edit_deposit_min')],
            [InlineKeyboardButton("📤 MUDAR DEPOSITO MAX", callback_data='admin_edit_deposit_max')],
            [InlineKeyboardButton("⏰ MUDAR TEMPO DE EXPIRAÇÃO", callback_data='admin_edit_expiration')],
            [InlineKeyboardButton("🎁 MUDAR BONUS", callback_data='admin_edit_bonus')],
            [InlineKeyboardButton("📊 MUDAR MIN PARA BONUS", callback_data='admin_edit_bonus_min')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_logins_config(self, query, db):
        stock_count = self.login_service.get_stock_count()
        text = (
            "📦 *CONFIGURAR LOGINS*\n\n"
            f"📊 LOGINS NO ESTOQUE: {stock_count}\n\n"
            "➕ *ADICIONAR LOGIN*\n"
            "Formato: NOME|EMAIL|SENHA|DESCRICAO|DURACAO|PRECO\n"
            "Use === como separador\n\n"
            "➖ *REMOVER LOGIN*\n"
            "Envie o serviço e o email separados por ===\n"
            "Ex: NETFLIX===EMAIL\n\n"
            "🗑️ *REMOVER POR PLATAFORMA*\n"
            "Envie o nome da plataforma\n\n"
            "💣 *ZERAR ESTOQUE*\n"
            "Remove todos os logins"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR LOGIN", callback_data='admin_actions_add_login')],
            [InlineKeyboardButton("➖ REMOVER LOGIN", callback_data='admin_actions_remove_login')],
            [InlineKeyboardButton("🗑️ REMOVER POR PLATAFORMA", callback_data='admin_edit_remove_platform')],
            [InlineKeyboardButton("📊 ESTOQUE DETALHADO", callback_data='admin_edit_stock_detail')],
            [InlineKeyboardButton("💣 ZERAR ESTOQUE", callback_data='admin_actions_clear_stock')],
            [InlineKeyboardButton("💰 MUDAR VALOR DO SERVIÇO", callback_data='admin_edit_service_price')],
            [InlineKeyboardButton("💵 MUDAR VALOR DE TODOS", callback_data='admin_edit_all_prices')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_search_config(self, query, db):
        text = (
            "🔍 *PAINEL DE CONFIGURAÇÃO DA PESQUISA DE SERVIÇOS*\n\n"
            "📸 IMAGENS SALVAS: 0\n"
            "🔍 SISTEMA PESQUISA: ON"
        )
        
        keyboard = [
            [InlineKeyboardButton("📸 ADICIONAR IMAGEM", callback_data='admin_edit_add_image')],
            [InlineKeyboardButton("🗑️ REMOVER IMAGEM", callback_data='admin_edit_remove_image')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_actions_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("📦 Adicionar Produto", callback_data='admin_actions_add_product')],
            [InlineKeyboardButton("📤 Transmitir a Todos", callback_data='admin_actions_broadcast')],
            [InlineKeyboardButton("🎁 Criar Gift Card", callback_data='admin_actions_gift')],
            [InlineKeyboardButton("📦 Adicionar Login", callback_data='admin_actions_add_login')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await query.edit_message_text("🔧 *AÇÕES*\n\nSelecione uma ação:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_transactions_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("📊 Relatório de Vendas", callback_data='admin_edit_sales_report')],
            [InlineKeyboardButton("💳 Relatório de Recargas", callback_data='admin_edit_recharge_report')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await query.edit_message_text("📊 *TRANSAÇÕES*\n\nSelecione o relatório:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_updates(self, query):
        text = (
            "🔄 *ATUALIZAÇÕES*\n\n"
            "📱 Versão: V4.1.0\n"
            "📅 Última atualização: 26/11/2024\n\n"
            "✅ Todas as funcionalidades operacionais."
        )
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def ask_product_data(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_product_data'
        await query.edit_message_text(
            "📦 *Adicionar Produto*\n\nEnvie os dados no formato:\n\n`NOME|PRECO|ESTOQUE|CATEGORIA|DESCRICAO`\n\nExemplo:\n`Netflix|15.00|50|Streaming|Acesso 30 dias`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='admin_actions')]]),
            parse_mode='Markdown'
        )
    
    async def ask_broadcast(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_broadcast'
        await query.edit_message_text(
            "📤 *Transmitir Mensagem*\n\nEnvie a mensagem que deseja enviar para todos os usuários:\n\n_Digite 'cancelar' para sair_",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='admin_actions')]]),
            parse_mode='Markdown'
        )
    
    async def ask_gift_value(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_gift_value'
        await query.edit_message_text(
            "🎁 *Criar Gift Card*\n\nEnvie o valor do Gift Card:\n\nExemplo: 50",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='admin_actions')]]),
            parse_mode='Markdown'
        )
    
    async def ask_login_data(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_login_data'
        await query.edit_message_text(
            "📦 *Adicionar Login*\n\nEnvie os dados no formato:\n\n`SERVICO|EMAIL|SENHA|DESCRICAO|DURACAO|PRECO`\n\nUse | como separador",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='admin_actions')]]),
            parse_mode='Markdown'
        )
    
    async def ask_remove_login(self, query, user_id):
        self.admin_states[user_id] = 'awaiting_remove_login'
        await query.edit_message_text(
            "➖ *Remover Login*\n\nEnvie o serviço e email separados por |\n\nExemplo: `NETFLIX|email@email.com`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data='admin_actions')]]),
            parse_mode='Markdown'
        )
    
    async def confirm_clear_stock(self, query):
        keyboard = [
            [InlineKeyboardButton("⚠️ SIM, ZERAR TUDO", callback_data='admin_actions_clear_stock_confirm')],
            [InlineKeyboardButton("❌ Cancelar", callback_data='admin_config_logins')]
        ]
        await query.edit_message_text(
            "⚠️ *TEM CERTEZA?*\n\nIsso irá remover TODOS os logins do estoque!\n\nEsta ação não pode ser desfeita.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_edit_field(self, query, data, user_id):
        field = data.replace('admin_edit_', '')
        self.admin_states[user_id] = f'admin_editing_{field}'
        
        prompts = {
            'support': "Envie o novo link/nome de suporte:",
            'separator': "Envie o novo caractere separador:",
            'log_channel': "Envie o ID do canal de logs:",
            'mp_token': "Envie o novo Token do Mercado Pago:",
            'deposit_min': "Envie o novo valor mínimo de depósito:",
            'deposit_max': "Envie o novo valor máximo de depósito:",
            'expiration': "Envie o novo tempo de expiração (minutos):",
            'bonus': "Envie o novo percentual de bônus (%):",
            'bonus_min': "Envie o novo valor mínimo para bônus:",
            'commission': "Envie o novo percentual de comissão:",
            'registration_bonus': "Envie o novo bônus de registro:",
            'affiliate_points': "Envie a quantidade de pontos por recarga:",
            'affiliate_min_points': "Envie o mínimo de pontos para converter:",
            'welcome_text': "Envie o novo texto de boas-vindas:",
            'welcome_image': "Envie a URL da nova imagem:",
            'about_text': "Envie o novo texto Sobre:",
            'terms_text': "Envie os novos termos de uso:",
            'btn1_text': "Envie o texto do botão 1:",
            'btn2_text': "Envie o texto do botão 2:",
            'btn3_text': "Envie o texto do botão 3:",
            'btn4_text': "Envie o texto do botão 4:",
            'service_price': "Envie o nome do serviço e novo valor separados por |:\nEx: NETFLIX|12.00",
            'all_prices': "Envie o novo valor para TODOS os serviços:",
            'remove_platform': "Envie o nome da plataforma para remover:",
            'add_admin': "Envie o ID do Telegram do novo admin:",
            'remove_admin': "Envie o ID do Telegram do admin a remover:",
            'search_user': "Envie o ID do Telegram do usuário:",
            'add_image': "Envie a URL da imagem:",
            'remove_image': "Envie o nome da imagem a remover:",
        }
        
        msg = prompts.get(field, f"Envie o novo valor para {field}:")
        await query.edit_message_text(msg)
    
    async def handle_toggle(self, query, data, db):
        field = data.replace('admin_toggle_', '')
        current = db.get_setting(field, 'off')
        new_value = 'on' if current == 'off' else 'off'
        db.set_setting(field, new_value)
        await query.edit_message_text(f"✅ {field} alterado para: {new_value}")
    
    async def admin_panel_back(self, query, db):
        stats = db.get_stats()
        text = (
            "📊 *DASHBOARD*\n\n"
            f"👥 Users: {stats['users']}\n"
            f"💰 Receita: R$ {stats.get('total_revenue', 0):.2f}\n"
            f"🛒 Vendas: {stats['sales']}"
        )
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
            [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
            [InlineKeyboardButton("📊 TRANSAÇÕES", callback_data='admin_transactions')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
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
                else:
                    await update.message.reply_text("❌ Formato invalido. Use: NOME|PRECO|ESTOQUE|CATEGORIA|DESCRICAO")
                self.admin_states.pop(user.id, None)
            
            elif state == 'awaiting_broadcast':
                if text.lower() != 'cancelar':
                    from database.models import SessionLocal, User
                    session = SessionLocal()
                    users = session.query(User).all()
                    count = 0
                    for u in users:
                        try:
                            await context.bot.send_message(u.telegram_id, text)
                            count += 1
                        except:
                            pass
                    session.close()
                    await update.message.reply_text(f"✅ Transmissão concluída! Enviado para {count} usuários.")
                else:
                    await update.message.reply_text("❌ Transmissão cancelada.")
                self.admin_states.pop(user.id, None)
            
            elif state == 'awaiting_gift_value':
                try:
                    value = float(text)
                    gift = self.gift_service.create_gift(value)
                    await update.message.reply_text(f"✅ Gift Card criado!\n🎁 Código: `{gift.code}`\n💰 Valor: R$ {value:.2f}", parse_mode='Markdown')
                except:
                    await update.message.reply_text("❌ Valor invalido.")
                self.admin_states.pop(user.id, None)
            
            elif state == 'awaiting_login_data':
                parts = text.split('|')
                if len(parts) >= 3:
                    service = parts[0].strip()
                    email = parts[1].strip()
                    password = parts[2].strip()
                    description = parts[3].strip() if len(parts) > 3 else ''
                    duration = parts[4].strip() if len(parts) > 4 else '30 dias'
                    price = float(parts[5].strip()) if len(parts) > 5 else 0
                    self.login_service.add_login(service, email, password, description, duration, price)
                    await update.message.reply_text(f"✅ Login adicionado para {service}!")
                else:
                    await update.message.reply_text("❌ Formato invalido. Use: SERVICO|EMAIL|SENHA|DESCRICAO|DURACAO|PRECO")
                self.admin_states.pop(user.id, None)
            
            elif state == 'awaiting_remove_login':
                parts = text.split('|')
                if len(parts) >= 2:
                    service = parts[0].strip()
                    email = parts[1].strip()
                    count = self.login_service.remove_by_platform(service)
                    await update.message.reply_text(f"✅ {count} logins removidos de {service}!")
                else:
                    await update.message.reply_text("❌ Formato invalido. Use: SERVICO|EMAIL")
                self.admin_states.pop(user.id, None)
            
            elif state and state.startswith('admin_editing_'):
                field = state.replace('admin_editing_', '')
                
                field_map = {
                    'support': 'support_link',
                    'separator': 'separator',
                    'log_channel': 'log_channel',
                    'mp_token': 'mp_access_token',
                    'deposit_min': 'deposit_min',
                    'deposit_max': 'deposit_max',
                    'expiration': 'pix_expiration',
                    'bonus': 'bonus_percentage',
                    'bonus_min': 'bonus_min_value',
                    'commission': 'commission_percentage',
                    'registration_bonus': 'registration_bonus',
                    'affiliate_points': 'affiliate_points_per_recharge',
                    'affiliate_min_points': 'affiliate_min_points',
                    'welcome_text': 'welcome_text',
                    'welcome_image': 'welcome_image',
                    'about_text': 'about_text',
                    'terms_text': 'terms_text',
                    'btn1_text': 'btn1_text',
                    'btn2_text': 'btn2_text',
                    'btn3_text': 'btn3_text',
                    'btn4_text': 'btn4_text',
                }
                
                if field == 'service_price':
                    parts = text.split('|')
                    if len(parts) >= 2:
                        service = parts[0].strip()
                        price = float(parts[1].strip())
                        count = self.login_service.update_price_by_service(service, price)
                        await update.message.reply_text(f"✅ {count} logins de {service} atualizados para R$ {price:.2f}!")
                    else:
                        await update.message.reply_text("❌ Formato: SERVICO|PRECO")
                
                elif field == 'all_prices':
                    try:
                        price = float(text)
                        count = self.login_service.update_all_prices(price)
                        await update.message.reply_text(f"✅ {count} logins atualizados para R$ {price:.2f}!")
                    except:
                        await update.message.reply_text("❌ Valor invalido.")
                
                elif field == 'remove_platform':
                    count = self.login_service.remove_by_platform(text.strip())
                    await update.message.reply_text(f"✅ {count} logins removidos de {text.strip()}!")
                
                elif field == 'add_admin':
                    try:
                        admin_id = int(text)
                        from database.models import SessionLocal, User
                        session = SessionLocal()
                        user = session.query(User).filter_by(telegram_id=admin_id).first()
                        if user:
                            user.is_admin = True
                            session.commit()
                            await update.message.reply_text(f"✅ Admin adicionado: {admin_id}")
                        else:
                            await update.message.reply_text("❌ Usuário não encontrado.")
                        session.close()
                    except:
                        await update.message.reply_text("❌ ID invalido.")
                
                elif field == 'search_user':
                    try:
                        user_id = int(text)
                        from database.models import SessionLocal, User
                        session = SessionLocal()
                        u = session.query(User).filter_by(telegram_id=user_id).first()
                        if u:
                            info = (
                                f"👤 *Usuário Encontrado*\n\n"
                                f"🆔 ID: {u.telegram_id}\n"
                                f"👤 Nome: {u.first_name}\n"
                                f"💰 Saldo: R$ {u.balance:.2f}\n"
                                f"💼 Comissão: R$ {u.commission_balance:.2f}\n"
                                f"🛒 Compras: {u.total_purchases}\n"
                                f"💳 Recarregado: R$ {u.total_recharged:.2f}"
                            )
                            await update.message.reply_text(info, parse_mode='Markdown')
                        else:
                            await update.message.reply_text("❌ Usuário não encontrado.")
                        session.close()
                    except:
                        await update.message.reply_text("❌ ID invalido.")
                
                elif field_map.get(field):
                    db.set_setting(field_map[field], text)
                    await update.message.reply_text(f"✅ {field} atualizado com sucesso!")
                
                else:
                    await update.message.reply_text(f"✅ Comando processado!")
                
                self.admin_states.pop(user.id, None)
        
        finally:
            db.close()

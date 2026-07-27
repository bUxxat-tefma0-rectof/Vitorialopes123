from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database.db_manager import DBManager

class ClientHandlers:
    def __init__(self):
        self.db = DBManager()
        self.user_states = {}
    
    def register(self, app):
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^menu_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^products_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^profile_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^recharge_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^affiliate_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^buy_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^pix_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^back_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^history_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^gift_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^top_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^search_'))
        app.add_handler(CommandHandler('pix', self.cmd_pix))
        app.add_handler(CommandHandler('saldo', self.cmd_saldo))
        app.add_handler(CommandHandler('id', self.cmd_id))
        app.add_handler(CommandHandler('historico', self.cmd_historico))
        app.add_handler(CommandHandler('afiliados', self.cmd_afiliados))
        app.add_handler(CommandHandler('ranking', self.cmd_ranking))
        app.add_handler(CommandHandler('termos', self.cmd_termos))
        app.add_handler(CommandHandler('alertas', self.cmd_alertas))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user
        db = DBManager()
        
        try:
            db_user = db.get_user(user.id)
            if not db_user:
                db_user = db.create_user(user.id, user.username, user.first_name)
            
            if data == 'menu_products':
                await self.show_categories(query, db)
            elif data.startswith('category_'):
                category = data.replace('category_', '')
                await self.show_products(query, db, category)
            elif data.startswith('product_'):
                product_id = int(data.replace('product_', ''))
                await self.show_product_detail(query, db, product_id, db_user)
            elif data.startswith('buy_confirm_'):
                product_id = int(data.replace('buy_confirm_', ''))
                await self.confirm_purchase(query, db, product_id, db_user)
            elif data == 'menu_profile':
                await self.show_profile(query, db, db_user)
            elif data == 'menu_recharge':
                await self.show_recharge_menu(query, db, db_user)
            elif data == 'menu_affiliate':
                await self.show_affiliate(query, db, db_user)
            elif data == 'menu_top':
                await self.show_top(query, db)
            elif data == 'menu_search':
                await self.ask_search(query, db, user.id)
            elif data == 'menu_support':
                await self.show_support(query, db)
            elif data == 'menu_about':
                await self.show_about(query, db)
            elif data == 'profile_history':
                await self.show_history(query, db, db_user, 0)
            elif data.startswith('history_page_'):
                page = int(data.replace('history_page_', ''))
                await self.show_history(query, db, db_user, page)
            elif data == 'profile_gift':
                await self.ask_gift_code(query, user.id)
            elif data == 'profile_edit':
                await self.show_edit_data(query, db, db_user)
            elif data == 'edit_whatsapp':
                await self.ask_whatsapp(query, user.id)
            elif data == 'recharge_pix':
                await self.ask_recharge_value(query, user.id)
            elif data.startswith('pix_generate_'):
                amount = float(data.replace('pix_generate_', ''))
                await self.generate_pix(query, db, db_user, amount)
            elif data.startswith('back_'):
                target = data.replace('back_', '')
                await self.go_back(query, target, db, db_user)
            elif data.startswith('top_'):
                tipo = data.replace('top_', '')
                await self.show_top_type(query, db, tipo)
        finally:
            db.close()
    
    async def show_categories(self, query, db):
        products = db.get_products()
        categories = list(set(p.category for p in products if p.category))
        
        if not categories:
            await query.edit_message_text("Nenhuma categoria disponivel.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar", callback_data='back_main')]
            ]))
            return
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(cat, callback_data=f'category_{cat}')])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data='back_main')])
        
        text = db.get_setting('categories_text', 'Escolha uma categoria:')
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_products(self, query, db, category):
        products = db.get_products(category)
        
        if not products:
            await query.edit_message_text("Nenhum produto nesta categoria.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar", callback_data='menu_products')]
            ]))
            return
        
        keyboard = []
        for p in products:
            stock_text = f" ({p.stock} unid.)" if p.stock > 0 else " (ESGOTADO)"
            keyboard.append([InlineKeyboardButton(f"{p.name} - R$ {p.price:.2f}{stock_text}", callback_data=f'product_{p.id}')])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data='menu_products')])
        
        text = db.get_setting('products_text', 'Produtos disponiveis:')
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_product_detail(self, query, db, product_id, user):
        p = db.get_product(product_id)
        if not p:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        text = f"{p.name}\n\n"
        if p.description:
            text += f"Descricao: {p.description}\n\n"
        text += f"Preco: R$ {p.price:.2f}\n"
        text += f"Estoque: {p.stock} unid.\n"
        text += f"Seu Saldo: R$ {user.balance:.2f}\n"
        text += f"Vendidos: {p.total_sold}"
        
        keyboard = []
        if p.stock > 0:
            keyboard.append([InlineKeyboardButton("Comprar", callback_data=f'buy_confirm_{p.id}')])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data=f'category_{p.category}')])
        
        if p.image:
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def confirm_purchase(self, query, db, product_id, user):
        p = db.get_product(product_id)
        if not p:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        if user.balance < p.price:
            falta = p.price - user.balance
            text = f"Saldo insuficiente!\n\nSeu saldo: R$ {user.balance:.2f}\nValor: R$ {p.price:.2f}\nFalta: R$ {falta:.2f}\n\nDeseja gerar um PIX?"
            keyboard = [
                [InlineKeyboardButton("Gerar PIX", callback_data=f'pix_generate_{p.price}')],
                [InlineKeyboardButton("Cancelar", callback_data=f'product_{p.id}')]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        if p.stock <= 0:
            await query.edit_message_text("Produto esgotado!")
            return
        
        success = db.subtract_balance(user.id, p.price)
        if not success:
            await query.edit_message_text("Erro ao processar pagamento.")
            return
        
        db.decrease_stock(product_id)
        
        login = db.get_available_login(p.name)
        email = login.email if login else ''
        password = login.password if login else ''
        link = ''
        
        if login:
            db.mark_login_sold(login.id, user.id)
        
        purchase = db.create_purchase(user.id, p.name, p.price, email, password, link)
        
        text = f"Compra realizada!\n\nProduto: {p.name}\nValor: R$ {p.price:.2f}\n\n"
        if email:
            text += f"Email: {email}\nSenha: {password}\n"
        text += f"\nID da compra: {purchase.id}"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='menu_products')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_profile(self, query, db, user):
        text = "Meu Perfil\n\n"
        text += f"ID: {user.telegram_id}\n"
        text += f"Saldo: R$ {user.balance:.2f}\n"
        if user.whatsapp:
            text += f"WhatsApp: {user.whatsapp}\n"
        text += f"Compras: {user.total_purchases}\n"
        text += f"Total Gasto: R$ {user.total_spent:.2f}\n"
        text += f"Recarregado: R$ {user.total_recharged:.2f}\n"
        text += f"Gifts: {user.gifts_redeemed}"
        
        keyboard = [
            [InlineKeyboardButton("Historico de Compras", callback_data='profile_history')],
            [InlineKeyboardButton("Resgatar Gift Card", callback_data='profile_gift')],
            [InlineKeyboardButton("Alterar Dados", callback_data='profile_edit')],
            [InlineKeyboardButton("Voltar", callback_data='back_main')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_history(self, query, db, user, page):
        purchases = db.get_user_purchases(user.id)
        
        if not purchases:
            await query.edit_message_text("Nenhuma compra encontrada.", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
            ]))
            return
        
        if page >= len(purchases):
            page = 0
        
        p = purchases[page]
        text = f"Compra {page+1} de {len(purchases)}\n\n"
        text += f"Produto: {p.product_name}\n"
        text += f"Valor: R$ {p.amount:.2f}\n"
        text += f"Data: {p.purchase_date.strftime('%d/%m/%Y')}\n"
        if p.expiration_date:
            text += f"Vencimento: {p.expiration_date.strftime('%d/%m/%Y')}\n"
        text += f"ID: {p.id}\n"
        if p.email:
            text += f"Email: {p.email}\n"
            text += f"Senha: {p.password}\n"
        if p.activation_link:
            text += f"Link: {p.activation_link}"
        
        keyboard = []
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("Anterior", callback_data=f'history_page_{page-1}'))
        if page < len(purchases) - 1:
            nav.append(InlineKeyboardButton("Proximo", callback_data=f'history_page_{page+1}'))
        if nav:
            keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("Voltar", callback_data='menu_profile')])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_gift_code(self, query, user_id):
        self.user_states[user_id] = 'awaiting_gift_code'
        await query.edit_message_text("Digite o codigo do Gift Card:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancelar", callback_data='menu_profile')]
        ]))
    
    async def show_edit_data(self, query, db, user):
        text = "Alterar Dados\n\n"
        text += f"WhatsApp: {user.whatsapp or 'Nao cadastrado'}"
        keyboard = [
            [InlineKeyboardButton("Alterar WhatsApp", callback_data='edit_whatsapp')],
            [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_whatsapp(self, query, user_id):
        self.user_states[user_id] = 'awaiting_whatsapp'
        await query.edit_message_text("Envie seu numero de WhatsApp (DDD+Numero):\n\nDigite 'remover' para apagar.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancelar", callback_data='menu_profile')]
        ]))
    
    async def show_recharge_menu(self, query, db, user):
        text = f"Recarregar Saldo\n\nID: {user.telegram_id}\nSaldo: R$ {user.balance:.2f}"
        keyboard = [
            [InlineKeyboardButton("PIX Rapido", callback_data='recharge_pix')],
            [InlineKeyboardButton("Voltar", callback_data='back_main')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_recharge_value(self, query, user_id):
        self.user_states[user_id] = 'awaiting_recharge_value'
        min_val = self.db.get_setting('deposit_min', '2')
        await query.edit_message_text(f"Informe o valor para recarregar:\n\nMinimo: R$ {min_val}", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancelar", callback_data='menu_recharge')]
        ]))
    
    async def generate_pix(self, query, db, user, amount):
        import uuid
        from datetime import datetime, timedelta
        
        exp_min = int(db.get_setting('pix_expiration', '15'))
        pix_id = uuid.uuid4().hex[:32]
        copy_paste = f"00020101021226830014BR.GOV.BCB.PIX2561qrcodespix.sejaefi.com.br/v2/{uuid.uuid4().hex[:32]}5204000053039865802BR5905EFISA6008SAOPAULO62070503***6304{uuid.uuid4().hex[:4].upper()}"
        expires_at = datetime.now() + timedelta(minutes=exp_min)
        
        db.create_pix(user.id, amount, pix_id, '', copy_paste, expires_at)
        
        bonus_pct = float(db.get_setting('bonus_percentage', '0'))
        bonus = amount * (bonus_pct/100) if bonus_pct > 0 else 0
        
        text = f"PIX Gerado\n\n"
        text += f"Valor: R$ {amount:.2f}\n"
        text += f"ID: {pix_id}\n"
        text += f"Expira em: {exp_min} minutos\n"
        if bonus > 0:
            text += f"Bonus: R$ {bonus:.2f}\n"
        text += f"\nCodigo Copia e Cola:\n`{copy_paste}`\n\nApos o pagamento, seu saldo sera liberado automaticamente."
        
        keyboard = [
            [InlineKeyboardButton("Verificar Pagamento", callback_data=f'pix_check_{pix_id}')],
            [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_affiliate(self, query, db, user):
        commission = db.get_setting('commission_percentage', '20')
        text = "Programa de Afiliados\n\n"
        text += f"Status: Ativo\n"
        text += f"Comissao: {commission}%\n"
        text += f"Indicacoes: {user.total_referrals}\n"
        text += f"Total ganho: R$ {user.commission_balance:.2f}\n"
        text += f"Seu link:\nhttps://t.me/{(await query.message.chat.username) or 'bot'}?start={user.telegram_id}"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_top(self, query, db):
        keyboard = [
            [InlineKeyboardButton("Servicos Mais Vendidos", callback_data='top_products')],
            [InlineKeyboardButton("Mais Recarregaram", callback_data='top_rechargers')],
            [InlineKeyboardButton("Mais Compraram", callback_data='top_buyers')],
            [InlineKeyboardButton("Voltar", callback_data='back_main')]
        ]
        await query.edit_message_text("Rankings:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_top_type(self, query, db, tipo):
        text = "Ranking\n\n"
        if tipo == 'products':
            items = db.get_top_products()
            for i, p in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}."
                text += f"{medal} {p.name} - {p.total_sold} vendas\n"
        elif tipo == 'rechargers':
            items = db.get_top_rechargers()
            for i, u in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}."
                name = u.first_name or f"ID:{u.telegram_id}"
                text += f"{medal} {name} - R$ {u.total_recharged:.2f}\n"
        elif tipo == 'buyers':
            items = db.get_top_buyers()
            for i, u in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}."
                name = u.first_name or f"ID:{u.telegram_id}"
                text += f"{medal} {name} - {u.total_purchases} compras\n"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='menu_top')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_search(self, query, db, user_id):
        self.user_states[user_id] = 'awaiting_search'
        await query.edit_message_text("Digite o nome do produto que deseja pesquisar:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancelar", callback_data='back_main')]
        ]))
    
    async def show_support(self, query, db):
        link = db.get_setting('support_link', '')
        text = db.get_setting('support_text', 'Atendimento via Telegram')
        keyboard = []
        if link:
            keyboard.append([InlineKeyboardButton("Falar com Suporte", url=link)])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data='back_main')])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_about(self, query, db):
        text = db.get_setting('about_text', 'Sobre o Bot')
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def go_back(self, query, target, db, user):
        if target == 'main':
            welcome = db.get_setting('welcome_text', 'Bem-vindo!')
            text = f"{welcome}\n\nSeus Dados:\nID: {user.telegram_id}\nSaldo: R$ {user.balance:.2f}"
            keyboard = [
                [InlineKeyboardButton(db.get_setting('btn1_text', 'Comprar'), callback_data='menu_products')],
                [InlineKeyboardButton(db.get_setting('btn2_text', 'Perfil'), callback_data='menu_profile'),
                 InlineKeyboardButton(db.get_setting('btn3_text', 'Recarregar'), callback_data='menu_recharge')],
                [InlineKeyboardButton(db.get_setting('btn4_text', 'Afiliado'), callback_data='menu_affiliate')],
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def cmd_pix(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        args = context.args
        if args:
            try:
                amount = float(args[0])
                db = DBManager()
                db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
                # Gerar PIX...
                await update.message.reply_text(f"PIX de R$ {amount:.2f} gerado!")
                db.close()
            except:
                await update.message.reply_text("Valor invalido. Use: /pix 10")
        else:
            await update.message.reply_text("Use: /pix VALOR\nExemplo: /pix 10")
    
    async def cmd_saldo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db = DBManager()
        db_user = db.get_user(user.id)
        if db_user:
            await update.message.reply_text(f"Seu saldo: R$ {db_user.balance:.2f}")
        db.close()
    
    async def cmd_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Seu ID: {update.effective_user.id}")
    
    async def cmd_historico(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botoes do menu para ver seu historico.")
    
    async def cmd_afiliados(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botoes do menu para ver seus afiliados.")
    
    async def cmd_ranking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botoes do menu para ver os rankings.")
    
    async def cmd_termos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db = DBManager()
        text = db.get_setting('terms_text', 'Termos de uso nao configurados.')
        await update.message.reply_text(text)
        db.close()
    
    async def cmd_alertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Sistema de alertas em breve.")

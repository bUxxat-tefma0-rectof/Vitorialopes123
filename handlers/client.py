from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database.db_manager import DBManager
from datetime import datetime

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
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^multi_buy_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^category_'))
        app.add_handler(CallbackQueryHandler(self.handle_callback, pattern='^product_'))
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
            elif data.startswith('buy_multi_'):
                product_id = int(data.replace('buy_multi_', ''))
                await self.show_multi_buy(query, db, product_id, db_user)
            elif data.startswith('multi_buy_confirm_'):
                parts = data.replace('multi_buy_confirm_', '').split('_')
                product_id = int(parts[0])
                quantity = int(parts[1])
                await self.process_multi_buy(query, db, product_id, quantity, db_user)
            elif data.startswith('multi_buy_custom_'):
                product_id = int(data.replace('multi_buy_custom_', ''))
                self.user_states[user.id] = f'awaiting_multi_buy_{product_id}'
                await query.edit_message_text(
                    "Digite a quantidade desejada:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]
                    ])
                )
            elif data.startswith('multi_buy_execute_'):
                parts = data.replace('multi_buy_execute_', '').split('_')
                product_id = int(parts[0])
                quantity = int(parts[1])
                await self.execute_multi_buy(query, db, product_id, quantity, db_user)
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
                await self.generate_pix_full(query, db, db_user, amount)
            elif data.startswith('pix_check_'):
                pix_id = data.replace('pix_check_', '')
                await self.check_pix_payment(query, db, pix_id, db_user)
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
        
        text = f"🔥 *{p.name}*\n\n"
        text += f"🟢 DISPONÍVEL AGORA\n"
        text += f"├ 💵 Preço: R$ {p.price:.2f}\n"
        text += f"├ 💰 Seu Saldo: R$ {user.balance:.2f}\n"
        text += f"└ 📦 Estoque: {p.stock}\n\n"
        if p.description:
            text += f"📝 Descrição:\n{p.description}\n\n"
        text += f"📊 Estatísticas:\n"
        text += f"⚡️ Já foram vendidas {p.total_sold} unidades!\n"
        text += f"🛡 Garantia: 30 dias\n"
        text += f"✅ Compra segura."
        
        keyboard = []
        if p.stock > 0:
            keyboard.append([InlineKeyboardButton("💳 Comprar", callback_data=f'buy_confirm_{p.id}')])
            keyboard.append([InlineKeyboardButton("🛒 Comprar mais de um", callback_data=f'buy_multi_{p.id}')])
        keyboard.append([InlineKeyboardButton("↩️ Voltar", callback_data=f'category_{p.category}')])
        
        if p.image:
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def confirm_purchase(self, query, db, product_id, user):
        p = db.get_product(product_id)
        if not p:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        if user.balance < p.price:
            falta = p.price - user.balance
            text = f"❌ *Saldo insuficiente!*\n\n💰 Seu saldo: R$ {user.balance:.2f}\n💵 Valor do produto: R$ {p.price:.2f}\n📉 Faltam: R$ {falta:.2f}\n\n💡 Deseja gerar um PIX?"
            keyboard = [
                [InlineKeyboardButton(f"Gerar PIX de R$ {p.price:.2f}", callback_data=f'pix_generate_{p.price}')],
                [InlineKeyboardButton("Cancelar", callback_data=f'product_{p.id}')]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return
        
        if p.stock <= 0:
            await query.edit_message_text("Produto esgotado!")
            return
        
        success = db.subtract_balance(user.id, p.price)
        if not success:
            await query.edit_message_text("Erro ao processar pagamento.")
            return
        
        db.decrease_stock(product_id)
        
        from services.login_service import LoginService
        login_service = LoginService()
        login = login_service.get_available(p.name)
        email = login.email if login else ''
        password = login.password if login else ''
        link = ''
        
        if login:
            login_service.mark_sold(login.id, user.id)
        
        purchase = db.create_purchase(user.id, p.name, p.price, email, password, link)
        login_service.close()
        
        text = f"✅ *Compra realizada!*\n\n📦 Produto: {p.name}\n💰 Valor: R$ {p.price:.2f}\n🎫 ID: {purchase.id}\n"
        if email:
            text += f"\n📧 Email: {email}\n🔐 Senha: {password}\n"
        
        keyboard = [[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # ============ COMPRA MÚLTIPLA ============
    
    async def show_multi_buy(self, query, db, product_id, user):
        p = db.get_product(product_id)
        if not p:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        text = (
            f"🛒 *Comprar Múltiplos*\n\n"
            f"📦 Produto: *{p.name}*\n"
            f"💰 Preço unitário: R$ {p.price:.2f}\n"
            f"💵 Seu saldo: R$ {user.balance:.2f}\n"
            f"📦 Estoque disponível: {p.stock} unid.\n\n"
            f"*Selecione a quantidade:*"
        )
        
        max_display = min(p.stock, 10)
        keyboard = []
        
        for qty in [1, 2, 3, 5]:
            if qty <= p.stock:
                total = p.price * qty
                keyboard.append([InlineKeyboardButton(
                    f"{qty} unid. - R$ {total:.2f}",
                    callback_data=f'multi_buy_confirm_{product_id}_{qty}'
                )])
        
        keyboard.append([InlineKeyboardButton("✍️ Digitar quantidade", callback_data=f'multi_buy_custom_{product_id}')])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data=f'product_{product_id}')])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def process_multi_buy(self, query, db, product_id, quantity, user):
        p = db.get_product(product_id)
        
        if not p:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        if quantity > p.stock:
            await query.edit_message_text(
                f"❌ Estoque insuficiente!\n\nDisponível: {p.stock} unid.\nSolicitado: {quantity} unid.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Tentar novamente", callback_data=f'buy_multi_{product_id}')],
                    [InlineKeyboardButton("Voltar", callback_data=f'product_{product_id}')]
                ])
            )
            return
        
        total = p.price * quantity
        
        if user.balance < total:
            falta = total - user.balance
            await query.edit_message_text(
                f"❌ *Saldo insuficiente!*\n\n"
                f"💰 Seu saldo: R$ {user.balance:.2f}\n"
                f"💵 Valor total: R$ {total:.2f}\n"
                f"📉 Faltam: R$ {falta:.2f}\n"
                f"📦 Quantidade: {quantity} unid.\n\n"
                f"💡 Deseja gerar um PIX?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Gerar PIX de R$ {total:.2f}", callback_data=f'pix_generate_{total}')],
                    [InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]
                ]),
                parse_mode='Markdown'
            )
            return
        
        text = (
            f"🛒 *Confirmar Compra Múltipla*\n\n"
            f"📦 Produto: *{p.name}*\n"
            f"📦 Quantidade: {quantity} unid.\n"
            f"💰 Preço unitário: R$ {p.price:.2f}\n"
            f"💵 Valor total: R$ {total:.2f}\n"
            f"💳 Seu saldo: R$ {user.balance:.2f}\n"
            f"💸 Saldo após compra: R$ {user.balance - total:.2f}\n\n"
            f"*Confirmar compra?*"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data=f'multi_buy_execute_{product_id}_{quantity}')],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f'product_{product_id}')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def execute_multi_buy(self, query, db, product_id, quantity, user):
        p = db.get_product(product_id)
        
        if not p or p.stock < quantity:
            await query.edit_message_text("❌ Produto indisponível ou estoque insuficiente.")
            return
        
        total = p.price * quantity
        
        if user.balance < total:
            await query.edit_message_text("❌ Saldo insuficiente!")
            return
        
        from services.login_service import LoginService
        login_service = LoginService()
        
        purchases = []
        for i in range(quantity):
            success = db.subtract_balance(user.id, p.price)
            if success:
                db.decrease_stock(product_id)
                login = login_service.get_available(p.name)
                email = login.email if login else ''
                password = login.password if login else ''
                
                if login:
                    login_service.mark_sold(login.id, user.id)
                
                purchase = db.create_purchase(user.id, p.name, p.price, email, password, '')
                purchases.append(purchase)
        
        login_service.close()
        
        text = f"✅ *Compra Múltipla Realizada!*\n\n"
        text += f"📦 Produto: *{p.name}*\n"
        text += f"📦 Quantidade: {len(purchases)} unid.\n"
        text += f"💰 Valor unitário: R$ {p.price:.2f}\n"
        text += f"💵 Valor total: R$ {total:.2f}\n\n"
        
        for i, pur in enumerate(purchases, 1):
            text += f"🎫 Compra #{i} - ID: {pur.id}\n"
            if pur.email:
                text += f"   📧 {pur.email} | 🔐 {pur.password}\n"
            text += f"   📅 Vence: {pur.expiration_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # ============ PIX COMPLETO ============
    
    async def generate_pix_full(self, query, db, user, amount):
        from services.pix_service import PixService
        
        pix_service = PixService()
        resultado = pix_service.gerar_pix(user.id, amount, "Recarga de saldo")
        
        if not resultado['sucesso']:
            await query.edit_message_text(
                f"❌ Erro ao gerar PIX: {resultado.get('erro', 'Tente novamente')}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ])
            )
            pix_service.close()
            return
        
        bonus_pct = float(db.get_setting('bonus_percentage', '0'))
        bonus_min = float(db.get_setting('bonus_min_value', '0'))
        bonus = amount * (bonus_pct/100) if amount >= bonus_min and bonus_pct > 0 else 0
        
        if resultado.get('qr_code_imagem'):
            caption = (
                f"💰 *Comprar Saldo com Pix Automático*\n\n"
                f"⏱️ Expira em: {resultado['expiracao_minutos']} Minutos\n"
                f"💵 Valor: R$ {amount:.2f}\n"
                f"✨ ID da Recarga: {resultado['pix_id']}\n\n"
                f"📃 Atenção: Este código é válido para apenas um único pagamento.\n\n"
                f"💎 Pix Copia e Cola:\n"
                f"`{resultado['copia_cola']}`\n\n"
                f"📊 Dados:\n"
                f"— 💰 Saldo Atual: R$ {user.balance:.2f}\n"
            )
            
            if bonus > 0:
                caption += f"— 🎁 Bônus à receber: R$ {bonus:.2f}\n"
                caption += f"— 💸 Saldo após o pagamento: R$ {user.balance + amount + bonus:.2f}\n"
            else:
                caption += f"— 💸 Saldo após o pagamento: R$ {user.balance + amount:.2f}\n"
            
            caption += "\n🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
                [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{resultado["pix_id"]}')]
            ]
            
            try:
                await query.message.reply_photo(
                    photo=resultado['qr_code_imagem'],
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                await query.edit_message_text(
                    "💳 PIX gerado! Confira a imagem acima.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]
                    ])
                )
            except:
                text = (
                    f"💰 PIX Gerado\n\n"
                    f"💵 Valor: R$ {amount:.2f}\n"
                    f"⏰ Expira em: {resultado['expiracao_minutos']} min\n"
                    f"🆔 ID: {resultado['pix_id']}\n\n"
                    f"📋 Copia e Cola:\n`{resultado['copia_cola']}`"
                )
                keyboard = [
                    [InlineKeyboardButton("Verificar Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            text = (
                f"💰 PIX Gerado\n\n"
                f"💵 Valor: R$ {amount:.2f}\n"
                f"⏰ Expira em: {resultado['expiracao_minutos']} min\n"
                f"🆔 ID: {resultado['pix_id']}\n\n"
                f"📋 Copia e Cola:\n`{resultado['copia_cola']}`"
            )
            keyboard = [
                [InlineKeyboardButton("Verificar Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
                [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
        pix_service.close()
    
    async def check_pix_payment(self, query, db, pix_id, user):
        from services.pix_service import PixService
        pix_service = PixService()
        
        resultado = pix_service.verificar_pagamento(pix_id)
        
        if resultado.get('status') == 'approved':
            await query.edit_message_text(
                f"✅ *Pagamento Aprovado!*\n\n"
                f"💰 Valor creditado: R$ {resultado.get('total_creditado', 0):.2f}\n"
                f"💵 Novo saldo: R$ {user.balance:.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]
                ]),
                parse_mode='Markdown'
            )
        elif resultado.get('pendente'):
            await query.edit_message_text(
                "⏳ *Pagamento Pendente*\n\nAguardando confirmação do PIX...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f'pix_check_{pix_id}')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ]),
                parse_mode='Markdown'
            )
        elif resultado.get('expirado'):
            await query.edit_message_text(
                f"⌛️ *PAGAMENTO PIX EXPIRADO*\n\n"
                f"⚠️ O tempo limite para realizar este pagamento foi excedido.\n\n"
                f"🆔 Referência: {pix_id}\n"
                f"💸 Valor: R$ {resultado.get('valor', 0):.2f}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Gerar Novo PIX", callback_data='menu_recharge')],
                    [InlineKeyboardButton("Voltar", callback_data='back_main')]
                ]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "❌ Pagamento não localizado.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ])
            )
        
        pix_service.close()
    
    async def show_profile(self, query, db, user):
        text = "👤 *Meu Perfil*\n\n"
        text += f"🔍 Veja aqui os detalhes da sua conta:\n\n"
        text += f"👤 Informações:\n"
        text += f"🆔 ID da Carteira: {user.telegram_id}\n"
        text += f"💰 Saldo Atual: R$ {user.balance:.2f}\n"
        if user.whatsapp:
            text += f"📲 Seu Whatsapp: {user.whatsapp}\n"
        text += f"\n─── 📊 Suas Movimentações:\n"
        text += f"ー 🛒 Compras Realizadas: {user.total_purchases}\n"
        text += f"ー 💰 Total Gasto Em Compras: R$ {user.total_spent:.2f}\n"
        text += f"ー 💠 Pix Inseridos: R$ {user.total_recharged:.2f}\n"
        text += f"ー 🎁 Gifts Resgatados: R$ {user.gifts_redeemed:.2f}"
        
        keyboard = [
            [InlineKeyboardButton("📋 Histórico de Compras", callback_data='profile_history')],
            [InlineKeyboardButton("🎁 Resgatar Gift Card", callback_data='profile_gift')],
            [InlineKeyboardButton("✏️ Alterar Dados", callback_data='profile_edit')],
            [InlineKeyboardButton("↩️ Voltar", callback_data='back_main')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
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
        text = f"🛍 Compras: {len(purchases)}\n\n"
        text += f"⏰ Data da compra: {p.purchase_date.strftime('%d/%m/%Y')}\n"
        if p.expiration_date:
            text += f"📆 Vencimento: {p.expiration_date.strftime('%d/%m/%Y')}\n"
        text += f"💰 Valor: R$ {p.amount:.2f}\n"
        text += f"🎫 ID da compra: {p.id}\n"
        text += f"⚜️ Serviço: {p.product_name}\n"
        if p.email:
            text += f"📧 Email: {p.email}\n"
            text += f"🔐 Senha: {p.password}\n"
        if p.activation_link:
            text += f"📃 Nota: Use o link abaixo para ativar:\n{p.activation_link}\n"
        
        keyboard = []
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f'history_page_{page-1}'))
        if page < len(purchases) - 1:
            nav.append(InlineKeyboardButton("➡️ Próximo", callback_data=f'history_page_{page+1}'))
        if nav:
            keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("Voltar", callback_data='menu_profile')])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_gift_code(self, query, user_id):
        self.user_states[user_id] = 'awaiting_gift_code'
        await query.edit_message_text(
            "🎁 *RESGATAR GIFT CARD*\n\nDigite o código do seu gift card abaixo:\n\nExemplo: ABC123XYZ456",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancelar", callback_data='menu_profile')]
            ]),
            parse_mode='Markdown'
        )
    
    async def show_edit_data(self, query, db, user):
        text = "✏️ *Alterar Dados*\n\n"
        text += "Selecione o dado que deseja alterar:\n\n"
        text += f"📱 WhatsApp: {user.whatsapp or 'Nao cadastrado'}"
        keyboard = [
            [InlineKeyboardButton("📱 Alterar WhatsApp", callback_data='edit_whatsapp')],
            [InlineKeyboardButton("↩️ Voltar", callback_data='menu_profile')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def ask_whatsapp(self, query, user_id):
        self.user_states[user_id] = 'awaiting_whatsapp'
        await query.edit_message_text(
            "📱 *Envie seu número de WhatsApp*\n\nFormato: DDD + Número (apenas números)\nExemplo: 11999998888\n\n⚠️ Envie *remover* para remover o número cadastrado.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancelar", callback_data='menu_profile')]
            ]),
            parse_mode='Markdown'
        )
    
    async def show_recharge_menu(self, query, db, user):
        text = f"🆔| ID da Carteira: {user.telegram_id}\n"
        text += f"💰| Saldo Disponível: R$ {user.balance:.2f}\n\n"
        text += "📍 Opte por 💠 Pix Rápido para que seu saldo seja creditado imediatamente.\n\n"
        text += "💡 Selecione uma opção para recarregar:"
        
        keyboard = [
            [InlineKeyboardButton("💠 Pix Rápido", callback_data='recharge_pix')],
            [InlineKeyboardButton("↩️ Voltar", callback_data='back_main')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def ask_recharge_value(self, query, user_id):
        self.user_states[user_id] = 'awaiting_recharge_value'
        min_val = self.db.get_setting('deposit_min', '2')
        await query.edit_message_text(
            f"ℹ️ *Informe o valor que deseja recarregar:*\n\n🔻 Recarga mínima: R$ {min_val}\n\n⚠️ Por favor, envie o valor que deseja recarregar agora.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancelar", callback_data='menu_recharge')]
            ]),
            parse_mode='Markdown'
        )
    
    async def show_affiliate(self, query, db, user):
        commission = db.get_setting('commission_percentage', '20')
        text = "🎯 *PROGRAMA DE AFILIADOS*\n\n"
        text += f"Status: Ativo\n"
        text += f"Sua comissão: {commission}%\n\n"
        text += f"👥 Indicações: {user.total_referrals}\n"
        text += f"💰 Total ganho: R$ {user.commission_balance:.2f}\n"
        
        link = f"https://t.me/{(await query.message.chat.username) or 'bot'}?start={user.telegram_id}"
        text += f"\n🔗 Seu link:\n{link}"
        
        keyboard = [[InlineKeyboardButton("↩️ Voltar", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_top(self, query, db):
        keyboard = [
            [InlineKeyboardButton("🏆 Serviços Mais Vendidos", callback_data='top_products')],
            [InlineKeyboardButton("💰 Mais Recarregaram", callback_data='top_rechargers')],
            [InlineKeyboardButton("🛒 Mais Compraram", callback_data='top_buyers')],
            [InlineKeyboardButton("💵 Mais Saldo", callback_data='top_balance')],
            [InlineKeyboardButton("↩️ Voltar", callback_data='back_main')]
        ]
        await query.edit_message_text("🏆 *Rankings*\n\nSelecione o ranking:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_top_type(self, query, db, tipo):
        text = "🏆 *Ranking*\n\n"
        if tipo == 'products':
            items = db.get_top_products()
            text += "*Serviços mais vendidos (deste mês):*\n\n"
            for i, p in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}°)"
                text += f"{medal} {p.name} - {p.total_sold} pedidos\n"
        elif tipo == 'rechargers':
            items = db.get_top_rechargers()
            text += "*Usuários que mais recarregaram:*\n\n"
            for i, u in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}°)"
                name = u.first_name or f"ID:{u.telegram_id}"
                text += f"{medal} {name} - R$ {u.total_recharged:.2f}\n"
        elif tipo == 'buyers':
            items = db.get_top_buyers()
            text += "*Usuários que mais compraram:*\n\n"
            for i, u in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}°)"
                name = u.first_name or f"ID:{u.telegram_id}"
                text += f"{medal} {name} - {u.total_purchases} compras\n"
        elif tipo == 'balance':
            items = db.get_top_buyers()
            text += "*Usuários com mais saldo:*\n\n"
            for i, u in enumerate(items, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}°)"
                name = u.first_name or f"ID:{u.telegram_id}"
                text += f"{medal} {name} - R$ {u.balance:.2f}\n"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='menu_top')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def ask_search(self, query, db, user_id):
        self.user_states[user_id] = 'awaiting_search'
        await query.edit_message_text(
            "🔍 Digite o nome do produto que deseja pesquisar:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancelar", callback_data='back_main')]
            ])
        )
    
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
            text = f"{welcome}\n\n💠 Seus Dados:\n├👤 ID: {user.telegram_id}\n└💰 Saldo: R$ {user.balance:.2f}"
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
                await update.message.reply_text(f"💳 Gerando PIX de R$ {amount:.2f}...\n\nUse /start para ver o menu.")
            except:
                await update.message.reply_text("Valor invalido. Use: /pix 10")
        else:
            await update.message.reply_text("Use: /pix VALOR\nExemplo: /pix 10")
    
    async def cmd_saldo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db = DBManager()
        db_user = db.get_user(user.id)
        if db_user:
            text = f"╭{'─'*20}╮\n"
            text += f"💰 Carteira id: {user.id}\n"
            text += f"💸 Saldo: R$ {db_user.balance:.2f}\n"
            text += f"╰{'─'*20}╯"
            await update.message.reply_text(text)
        db.close()
    
    async def cmd_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🆔 Seu id é: {update.effective_user.id}")
    
    async def cmd_historico(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botões do menu para ver seu histórico.")
    
    async def cmd_afiliados(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botões do menu para ver seus afiliados.")
    
    async def cmd_ranking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use os botões do menu para ver os rankings.")
    
    async def cmd_termos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db = DBManager()
        text = db.get_setting('terms_text', 'Termos de uso nao configurados.')
        await update.message.reply_text(text)
        db.close()
    
    async def cmd_alertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Sistema de alertas em breve.")

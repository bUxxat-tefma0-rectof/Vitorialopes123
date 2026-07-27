from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DBManager
from services.pix_service import PixService
from services.gift_service import GiftService
from services.affiliate_service import AffiliateService
from services.login_service import LoginService
from datetime import datetime

class CallbackHandler:
    def __init__(self):
        self.db = DBManager()
        self.pix = PixService()
        self.gift = GiftService()
        self.affiliate = AffiliateService()
        self.login = LoginService()
        self.states = {}
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user
        
        db_user = self.db.get_user(user.id)
        if not db_user:
            db_user = self.db.create_user(user.id, user.username, user.first_name)
        
        if data.startswith('buy_confirm_'):
            await self.confirm_buy(query, data, db_user)
        elif data.startswith('buy_multi_'):
            await self.show_multi_buy(query, data, db_user)
        elif data.startswith('multi_buy_confirm_'):
            await self.process_multi_buy(query, data, db_user)
        elif data.startswith('multi_buy_execute_'):
            await self.execute_multi_buy(query, data, db_user)
        elif data.startswith('pix_generate_'):
            await self.generate_pix(query, data, db_user)
        elif data.startswith('pix_check_'):
            await self.check_pix(query, data, db_user)
        elif data.startswith('pix_copy_'):
            await self.copy_pix(query, data)
        elif data.startswith('gift_redeem_'):
            await self.redeem_gift(query, data, user.id)
        elif data.startswith('edit_confirm_'):
            await self.confirm_edit(query, data, db_user)
        elif data.startswith('alert_toggle_'):
            await self.toggle_alert(query, data, user.id)
        elif data == 'profile_history_active':
            await self.show_active_purchases(query, db_user)
        elif data == 'profile_history_all':
            await self.show_all_purchases(query, db_user)
    
    async def confirm_buy(self, query, data, user):
        product_id = int(data.replace('buy_confirm_', ''))
        product = self.db.get_product(product_id)
        
        if not product:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        if user.balance < product.price:
            falta = product.price - user.balance
            keyboard = [
                [InlineKeyboardButton(f"Gerar PIX de R$ {product.price:.2f}", callback_data=f'pix_generate_{product.price}')],
                [InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]
            ]
            await query.edit_message_text(
                f"❌ *Saldo insuficiente!*\n\n💰 Seu saldo: R$ {user.balance:.2f}\n💵 Valor: R$ {product.price:.2f}\n📉 Faltam: R$ {falta:.2f}\n\n💡 Deseja gerar um PIX?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        if product.stock <= 0:
            await query.edit_message_text("❌ Produto esgotado!")
            return
        
        success = self.db.subtract_balance(user.id, product.price)
        if not success:
            await query.edit_message_text("❌ Erro ao processar pagamento.")
            return
        
        self.db.decrease_stock(product_id)
        
        login = self.login.get_available(product.name)
        email = login.email if login else ''
        password = login.password if login else ''
        
        if login:
            self.login.mark_sold(login.id, user.id)
        
        purchase = self.db.create_purchase(user.id, product.name, product.price, email, password, '')
        
        text = f"✅ *Compra realizada!*\n\n📦 Produto: {product.name}\n💰 Valor: R$ {product.price:.2f}\n🎫 ID: {purchase.id}\n"
        if email:
            text += f"\n📧 Email: `{email}`\n🔐 Senha: `{password}`\n"
            if purchase.activation_link:
                text += f"\n🔗 Link: {purchase.activation_link}\n"
        text += f"\n📅 Vence: {purchase.expiration_date.strftime('%d/%m/%Y')}"
        
        keyboard = [[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_multi_buy(self, query, data, user):
        product_id = int(data.replace('buy_multi_', ''))
        product = self.db.get_product(product_id)
        
        if not product:
            await query.edit_message_text("Produto nao encontrado.")
            return
        
        text = (
            f"🛒 *Comprar Múltiplos*\n\n"
            f"📦 Produto: *{product.name}*\n"
            f"💰 Preço unitário: R$ {product.price:.2f}\n"
            f"💵 Seu saldo: R$ {user.balance:.2f}\n"
            f"📦 Estoque: {product.stock} unid.\n\n"
            f"*Selecione a quantidade:*"
        )
        
        keyboard = []
        for qty in [1, 2, 3, 5]:
            if qty <= product.stock:
                total = product.price * qty
                keyboard.append([InlineKeyboardButton(
                    f"{qty} unid. - R$ {total:.2f}",
                    callback_data=f'multi_buy_confirm_{product_id}_{qty}'
                )])
        
        keyboard.append([InlineKeyboardButton("✍️ Digitar quantidade", callback_data=f'multi_buy_custom_{product_id}')])
        keyboard.append([InlineKeyboardButton("Voltar", callback_data=f'product_{product_id}')])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def process_multi_buy(self, query, data, user):
        parts = data.replace('multi_buy_confirm_', '').split('_')
        product_id = int(parts[0])
        quantity = int(parts[1])
        product = self.db.get_product(product_id)
        
        if not product or quantity > product.stock:
            await query.edit_message_text("❌ Produto indisponível ou estoque insuficiente.")
            return
        
        total = product.price * quantity
        
        if user.balance < total:
            falta = total - user.balance
            keyboard = [
                [InlineKeyboardButton(f"Gerar PIX de R$ {total:.2f}", callback_data=f'pix_generate_{total}')],
                [InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]
            ]
            await query.edit_message_text(
                f"❌ Saldo insuficiente!\n\n💰 Seu saldo: R$ {user.balance:.2f}\n💵 Total: R$ {total:.2f}\n📉 Faltam: R$ {falta:.2f}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        text = (
            f"🛒 *Confirmar Compra Múltipla*\n\n"
            f"📦 {product.name}\n"
            f"📦 Quantidade: {quantity} unid.\n"
            f"💰 Unitário: R$ {product.price:.2f}\n"
            f"💵 Total: R$ {total:.2f}\n"
            f"💳 Saldo: R$ {user.balance:.2f}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data=f'multi_buy_execute_{product_id}_{quantity}')],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f'product_{product_id}')]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def execute_multi_buy(self, query, data, user):
        parts = data.replace('multi_buy_execute_', '').split('_')
        product_id = int(parts[0])
        quantity = int(parts[1])
        product = self.db.get_product(product_id)
        
        if not product or product.stock < quantity:
            await query.edit_message_text("❌ Produto indisponível.")
            return
        
        total = product.price * quantity
        
        if user.balance < total:
            await query.edit_message_text("❌ Saldo insuficiente!")
            return
        
        purchases = []
        for i in range(quantity):
            success = self.db.subtract_balance(user.id, product.price)
            if success:
                self.db.decrease_stock(product_id)
                login = self.login.get_available(product.name)
                email = login.email if login else ''
                password = login.password if login else ''
                
                if login:
                    self.login.mark_sold(login.id, user.id)
                
                purchase = self.db.create_purchase(user.id, product.name, product.price, email, password, '')
                purchases.append(purchase)
        
        text = f"✅ *Compra Múltipla Realizada!*\n\n📦 {product.name}\n📦 Quantidade: {len(purchases)} unid.\n💰 Unitário: R$ {product.price:.2f}\n💵 Total: R$ {total:.2f}\n\n"
        
        for i, pur in enumerate(purchases, 1):
            text += f"🎫 #{i} - ID: {pur.id}\n"
            if pur.email:
                text += f"📧 `{pur.email}` | 🔐 `{pur.password}`\n"
            text += f"📅 Vence: {pur.expiration_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def generate_pix(self, query, data, user):
        amount = float(data.replace('pix_generate_', ''))
        
        resultado = self.pix.gerar_pix(user.id, amount, "Recarga de saldo")
        
        if not resultado['sucesso']:
            await query.edit_message_text(f"❌ Erro: {resultado.get('erro', 'Tente novamente')}")
            return
        
        bonus_pct = float(self.db.get_setting('bonus_percentage', '0'))
        bonus_min = float(self.db.get_setting('bonus_min_value', '0'))
        bonus = amount * (bonus_pct/100) if amount >= bonus_min and bonus_pct > 0 else 0
        
        caption = (
            f"💰 *PIX Gerado*\n\n"
            f"💵 Valor: R$ {amount:.2f}\n"
            f"⏰ Expira em: {resultado['expiracao_minutos']} min\n"
            f"🆔 ID: {resultado['pix_id']}\n\n"
            f"📋 Copia e Cola:\n`{resultado['copia_cola']}`"
        )
        
        if bonus > 0:
            caption += f"\n\n🎁 Bônus: R$ {bonus:.2f}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
            [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{resultado["pix_id"]}')],
            [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
        ]
        
        if resultado.get('qr_code_imagem'):
            try:
                await query.message.reply_photo(
                    photo=resultado['qr_code_imagem'],
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                await query.edit_message_text("💳 PIX gerado! Confira a imagem acima.")
            except:
                await query.edit_message_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.edit_message_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def check_pix(self, query, data, user):
        pix_id = data.replace('pix_check_', '')
        resultado = self.pix.verificar_pagamento(pix_id)
        
        if resultado.get('status') == 'approved':
            await query.edit_message_text(
                f"✅ *Pagamento Aprovado!*\n\n💰 Valor creditado com sucesso!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]),
                parse_mode='Markdown'
            )
        elif resultado.get('pendente'):
            await query.edit_message_text(
                "⏳ *Pagamento Pendente*\n\nAguardando confirmação...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f'pix_check_{pix_id}')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ]),
                parse_mode='Markdown'
            )
        elif resultado.get('expirado'):
            await query.edit_message_text(
                f"⌛️ *PIX Expirado*\n\n🆔 {pix_id}\n💸 Valor: R$ {resultado.get('valor', 0):.2f}\n\nGere um novo PIX.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Novo PIX", callback_data='menu_recharge')]]),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Pagamento não localizado.")
    
    async def copy_pix(self, query, data):
        await query.answer("📋 Código PIX copiado! Cole no seu banco.", show_alert=True)
    
    async def redeem_gift(self, query, data, user_id):
        code = data.replace('gift_redeem_', '')
        success = self.gift.redeem(code, user_id)
        
        if success:
            await query.edit_message_text("✅ Gift Card resgatado com sucesso!")
        else:
            await query.edit_message_text("❌ Gift Card inválido ou já utilizado!")
    
    async def confirm_edit(self, query, data, user):
        field = data.replace('edit_confirm_', '')
        if field == 'whatsapp_remove':
            user.whatsapp = None
            self.db.db.commit()
            await query.edit_message_text("✅ WhatsApp removido!")
    
    async def toggle_alert(self, query, data, user_id):
        product_id = int(data.replace('alert_toggle_', ''))
        from database.models import SessionLocal, Alert
        db = SessionLocal()
        alert = db.query(Alert).filter_by(user_id=user_id, product_id=product_id).first()
        
        if alert and alert.active:
            alert.active = False
            status = "❌"
        else:
            if alert:
                alert.active = True
            else:
                db.add(Alert(user_id=user_id, product_id=product_id, active=True))
            status = "✅"
        
        db.commit()
        db.close()
        await query.answer(f"Alerta {status}")
    
    async def show_active_purchases(self, query, user):
        purchases = self.db.get_user_purchases(user.id)
        active = [p for p in purchases if p.expiration_date and p.expiration_date > datetime.now()]
        
        if not active:
            await query.edit_message_text(
                "Você não tem compras ativas (não vencidas) no bot.\n\nUse o botão abaixo para ver todas as compras.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Ver Todas", callback_data='profile_history_all')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
                ])
            )
            return
        
        text = f"🟢 *Compras Ativas:* {len(active)}\n\n"
        for p in active[:5]:
            text += f"📦 {p.product_name}\n📅 Vence: {p.expiration_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("Ver Todas", callback_data='profile_history_all')],
            [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_all_purchases(self, query, user):
        purchases = self.db.get_user_purchases(user.id)
        
        if not purchases:
            await query.edit_message_text(
                "Nenhuma compra encontrada.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data='menu_profile')]])
            )
            return
        
        text = f"📋 *Todas as Compras:* {len(purchases)}\n\n"
        for p in purchases[:10]:
            text += f"📦 {p.product_name} - R$ {p.amount:.2f}\n📅 {p.purchase_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='menu_profile')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    def close(self):
        self.db.close()
        self.pix.close()
        self.gift.close()
        self.affiliate.close()
        self.login.close()

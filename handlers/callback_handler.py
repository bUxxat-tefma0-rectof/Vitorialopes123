from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DBManager
from services.pix_service import PixService
from services.gift_service import GiftService
from services.affiliate_service import AffiliateService
from services.login_service import LoginService

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
            await self.ask_multi_buy(query, data, user.id)
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
        elif data.startswith('admin_edit_'):
            await self.handle_admin_edit(query, data, user.id)
        elif data.startswith('admin_toggle_'):
            await self.handle_admin_toggle(query, data)
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
                f"❌ Saldo insuficiente!\n\n"
                f"💰 Seu saldo: R$ {user.balance:.2f}\n"
                f"💵 Valor do produto: R$ {product.price:.2f}\n"
                f"📉 Faltam: R$ {falta:.2f}\n\n"
                f"💡 Deseja gerar um PIX?",
                reply_markup=InlineKeyboardMarkup(keyboard)
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
        link = ''
        
        if login:
            self.login.mark_sold(login.id, user.id)
        
        purchase = self.db.create_purchase(user.id, product.name, product.price, email, password, link)
        
        text = f"✅ Compra realizada!\n\n"
        text += f"📦 Produto: {product.name}\n"
        text += f"💰 Valor: R$ {product.price:.2f}\n"
        text += f"🎫 ID: {purchase.id}\n"
        if email:
            text += f"📧 Email: {email}\n"
            text += f"🔐 Senha: {password}\n"
        if link:
            text += f"🔗 Link: {link}\n"
        
        keyboard = [[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        if user.referred_by:
            self.affiliate.add_commission_on_recharge(user.id, product.price)
    
    async def ask_multi_buy(self, query, data, user_id):
        product_id = int(data.replace('buy_multi_', ''))
        self.states[user_id] = f'awaiting_multi_buy_{product_id}'
        await query.edit_message_text(
            "🛒 Quantas unidades deseja comprar?\n\nDigite a quantidade:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]])
        )
    
    async def check_pix(self, query, data, user):
        pix_id = data.replace('pix_check_', '')
        success, total = self.db.confirm_pix(pix_id)
        
        if success:
            await query.edit_message_text(
                f"✅ Pagamento confirmado!\n\n"
                f"💰 Valor creditado: R$ {total:.2f}\n"
                f"💵 Novo saldo: R$ {user.balance:.2f}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar ao Menu", callback_data='back_main')]])
            )
            if user.referred_by:
                self.affiliate.add_commission_on_recharge(user.id, total)
        else:
            await query.edit_message_text(
                "⏳ Pagamento ainda nao confirmado.\n\nVerifique novamente ou aguarde.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Verificar Novamente", callback_data=f'pix_check_{pix_id}')],
                    [InlineKeyboardButton("Voltar", callback_data='back_main')]
                ])
            )
    
    async def copy_pix(self, query, data):
        pix_id = data.replace('pix_copy_', '')
        await query.answer("Codigo PIX copiado para a mensagem acima!", show_alert=True)
    
    async def redeem_gift(self, query, data, user_id):
        code = data.replace('gift_redeem_', '')
        success = self.gift.redeem(code, user_id)
        
        if success:
            await query.edit_message_text(
                "✅ Gift Card resgatado com sucesso!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data='menu_profile')]])
            )
        else:
            await query.edit_message_text(
                "❌ Gift Card invalido ou ja utilizado!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data='menu_profile')]])
            )
    
    async def confirm_edit(self, query, data, user):
        field = data.replace('edit_confirm_', '')
        if field == 'whatsapp_remove':
            user.whatsapp = None
            self.db.db.commit()
            await query.edit_message_text(
                "✅ WhatsApp removido com sucesso!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data='menu_profile')]])
            )
    
    async def toggle_alert(self, query, data, user_id):
        product_id = int(data.replace('alert_toggle_', ''))
        from services.alert_service import AlertService
        alert_svc = AlertService()
        
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
    
    async def handle_admin_edit(self, query, data, user_id):
        from config.settings import ADMIN_ID
        if user_id != ADMIN_ID:
            return
        
        field = data.replace('admin_edit_', '')
        self.states[user_id] = f'admin_editing_{field}'
        
        prompts = {
            'welcome': "Envie o novo texto de boas-vindas:",
            'image': "Envie a URL da nova imagem:",
            'support': "Envie o novo link de suporte:",
            'buttons': "Envie a configuracao dos botoes no formato:\nBTN1|BTN2|BTN3|BTN4\nPOS1|POS2|POS3|POS4\n\nPosicoes: full, left, right",
            'commission': "Envie o novo percentual de comissao:",
            'deposit_min': "Envie o novo valor minimo de deposito:",
            'deposit_max': "Envie o novo valor maximo de deposito:",
            'expiration': "Envie o novo tempo de expiracao do PIX (minutos):",
            'mp_token': "Envie o novo Token do Mercado Pago:",
            'bonus': "Envie o novo percentual de bonus:",
            'bonus_min': "Envie o novo valor minimo para bonus:",
            'registration_bonus': "Envie o novo bonus de registro:",
        }
        
        msg = prompts.get(field, f"Envie o novo valor para {field}:")
        await query.edit_message_text(msg)
    
    async def handle_admin_toggle(self, query, data):
        from config.settings import ADMIN_ID
        if query.from_user.id != ADMIN_ID:
            return
        
        field = data.replace('admin_toggle_', '')
        current = self.db.get_setting(field, 'off')
        new_value = 'on' if current == 'off' else 'off'
        self.db.set_setting(field, new_value)
        
        await query.edit_message_text(f"✅ {field} alterado para: {new_value}")
    
    async def show_active_purchases(self, query, user):
        purchases = self.db.get_user_purchases(user.id)
        active = [p for p in purchases if p.expiration_date and p.expiration_date > datetime.now()]
        
        if not active:
            await query.edit_message_text(
                "Voce nao tem compras ativas.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Ver Todas", callback_data='profile_history_all')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
                ])
            )
            return
        
        text = f"Compras Ativas: {len(active)}\n\n"
        for p in active[:5]:
            text += f"📦 {p.product_name}\n"
            text += f"📅 Vence: {p.expiration_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("Ver Todas", callback_data='profile_history_all')],
            [InlineKeyboardButton("Voltar", callback_data='menu_profile')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_all_purchases(self, query, user):
        purchases = self.db.get_user_purchases(user.id)
        
        if not purchases:
            await query.edit_message_text(
                "Nenhuma compra encontrada.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Voltar", callback_data='menu_profile')]])
            )
            return
        
        text = f"Todas as Compras: {len(purchases)}\n\n"
        for p in purchases[:10]:
            text += f"📦 {p.product_name} - R$ {p.amount:.2f}\n"
            text += f"📅 {p.purchase_date.strftime('%d/%m/%Y')}\n\n"
        
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='menu_profile')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    def close(self):
        self.db.close()
        self.gift.close()
        self.affiliate.close()
        self.login.close()

from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DBManager
from services.pix_service import PixService
from services.gift_service import GiftService
from services.affiliate_service import AffiliateService
from services.login_service import LoginService
from utils.helpers import validate_phone, validate_amount, parse_product_data, parse_login_data
from config.settings import ADMIN_ID

class MessageHandler:
    def __init__(self):
        self.db = DBManager()
        self.pix = PixService()
        self.gift = GiftService()
        self.affiliate = AffiliateService()
        self.login = LoginService()
        self.states = {}
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text
        
        db_user = self.db.get_user(user.id)
        if not db_user:
            db_user = self.db.create_user(user.id, user.username, user.first_name)
        
        state = self.states.get(user.id)
        
        if state and state.startswith('admin_editing_'):
            await self.handle_admin_edit_response(update, user, text, state)
            return
        
        if state and state.startswith('awaiting_'):
            await self.handle_state_response(update, user, text, state, db_user)
            return
        
        from handlers.client import ClientHandlers
        client = ClientHandlers()
        await client.show_main_menu(update, db_user)
    
    async def handle_state_response(self, update, user, text, state, db_user):
        if state == 'awaiting_recharge_value':
            if validate_amount(text, float(self.db.get_setting('deposit_min', '2')), float(self.db.get_setting('deposit_max', '150'))):
                amount = float(text)
                pix_id = self.pix.generate_pix_id()
                copy_paste = self.pix.generate_copy_paste()
                expires_at = self.pix.get_expiration(int(self.db.get_setting('pix_expiration', '15')))
                
                self.db.create_pix(db_user.id, amount, pix_id, '', copy_paste, expires_at)
                
                bonus_pct = float(self.db.get_setting('bonus_percentage', '0'))
                bonus = amount * (bonus_pct/100) if bonus_pct > 0 else 0
                
                text = f"💳 PIX Gerado\n\n"
                text += f"💰 Valor: R$ {amount:.2f}\n"
                text += f"🆔 ID: {pix_id}\n"
                text += f"⏰ Expira em: {self.db.get_setting('pix_expiration', '15')} min\n"
                if bonus > 0:
                    text += f"🎁 Bonus: R$ {bonus:.2f}\n"
                text += f"\n📋 Codigo:\n`{copy_paste}`"
                
                keyboard = [
                    [InlineKeyboardButton("Verificar Pagamento", callback_data=f'pix_check_{pix_id}')],
                    [InlineKeyboardButton("Voltar", callback_data='menu_recharge')]
                ]
                
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                self.states.pop(user.id, None)
            else:
                await update.message.reply_text("❌ Valor invalido! Tente novamente.")
        
        elif state == 'awaiting_gift_code':
            code = text.strip().upper()
            success = self.gift.redeem(code, user.id)
            
            if success:
                await update.message.reply_text("✅ Gift Card resgatado com sucesso!")
            else:
                await update.message.reply_text("❌ Codigo invalido ou ja utilizado!")
            
            self.states.pop(user.id, None)
        
        elif state == 'awaiting_whatsapp':
            if text.lower() == 'remover':
                db_user.whatsapp = None
                self.db.db.commit()
                await update.message.reply_text("✅ WhatsApp removido!")
            elif validate_phone(text):
                db_user.whatsapp = text
                self.db.db.commit()
                await update.message.reply_text(f"✅ WhatsApp salvo: {text}")
            else:
                await update.message.reply_text("❌ Numero invalido! Use DDD+Numero.")
            
            self.states.pop(user.id, None)
        
        elif state == 'awaiting_search':
            products = self.db.get_products()
            found = [p for p in products if text.lower() in p.name.lower()]
            
            if found:
                text = f"🔍 Resultados para '{text}':\n\n"
                for p in found[:10]:
                    text += f"📦 {p.name} - R$ {p.price:.2f} ({p.stock} unid.)\n"
                
                keyboard = []
                for p in found[:5]:
                    keyboard.append([InlineKeyboardButton(f"Comprar {p.name}", callback_data=f'product_{p.id}')])
                keyboard.append([InlineKeyboardButton("Voltar", callback_data='back_main')])
                
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text("Nenhum produto encontrado.")
            
            self.states.pop(user.id, None)
        
        elif state and state.startswith('awaiting_multi_buy_'):
            product_id = int(state.replace('awaiting_multi_buy_', ''))
            try:
                qty = int(text)
                if qty > 0:
                    product = self.db.get_product(product_id)
                    if product and product.stock >= qty:
                        total = product.price * qty
                        if db_user.balance >= total:
                            for _ in range(qty):
                                self.db.subtract_balance(db_user.id, product.price)
                                self.db.decrease_stock(product_id)
                                login = self.login.get_available(product.name)
                                if login:
                                    self.login.mark_sold(login.id, db_user.id)
                                    self.db.create_purchase(db_user.id, product.name, product.price, login.email, login.password)
                                else:
                                    self.db.create_purchase(db_user.id, product.name, product.price)
                            
                            await update.message.reply_text(f"✅ {qty}x {product.name} comprados!\nTotal: R$ {total:.2f}")
                        else:
                            await update.message.reply_text(f"❌ Saldo insuficiente! Necessario: R$ {total:.2f}")
                    else:
                        await update.message.reply_text("❌ Estoque insuficiente!")
                else:
                    await update.message.reply_text("❌ Quantidade invalida!")
            except:
                await update.message.reply_text("❌ Valor invalido!")
            
            self.states.pop(user.id, None)
    
    async def handle_admin_edit_response(self, update, user, text, state):
        if user.id != ADMIN_ID:
            return
        
        field = state.replace('admin_editing_', '')
        
        field_map = {
            'welcome': 'welcome_text',
            'image': 'welcome_image',
            'support': 'support_link',
            'commission': 'commission_percentage',
            'deposit_min': 'deposit_min',
            'deposit_max': 'deposit_max',
            'expiration': 'pix_expiration',
            'mp_token': 'mp_access_token',
            'bonus': 'bonus_percentage',
            'bonus_min': 'bonus_min_value',
            'registration_bonus': 'registration_bonus',
        }
        
        db_key = field_map.get(field)
        
        if field == 'buttons':
            parts = text.split('\n')
            if len(parts) >= 2:
                btns = parts[0].split('|')
                poss = parts[1].split('|')
                for i, (btn, pos) in enumerate(zip(btns[:4], poss[:4]), 1):
                    self.db.set_setting(f'btn{i}_text', btn.strip())
                    self.db.set_setting(f'btn{i}_pos', pos.strip())
                await update.message.reply_text("✅ Botoes atualizados!")
        elif db_key:
            self.db.set_setting(db_key, text)
            await update.message.reply_text(f"✅ {field} atualizado!")
        else:
            await update.message.reply_text(f"✅ {field} atualizado!")
        
        self.states.pop(user.id, None)
    
    def close(self):
        self.db.close()
        self.gift.close()
        self.affiliate.close()
        self.login.close()

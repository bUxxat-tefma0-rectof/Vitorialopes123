from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DBManager
from services.pix_service import PixService
from services.gift_service import GiftService
from services.affiliate_service import AffiliateService
from services.login_service import LoginService
from utils.helpers import validate_phone, validate_amount
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
    
    async def handle_state_response(self, update, user, text, state, db_user):
        if text.lower() == 'cancelar':
            self.states.pop(user.id, None)
            await update.message.reply_text("❌ Operação cancelada.")
            return
        
        if state == 'awaiting_recharge_value':
            await self.process_recharge_value(update, user, text, db_user)
        elif state == 'awaiting_gift_code':
            await self.process_gift_code(update, user, text)
        elif state == 'awaiting_whatsapp':
            await self.process_whatsapp(update, user, text, db_user)
        elif state == 'awaiting_search':
            await self.process_search(update, user, text)
        elif state.startswith('awaiting_multi_buy_'):
            await self.process_multi_buy_custom(update, user, text, state, db_user)
    
    async def process_recharge_value(self, update, user, text, db_user):
        min_val = float(self.db.get_setting('deposit_min', '2'))
        max_val = float(self.db.get_setting('deposit_max', '150'))
        
        if not validate_amount(text, min_val, max_val):
            await update.message.reply_text(f"❌ Valor inválido! Mín: R$ {min_val:.2f} Máx: R$ {max_val:.2f}")
            return
        
        amount = float(text)
        self.states.pop(user.id, None)
        
        from services.pix_service import PixService
        pix_service = PixService()
        resultado = pix_service.gerar_pix(db_user.id, amount, "Recarga de saldo")
        
        if resultado['sucesso']:
            caption = f"💰 PIX Gerado\n\n💵 Valor: R$ {amount:.2f}\n⏰ Expira em: {resultado['expiracao_minutos']} min\n🆔 ID: {resultado['pix_id']}\n\n📋 Copia e Cola:\n`{resultado['copia_cola']}`"
            keyboard = [
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
                [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{resultado["pix_id"]}')]
            ]
            
            if resultado.get('qr_code_imagem'):
                await update.message.reply_photo(photo=resultado['qr_code_imagem'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Erro: {resultado.get('erro')}")
        
        pix_service.close()
    
    async def process_gift_code(self, update, user, text):
        code = text.strip().upper()
        success = self.gift.redeem(code, user.id)
        await update.message.reply_text("✅ Gift Card resgatado!" if success else "❌ Código inválido!")
        self.states.pop(user.id, None)
    
    async def process_whatsapp(self, update, user, text, db_user):
        if text.lower() == 'remover':
            db_user.whatsapp = None
            self.db.db.commit()
            await update.message.reply_text("✅ WhatsApp removido!")
        elif validate_phone(text):
            db_user.whatsapp = text
            self.db.db.commit()
            await update.message.reply_text(f"✅ WhatsApp salvo: {text}")
        else:
            await update.message.reply_text("❌ Número inválido!")
            return
        self.states.pop(user.id, None)
    
    async def process_search(self, update, user, text):
        products = self.db.get_products()
        found = [p for p in products if text.lower() in p.name.lower()]
        
        if found:
            response = f"🔍 Resultados para '{text}':\n\n"
            for p in found[:10]:
                response += f"📦 {p.name} - R$ {p.price:.2f} ({p.stock} unid.)\n"
            keyboard = []
            for p in found[:5]:
                keyboard.append([InlineKeyboardButton(f"Comprar {p.name}", callback_data=f'product_{p.id}')])
            keyboard.append([InlineKeyboardButton("Voltar", callback_data='back_main')])
            await update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("Nenhum produto encontrado.")
        self.states.pop(user.id, None)
    
    async def process_multi_buy_custom(self, update, user, text, state, db_user):
        product_id = int(state.replace('awaiting_multi_buy_', ''))
        try:
            quantity = int(text)
            if quantity <= 0:
                await update.message.reply_text("❌ Quantidade inválida!")
                return
            
            product = self.db.get_product(product_id)
            if not product or quantity > product.stock:
                await update.message.reply_text("❌ Estoque insuficiente!")
                self.states.pop(user.id, None)
                return
            
            total = product.price * quantity
            if db_user.balance < total:
                falta = total - db_user.balance
                keyboard = [[InlineKeyboardButton(f"Gerar PIX de R$ {total:.2f}", callback_data=f'pix_generate_{total}')]]
                await update.message.reply_text(f"❌ Saldo insuficiente! Falta R$ {falta:.2f}", reply_markup=InlineKeyboardMarkup(keyboard))
                self.states.pop(user.id, None)
                return
            
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar", callback_data=f'multi_buy_execute_{product_id}_{quantity}')],
                [InlineKeyboardButton("❌ Cancelar", callback_data=f'product_{product_id}')]
            ]
            await update.message.reply_text(
                f"🛒 Confirmar {quantity}x {product.name}\n💰 Total: R$ {total:.2f}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            self.states.pop(user.id, None)
        except ValueError:
            await update.message.reply_text("❌ Digite um número válido!")
    
    async def handle_admin_edit_response(self, update, user, text, state):
        if user.id != ADMIN_ID:
            return
        
        field = state.replace('admin_editing_', '')
        field_map = {
            'support': 'support_link', 'separator': 'separator', 'mp_token': 'mp_access_token',
            'deposit_min': 'deposit_min', 'deposit_max': 'deposit_max', 'expiration': 'pix_expiration',
            'bonus': 'bonus_percentage', 'bonus_min': 'bonus_min_value', 'commission': 'commission_percentage',
            'registration_bonus': 'registration_bonus', 'welcome_text': 'welcome_text', 'welcome_image': 'welcome_image',
            'about_text': 'about_text', 'terms_text': 'terms_text', 'btn1_text': 'btn1_text', 'btn2_text': 'btn2_text',
            'btn3_text': 'btn3_text', 'btn4_text': 'btn4_text',
        }
        
        if field_map.get(field):
            self.db.set_setting(field_map[field], text)
            await update.message.reply_text(f"✅ {field} atualizado!")
        else:
            await update.message.reply_text(f"✅ Comando processado!")
        
        self.states.pop(user.id, None)
    
    def close(self):
        self.db.close()
        self.pix.close()
        self.gift.close()
        self.affiliate.close()
        self.login.close()

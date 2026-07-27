from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_manager import DBManager
from services.pix_service import PixService
from services.gift_service import GiftService
from services.affiliate_service import AffiliateService
from services.login_service import LoginService
from utils.helpers import validate_phone, validate_amount, validate_email
from config.settings import ADMIN_ID
from datetime import datetime

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
        
        await self.send_main_menu(update, db_user)
    
    async def handle_state_response(self, update, user, text, state, db_user):
        if text.lower() == 'cancelar':
            self.states.pop(user.id, None)
            await update.message.reply_text("❌ Operação cancelada.")
            await self.send_main_menu(update, db_user)
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
            await update.message.reply_text(
                f"❌ Valor inválido!\n\nMínimo: R$ {min_val:.2f}\nMáximo: R$ {max_val:.2f}\n\nDigite novamente ou 'cancelar' para sair."
            )
            return
        
        amount = float(text)
        self.states.pop(user.id, None)
        
        await update.message.reply_text("⏳ Gerando PIX...")
        
        from services.pix_service import PixService
        pix_service = PixService()
        resultado = pix_service.gerar_pix(db_user.id, amount, "Recarga de saldo")
        
        if not resultado['sucesso']:
            await update.message.reply_text(
                f"❌ Erro ao gerar PIX: {resultado.get('erro', 'Tente novamente')}"
            )
            pix_service.close()
            return
        
        bonus_pct = float(self.db.get_setting('bonus_percentage', '0'))
        bonus_min = float(self.db.get_setting('bonus_min_value', '0'))
        bonus = amount * (bonus_pct/100) if amount >= bonus_min and bonus_pct > 0 else 0
        
        caption = (
            f"💰 *Comprar Saldo com Pix Automático*\n\n"
            f"⏱️ Expira em: {resultado['expiracao_minutos']} Minutos\n"
            f"💵 Valor: R$ {amount:.2f}\n"
            f"✨ ID da Recarga: {resultado['pix_id']}\n\n"
            f"📃 Atenção: Este código é válido para apenas um único pagamento.\n\n"
            f"💎 Pix Copia e Cola:\n"
            f"`{resultado['copia_cola']}`\n\n"
            f"📊 Dados:\n"
            f"— 💰 Saldo Atual: R$ {db_user.balance:.2f}\n"
        )
        
        if bonus > 0:
            caption += f"— 🎁 Bônus à receber: R$ {bonus:.2f}\n"
            caption += f"— 💸 Saldo após o pagamento: R$ {db_user.balance + amount + bonus:.2f}\n"
        else:
            caption += f"— 💸 Saldo após o pagamento: R$ {db_user.balance + amount:.2f}\n"
        
        caption += "\n🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'pix_check_{resultado["pix_id"]}')],
            [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{resultado["pix_id"]}')]
        ]
        
        if resultado.get('qr_code_imagem'):
            try:
                await update.message.reply_photo(
                    photo=resultado['qr_code_imagem'],
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            except:
                await update.message.reply_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        pix_service.close()
    
    async def process_gift_code(self, update, user, text):
        code = text.strip().upper()
        success = self.gift.redeem(code, user.id)
        
        if success:
            await update.message.reply_text("✅ Gift Card resgatado com sucesso!")
        else:
            await update.message.reply_text("❌ Código inválido ou já utilizado!")
        
        self.states.pop(user.id, None)
    
    async def process_whatsapp(self, update, user, text, db_user):
        if text.lower() == 'remover':
            db_user.whatsapp = None
            self.db.db.commit()
            await update.message.reply_text("✅ WhatsApp removido com sucesso!")
        elif validate_phone(text):
            db_user.whatsapp = text
            self.db.db.commit()
            await update.message.reply_text(f"✅ WhatsApp salvo: {text}")
        else:
            await update.message.reply_text(
                "❌ Número inválido!\n\nEnvie apenas números com DDD (10-13 dígitos).\nExemplo: 11999998888\n\nDigite 'remover' para apagar ou 'cancelar' para sair."
            )
            return
        
        self.states.pop(user.id, None)
    
    async def process_search(self, update, user, text):
        products = self.db.get_products()
        found = [p for p in products if text.lower() in p.name.lower()]
        
        if found:
            response = f"🔍 *Resultados para '{text}':*\n\n"
            for p in found[:10]:
                response += f"📦 *{p.name}*\n"
                response += f"💰 R$ {p.price:.2f} | 📦 {p.stock} unid.\n"
                if p.description:
                    response += f"📝 {p.description[:100]}\n"
                response += "\n"
            
            keyboard = []
            for p in found[:5]:
                keyboard.append([InlineKeyboardButton(f"💳 Comprar {p.name}", callback_data=f'product_{p.id}')])
            keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='back_main')])
            
            await update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"❌ Nenhum produto encontrado para '{text}'.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back_main')]])
            )
        
        self.states.pop(user.id, None)
    
    async def process_multi_buy_custom(self, update, user, text, state, db_user):
        product_id = int(state.replace('awaiting_multi_buy_', ''))
        
        try:
            quantity = int(text)
            if quantity <= 0:
                await update.message.reply_text("❌ Quantidade deve ser maior que zero!")
                return
            
            product = self.db.get_product(product_id)
            if not product:
                await update.message.reply_text("❌ Produto não encontrado!")
                self.states.pop(user.id, None)
                return
            
            if quantity > product.stock:
                await update.message.reply_text(
                    f"❌ Estoque insuficiente!\n\nDisponível: {product.stock} unid.\nSolicitado: {quantity} unid.\n\nDigite uma quantidade menor ou 'cancelar' para sair."
                )
                return
            
            total = product.price * quantity
            
            if db_user.balance < total:
                falta = total - db_user.balance
                await update.message.reply_text(
                    f"❌ *Saldo insuficiente!*\n\n"
                    f"💰 Seu saldo: R$ {db_user.balance:.2f}\n"
                    f"💵 Valor total: R$ {total:.2f}\n"
                    f"📉 Faltam: R$ {falta:.2f}\n"
                    f"📦 Quantidade: {quantity} unid.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"Gerar PIX de R$ {total:.2f}", callback_data=f'pix_generate_{total}')],
                        [InlineKeyboardButton("Cancelar", callback_data=f'product_{product_id}')]
                    ]),
                    parse_mode='Markdown'
                )
                self.states.pop(user.id, None)
                return
            
            # Confirmar
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar", callback_data=f'multi_buy_execute_{product_id}_{quantity}')],
                [InlineKeyboardButton("❌ Cancelar", callback_data=f'product_{product_id}')]
            ]
            
            await update.message.reply_text(
                f"🛒 *Confirmar Compra Múltipla*\n\n"
                f"📦 Produto: *{product.name}*\n"
                f"📦 Quantidade: {quantity} unid.\n"
                f"💰 Preço unitário: R$ {product.price:.2f}\n"
                f"💵 Valor total: R$ {total:.2f}\n"
                f"💳 Seu saldo: R$ {db_user.balance:.2f}\n"
                f"💸 Saldo após compra: R$ {db_user.balance - total:.2f}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            self.states.pop(user.id, None)
            
        except ValueError:
            await update.message.reply_text("❌ Digite um número válido ou 'cancelar' para sair.")
    
    async def handle_admin_edit_response(self, update, user, text, state):
        if user.id != ADMIN_ID:
            return
        
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
            'btn5_text': 'btn5_text',
            'btn6_text': 'btn6_text',
            'btn7_text': 'btn7_text',
            'btn8_text': 'btn8_text',
            'btn1_pos': 'btn1_pos',
            'btn2_pos': 'btn2_pos',
            'btn3_pos': 'btn3_pos',
            'btn4_pos': 'btn4_pos',
        }
        
        if field == 'buttons':
            parts = text.split('\n')
            if len(parts) >= 1:
                btns = parts[0].split('|')
                for i, btn in enumerate(btns[:8], 1):
                    self.db.set_setting(f'btn{i}_text', btn.strip())
                await update.message.reply_text("✅ Botões atualizados!")
        elif field == 'positions':
            parts = text.split('\n')
            if len(parts) >= 1:
                poss = parts[0].split('|')
                for i, pos in enumerate(poss[:4], 1):
                    self.db.set_setting(f'btn{i}_pos', pos.strip())
                await update.message.reply_text("✅ Posições atualizadas!")
        elif field_map.get(field):
            self.db.set_setting(field_map[field], text)
            await update.message.reply_text(f"✅ {field} atualizado com sucesso!")
        else:
            await update.message.reply_text(f"✅ Comando processado!")
        
        self.states.pop(user.id, None)
    
    async def send_main_menu(self, update, db_user):
        user = update.effective_user
        
        welcome = self.db.get_setting('welcome_text', 'Bem-vindo!')
        image = self.db.get_setting('welcome_image', '')
        
        text = welcome if welcome else "Bem-vindo!"
        text += f"\n\n💠 Seus Dados:\n├👤 ID: {user.id}\n└💰 Saldo: R$ {db_user.balance:.2f}"
        
        btn1 = self.db.get_setting('btn1_text', '🛍️ Comprar Produtos')
        btn2 = self.db.get_setting('btn2_text', '👤 Meu Perfil')
        btn3 = self.db.get_setting('btn3_text', '💰 Recarregar')
        btn4 = self.db.get_setting('btn4_text', '💼 Afiliado')
        btn5 = self.db.get_setting('btn5_text', '🏆 Top')
        btn6 = self.db.get_setting('btn6_text', '🔍 Pesquisar')
        btn7 = self.db.get_setting('btn7_text', '👤 Atendimento')
        btn8 = self.db.get_setting('btn8_text', 'ℹ️ Sobre')
        
        pos1 = self.db.get_setting('btn1_pos', 'full')
        pos2 = self.db.get_setting('btn2_pos', 'left')
        pos3 = self.db.get_setting('btn3_pos', 'right')
        pos4 = self.db.get_setting('btn4_pos', 'full')
        
        keyboard = []
        
        row1 = [InlineKeyboardButton(btn1, callback_data='menu_products')]
        keyboard.append(row1)
        
        row2 = []
        if pos2 in ['left', 'full']:
            row2.append(InlineKeyboardButton(btn2, callback_data='menu_profile'))
        if pos3 in ['right', 'full']:
            row2.append(InlineKeyboardButton(btn3, callback_data='menu_recharge'))
        if row2:
            keyboard.append(row2)
        
        row3 = [InlineKeyboardButton(btn4, callback_data='menu_affiliate')]
        keyboard.append(row3)
        
        row4 = [
            InlineKeyboardButton(btn5, callback_data='menu_top'),
            InlineKeyboardButton(btn6, callback_data='menu_search')
        ]
        keyboard.append(row4)
        
        row5 = [
            InlineKeyboardButton(btn7, callback_data='menu_support'),
            InlineKeyboardButton(btn8, callback_data='menu_about')
        ]
        keyboard.append(row5)
        
        reply = InlineKeyboardMarkup(keyboard)
        
        if image:
            try:
                await update.message.reply_photo(photo=image, caption=text, reply_markup=reply)
            except:
                await update.message.reply_text(text, reply_markup=reply)
        else:
            await update.message.reply_text(text, reply_markup=reply)
    
    def close(self):
        self.db.close()
        self.gift.close()
        self.affiliate.close()
        self.login.close()
        self.pix.close()

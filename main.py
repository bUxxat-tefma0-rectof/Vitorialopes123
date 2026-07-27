import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
from database.models import init_db
from database.db_manager import DBManager

db = DBManager()
waiting = {}
user_selected = {}

def build_keyboard():
    p1 = db.get_setting('btn1_pos', 'full')
    p2 = db.get_setting('btn2_pos', 'left')
    p3 = db.get_setting('btn3_pos', 'right')
    p4 = db.get_setting('btn4_pos', 'full')
    p5 = db.get_setting('btn5_pos', 'left')
    p6 = db.get_setting('btn6_pos', 'right')
    p7 = db.get_setting('btn7_pos', 'left')
    p8 = db.get_setting('btn8_pos', 'right')
    
    b1 = db.get_setting('btn1_text', '🛍️ Comprar Produtos')
    b2 = db.get_setting('btn2_text', '👤 Meu Perfil')
    b3 = db.get_setting('btn3_text', '💰 Recarregar Saldo')
    b4 = db.get_setting('btn4_text', '💼 Afiliado')
    b5 = db.get_setting('btn5_text', '🏆 Top Compras')
    b6 = db.get_setting('btn6_text', '🔍 Pesquisar Serviços')
    b7 = db.get_setting('btn7_text', '👤 Atendimento')
    b8 = db.get_setting('btn8_text', 'ℹ️ Sobre o Bot')
    
    kb = []
    kb.append([InlineKeyboardButton(b1, callback_data='m1')])
    
    r2 = []
    if p2 in ['left', 'full']: r2.append(InlineKeyboardButton(b2, callback_data='m2'))
    if p3 in ['right', 'full']: r2.append(InlineKeyboardButton(b3, callback_data='m3'))
    if r2: kb.append(r2)
    
    kb.append([InlineKeyboardButton(b4, callback_data='m4')])
    
    r4 = []
    if p5 in ['left', 'full']: r4.append(InlineKeyboardButton(b5, callback_data='m5'))
    if p6 in ['right', 'full']: r4.append(InlineKeyboardButton(b6, callback_data='m6'))
    if r4: kb.append(r4)
    
    r5 = []
    if p7 in ['left', 'full']: r5.append(InlineKeyboardButton(b7, callback_data='m7'))
    if p8 in ['right', 'full']: r5.append(InlineKeyboardButton(b8, callback_data='m8'))
    if r5: kb.append(r5)
    
    return kb

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
    
    w = db.get_setting('welcome_text', 'Bem-vindo!')
    w = w.replace('{id}', str(user.id))
    w = w.replace('{saldo}', f'R$ {db_user.balance:.2f}')
    w = w.replace('{nome}', user.first_name or 'Usuário')
    
    img = db.get_setting('welcome_image', '')
    kb = build_keyboard()
    reply = InlineKeyboardMarkup(kb)
    
    if img:
        try:
            await update.message.reply_photo(photo=img, caption=w, reply_markup=reply)
        except:
            await update.message.reply_text(w, reply_markup=reply)
    else:
        await update.message.reply_text(w, reply_markup=reply)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    user = q.from_user
    db_user = db.get_user(user.id)
    
    # ============ COMPRAR PRODUTOS ============
    if d == 'm1':
        products = db.get_products()
        bal = db_user.balance if db_user else 0
        
        text = "📱 *Lari Contas | Catálogo de Serviços*\n"
        text += "🔗🔗🔗🔗🔗🔗🔗🔗🔗🔗🔗\n\n"
        text += f"💰| Saldo da Carteira: R$ {bal:.2f}\n\n"
        text += "⬇️ Selecione uma categoria abaixo para ver nossos planos:"
        
        if products:
            categories = list(set(p.category for p in products if p.category))
            keyboard = []
            for cat in categories:
                keyboard.append([InlineKeyboardButton(cat, callback_data=f'cat_{cat}')])
            keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='back')])
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await q.edit_message_text(text + "\n\nNenhum produto disponível.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d.startswith('cat_'):
        cat = d.replace('cat_', '')
        products = db.get_products(cat)
        bal = db_user.balance if db_user else 0
        
        text = f"📱 *{cat}*\n\n"
        text += f"💰| Saldo da Carteira: R$ {bal:.2f}\n\n"
        text += "⬇️ Selecione um produto:"
        
        keyboard = []
        for p in products:
            stock_text = f" ({p.stock} unid.)" if p.stock > 0 else " (ESGOTADO)"
            keyboard.append([InlineKeyboardButton(f"{p.name} - R$ {p.price:.2f}{stock_text}", callback_data=f'prod_{p.id}')])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='m1')])
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d.startswith('prod_'):
        pid = int(d.replace('prod_', ''))
        p = db.get_product(pid)
        bal = db_user.balance if db_user else 0
        
        if not p:
            await q.edit_message_text("Produto não encontrado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m1')]]))
            return
        
        text = f"🔥 *OPORTUNIDADE EXCLUSIVA*\n"
        text += f"🚀 *{p.name}*\n\n"
        text += f"🟢 DISPONÍVEL AGORA\n"
        text += f"├ 💵 Preço: R$ {p.price:.2f}\n"
        text += f"├ 💰 Seu Saldo: R$ {bal:.2f}\n"
        text += f"└ 📦 Estoque: {p.stock}\n\n"
        
        if p.description:
            text += f"📝 Descrição:\n{p.description}\n\n"
        
        text += f"📊 Estatísticas em tempo real:\n"
        text += f"⚡️ Já foram vendidas {p.total_sold} unidades!\n"
        text += f"👀 19 pessoas estão vendo isso agora.\n\n"
        text += f"🛡 Garantia: 30 dias\n"
        text += f"✅ Compra segura. Ao adquirir, concorda com /termos"
        
        keyboard = []
        if p.stock > 0:
            keyboard.append([InlineKeyboardButton("💳 Comprar", callback_data=f'buy_{pid}')])
            keyboard.append([InlineKeyboardButton("🛒 Comprar mais de um", callback_data=f'multi_{pid}')])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data=f'cat_{p.category}')])
        
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d.startswith('buy_'):
        pid = int(d.replace('buy_', ''))
        p = db.get_product(pid)
        bal = db_user.balance if db_user else 0
        
        if not p:
            await q.edit_message_text("Produto não encontrado.")
            return
        
        if bal < p.price:
            falta = p.price - bal
            text = f"❌ *Saldo insuficiente!*\n\n"
            text += f"💰 Seu saldo: R$ {bal:.2f}\n"
            text += f"💵 Valor do produto: R$ {p.price:.2f}\n"
            text += f"📉 Faltam: R$ {falta:.2f}\n\n"
            text += f"💡 Deseja gerar um PIX no valor de R$ {p.price:.2f} para completar a compra?"
            
            keyboard = [
                [InlineKeyboardButton(f"Gerar PIX de R$ {p.price:.2f}", callback_data=f'pixbuy_{p.price}')],
                [InlineKeyboardButton("Cancelar", callback_data=f'prod_{pid}')]
            ]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return
        
        if p.stock <= 0:
            await q.edit_message_text("❌ Produto esgotado!")
            return
        
        # Comprar
        success = db.subtract_balance(user.id, p.price)
        if success:
            db.decrease_stock(pid)
            from services.login_service import LoginService
            ls = LoginService()
            login = ls.get_available(p.name)
            email = login.email if login else ''
            password = login.password if login else ''
            if login: ls.mark_sold(login.id, user.id)
            db.create_purchase(user.id, p.name, p.price, email, password, '')
            ls.close()
            
            text = f"✅ *Compra realizada!*\n\n📦 {p.name}\n💰 R$ {p.price:.2f}"
            if email:
                text += f"\n\n📧 {email}\n🔐 {password}"
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
        else:
            await q.edit_message_text("❌ Erro ao processar compra.")
    
    elif d.startswith('multi_'):
        pid = int(d.replace('multi_', ''))
        p = db.get_product(pid)
        
        text = f"Quantos logins deseja comprar?\n\n📦 Estoque disponível: {p.stock}\n\n💡 Digite /cancelar a qualquer momento para sair."
        waiting[user.id] = f'multi_buy_{pid}'
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f'prod_{pid}')]]))
    
    elif d.startswith('pixbuy_'):
        amount = float(d.replace('pixbuy_', ''))
        await q.edit_message_text("⏳ Gerando pagamento...")
        await generate_pix(update, context, user, amount)
    
    elif d.startswith('pix_'):
        amount = float(d.replace('pix_', ''))
        await generate_pix(update, context, user, amount)
    
    # ============ PERFIL ============
    elif d == 'm2':
        bal = db_user.balance if db_user else 0
        tel = db_user.whatsapp if db_user and db_user.whatsapp else 'Não cadastrado'
        purchases = db_user.total_purchases if db_user else 0
        spent = db_user.total_spent if db_user else 0
        recharged = db_user.total_recharged if db_user else 0
        gifts = db_user.gifts_redeemed if db_user else 0
        
        text = f"👤 *Meu perfil*\n\n"
        text += f"🔍 Veja aqui os detalhes da sua conta:\n\n"
        text += f"- 👤 Informações:\n"
        text += f"🆔 ID da Carteira: {user.id}\n"
        text += f"💰 Saldo Atual: R$ {bal:.2f}\n"
        text += f"📲 Seu Whatsapp: {tel}\n\n"
        text += f"─── 📊 Suas Movimentações:\n"
        text += f"ー 🛒 Compras Realizadas: {purchases}\n"
        text += f"ー 💰 Total Gasto Em Compras: R$ {spent:.2f}\n"
        text += f"ー 💠 Pix Inseridos: R$ {recharged:.2f}\n"
        text += f"ー 🎁 Gifts Resgatados: R$ {gifts:.2f}"
        
        keyboard = [
            [InlineKeyboardButton("📋 Histórico de Compras", callback_data='history')],
            [InlineKeyboardButton("🎁 Resgatar Gift Card", callback_data='gift')],
            [InlineKeyboardButton("✏️ Alterar dados", callback_data='edit_data')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='back')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'history':
        purchases = db.get_user_purchases(user.id)
        if purchases:
            text = f"🛍️ *Histórico de Compras*\n\n"
            for p in purchases[:10]:
                text += f"📦 {p.product_name} - R$ {p.amount:.2f}\n📅 {p.purchase_date.strftime('%d/%m/%Y')}\n\n"
        else:
            text = "Nenhuma compra realizada."
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]), parse_mode='Markdown')
    
    elif d == 'gift':
        waiting[user.id] = 'gift_code'
        await q.edit_message_text("🎁 Digite o código do Gift Card:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]))
    
    elif d == 'edit_data':
        waiting[user.id] = 'edit_whatsapp'
        await q.edit_message_text("📱 Envie seu WhatsApp (DDD+Número) ou 'remover':", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]))
    
    # ============ RECARREGAR ============
    elif d == 'm3':
        bal = db_user.balance if db_user else 0
        recarga_text = db.get_setting('recarga_text', '📍 Opte por 💠 Pix Rápido para que seu saldo seja creditado imediatamente.\n\n💡 Selecione uma opção para recarregar:')
        text = f"🆔| ID da Carteira: {user.id}\n💰| Saldo Disponível: R$ {bal:.2f}\n\n{recarga_text}"
        keyboard = [
            [InlineKeyboardButton("💠 Pix Rápido", callback_data='recarga_pix')],
            [InlineKeyboardButton("↩️ Voltar", callback_data='back')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif d == 'recarga_pix':
        min_val = db.get_setting('deposit_min', '2')
        bonus = db.get_setting('bonus_percentage', '0')
        bonus_min = db.get_setting('bonus_min_value', '10')
        pix_ask = db.get_setting('pix_ask_text', 'ℹ️ Informe o valor que deseja recarregar:\n\n🔻 Recarga mínima: R$ {min}\n\n⚠️ Por favor, envie o valor que deseja recarregar agora.\n\n🎁 Bônus de recarga: {bonus}%\n❗️ Recarga mínima para ganhar o bônus: R$ {bonus_min}')
        pix_ask = pix_ask.replace('{min}', min_val).replace('{bonus}', bonus).replace('{bonus_min}', bonus_min)
        waiting[user.id] = 'recharge_value'
        await q.edit_message_text(pix_ask, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Cancelar", callback_data='m3')]]))
    
    # ============ AFILIADO ============
    elif d == 'm4':
        await q.edit_message_text(f"💼 *Afiliado*\n\n🔗 Seu link:\nt.me/SEUBOT?start={user.id}\n💰 Comissão: 10%\n👥 Indicados: 0", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    # ============ TOP ============
    elif d == 'm5':
        await q.edit_message_text("🏆 *Top Compradores*\n\n🥇 Em breve!\n🥈 Em breve!\n🥉 Em breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    # ============ PESQUISAR ============
    elif d == 'm6':
        await q.edit_message_text("🔍 *Pesquisar*\n\nDigite o nome do produto.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    # ============ ATENDIMENTO ============
    elif d == 'm7':
        sup = db.get_setting('support_link', '@suporte')
        await q.edit_message_text(f"👤 *Atendimento*\n\n📱 {sup}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    # ============ SOBRE ============
    elif d == 'm8':
        about = db.get_setting('about_text', 'Larizinha Store')
        await q.edit_message_text(f"ℹ️ *Sobre*\n\n{about}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    # ============ VOLTAR ============
    elif d == 'back':
        w = db.get_setting('welcome_text', 'Bem-vindo!')
        w = w.replace('{id}', str(user.id)).replace('{saldo}', f'R$ {db_user.balance:.2f}').replace('{nome}', user.first_name or 'Usuário')
        kb = build_keyboard()
        await q.edit_message_text(w, reply_markup=InlineKeyboardMarkup(kb))
    
    # ============ ADMIN ============
    elif d == 'adm_config':
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS", callback_data='adm_config_general')],
            [InlineKeyboardButton("👑 ADMINS", callback_data='adm_config_admins')],
            [InlineKeyboardButton("💼 AFILIADOS", callback_data='adm_config_affiliate')],
            [InlineKeyboardButton("👥 USUÁRIOS", callback_data='adm_config_users')],
            [InlineKeyboardButton("💳 PIX", callback_data='adm_config_pix')],
            [InlineKeyboardButton("📦 LOGINS", callback_data='adm_config_logins')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='adm_back')]
        ]
        await q.edit_message_text("⚙️ *CONFIGURAÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'adm_config_general':
        keyboard = [
            [InlineKeyboardButton("📝 TEXTO BOAS-VINDAS", callback_data='adm_welcome')],
            [InlineKeyboardButton("🖼️ IMAGEM", callback_data='adm_image')],
            [InlineKeyboardButton("📞 SUPORTE", callback_data='adm_support')],
            [InlineKeyboardButton("💰 TEXTO RECARGA", callback_data='adm_recarga_text')],
            [InlineKeyboardButton("💠 TEXTO PIX", callback_data='adm_pix_ask_text')],
            [InlineKeyboardButton("🔘 B1", callback_data='adm_btn1'), InlineKeyboardButton("🔘 B2", callback_data='adm_btn2')],
            [InlineKeyboardButton("🔘 B3", callback_data='adm_btn3'), InlineKeyboardButton("🔘 B4", callback_data='adm_btn4')],
            [InlineKeyboardButton("🔘 B5", callback_data='adm_btn5'), InlineKeyboardButton("🔘 B6", callback_data='adm_btn6')],
            [InlineKeyboardButton("🔘 B7", callback_data='adm_btn7'), InlineKeyboardButton("🔘 B8", callback_data='adm_btn8')],
            [InlineKeyboardButton("📐 POSIÇÕES", callback_data='adm_pos')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='adm_config')]
        ]
        await q.edit_message_text("⚙️ *GERAL*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'adm_config_pix':
        keyboard = [
            [InlineKeyboardButton("🔑 TOKEN", callback_data='adm_mp_token')],
            [InlineKeyboardButton("📥 MÍN", callback_data='adm_deposit_min')],
            [InlineKeyboardButton("📤 MÁX", callback_data='adm_deposit_max')],
            [InlineKeyboardButton("⏰ EXPIRA", callback_data='adm_expiration')],
            [InlineKeyboardButton("🎁 BÔNUS", callback_data='adm_bonus')],
            [InlineKeyboardButton("📊 MÍN BÔNUS", callback_data='adm_bonus_min')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='adm_config')]
        ]
        await q.edit_message_text("💳 *PIX*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'adm_back':
        stats = db.get_stats()
        await q.edit_message_text(f"📊 *DASHBOARD*\n\n👥 {stats['users']}\n💰 R$ {stats.get('total_revenue',0):.2f}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='adm_config')]]), parse_mode='Markdown')
    
    elif d == 'adm_actions':
        keyboard = [
            [InlineKeyboardButton("📦 PRODUTO", callback_data='adm_add_product')],
            [InlineKeyboardButton("📤 TRANSMITIR", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🎁 GIFT", callback_data='adm_gift')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='adm_back')]
        ]
        await q.edit_message_text("🔧 *AÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # Edit actions
    elif d == 'adm_welcome': waiting[user.id]='welcome'; await q.edit_message_text("📝 Texto:")
    elif d == 'adm_image': waiting[user.id]='image'; await q.edit_message_text("🖼️ URL:")
    elif d == 'adm_support': waiting[user.id]='support'; await q.edit_message_text("📞 Suporte:")
    elif d == 'adm_recarga_text': waiting[user.id]='recarga_text'; await q.edit_message_text("💰 Texto recarga:")
    elif d == 'adm_pix_ask_text': waiting[user.id]='pix_ask_text'; await q.edit_message_text("💠 Texto PIX:")
    elif d == 'adm_btn1': waiting[user.id]='btn1'; await q.edit_message_text("🔘 B1:")
    elif d == 'adm_btn2': waiting[user.id]='btn2'; await q.edit_message_text("🔘 B2:")
    elif d == 'adm_btn3': waiting[user.id]='btn3'; await q.edit_message_text("🔘 B3:")
    elif d == 'adm_btn4': waiting[user.id]='btn4'; await q.edit_message_text("🔘 B4:")
    elif d == 'adm_btn5': waiting[user.id]='btn5'; await q.edit_message_text("🔘 B5:")
    elif d == 'adm_btn6': waiting[user.id]='btn6'; await q.edit_message_text("🔘 B6:")
    elif d == 'adm_btn7': waiting[user.id]='btn7'; await q.edit_message_text("🔘 B7:")
    elif d == 'adm_btn8': waiting[user.id]='btn8'; await q.edit_message_text("🔘 B8:")
    elif d == 'adm_pos': waiting[user.id]='pos'; await q.edit_message_text("📐 Posições (8):\nfull|left|right|full|left|right|left|right")
    elif d == 'adm_mp_token': waiting[user.id]='mp_token'; await q.edit_message_text("🔑 Token:")
    elif d == 'adm_deposit_min': waiting[user.id]='deposit_min'; await q.edit_message_text("📥 Mín:")
    elif d == 'adm_deposit_max': waiting[user.id]='deposit_max'; await q.edit_message_text("📤 Máx:")
    elif d == 'adm_expiration': waiting[user.id]='expiration'; await q.edit_message_text("⏰ Expira (min):")
    elif d == 'adm_bonus': waiting[user.id]='bonus'; await q.edit_message_text("🎁 Bônus (%):")
    elif d == 'adm_bonus_min': waiting[user.id]='bonus_min'; await q.edit_message_text("📊 Mín bônus:")
    elif d == 'adm_commission': waiting[user.id]='commission'; await q.edit_message_text("💰 Comissão (%):")
    elif d == 'adm_broadcast': waiting[user.id]='broadcast'; await q.edit_message_text("📤 Mensagem:")
    elif d == 'adm_add_product': waiting[user.id]='add_product'; await q.edit_message_text("📦 NOME|PREÇO|ESTOQUE|CATEGORIA")
    elif d == 'adm_gift': waiting[user.id]='gift'; await q.edit_message_text("🎁 Valor:")
    elif d == 'adm_add_admin': waiting[user.id]='add_admin'; await q.edit_message_text("➕ ID:")
    elif d == 'adm_remove_admin': waiting[user.id]='remove_admin'; await q.edit_message_text("➖ ID:")

async def generate_pix(update, context, user, amount):
    from services.pix_service import PixService
    ps = PixService()
    db_user = db.get_user(user.id)
    result = ps.gerar_pix(db_user.id if db_user else user.id, amount, "Recarga")
    
    if result['sucesso']:
        bonus_pct = float(db.get_setting('bonus_percentage', '0'))
        bonus_min = float(db.get_setting('bonus_min_value', '10'))
        bonus = amount * (bonus_pct/100) if amount >= bonus_min and bonus_pct > 0 else 0
        total = amount + bonus
        
        caption = f"💰 *Comprar Saldo com Pix Automático*\n\n"
        caption += f"⏱️ Expira em: {result['expiracao_minutos']} Minutos\n"
        caption += f"💵 Valor: R$ {amount:.2f}\n"
        caption += f"✨ ID da Recarga: {result['pix_id']}\n\n"
        caption += f"📃 Atenção: Este código é válido para apenas um único pagamento.\n\n"
        caption += f"💎 Pix Copia e Cola:\n`{result['copia_cola']}`\n\n"
        caption += f"💡 Dica: Clique no código acima para copiar.\n\n"
        caption += f"📊 Dados:\n"
        caption += f"— 💰 Saldo Atual: R$ {db_user.balance if db_user else 0:.2f}\n"
        if bonus > 0:
            caption += f"— 🎁 Bônus à receber: R$ {bonus:.2f}\n"
        caption += f"— 💸 Saldo após o pagamento: R$ {(db_user.balance if db_user else 0) + total:.2f}\n\n"
        caption += f"🇧🇷 Após o pagamento, seu saldo será liberado instantaneamente."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'check_{result["pix_id"]}')],
            [InlineKeyboardButton("📋 Copiar PIX", callback_data='none')]
        ]
        
        if hasattr(update, 'callback_query'):
            q = update.callback_query
            if result.get('qr_code_imagem'):
                await q.message.reply_photo(photo=result['qr_code_imagem'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await q.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            if result.get('qr_code_imagem'):
                await update.message.reply_photo(photo=result['qr_code_imagem'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    ps.close()

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Não é admin!")
        return
    stats = db.get_stats()
    keyboard = [
        [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='adm_config')],
        [InlineKeyboardButton("🔧 AÇÕES", callback_data='adm_actions')],
    ]
    await update.message.reply_text(f"👑 *ADMIN*\n\n👥 {stats['users']} usuários\n💰 R$ {stats.get('total_revenue',0):.2f}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text.startswith('/'): return
    
    if user.id == ADMIN_ID and user.id in waiting:
        state = waiting[user.id]
        field_map = {
            'welcome':'welcome_text','image':'welcome_image','support':'support_link',
            'recarga_text':'recarga_text','pix_ask_text':'pix_ask_text',
            'btn1':'btn1_text','btn2':'btn2_text','btn3':'btn3_text','btn4':'btn4_text',
            'btn5':'btn5_text','btn6':'btn6_text','btn7':'btn7_text','btn8':'btn8_text',
            'mp_token':'mp_access_token','deposit_min':'deposit_min','deposit_max':'deposit_max',
            'expiration':'pix_expiration','bonus':'bonus_percentage','bonus_min':'bonus_min_value',
            'commission':'commission_percentage',
        }
        
        if state == 'pos':
            parts = text.split('|')
            for i, p in enumerate(parts[:8], 1):
                if p.strip() in ['full','left','right']:
                    db.set_setting(f'btn{i}_pos', p.strip())
            await update.message.reply_text("✅ Posições salvas!")
        
        elif state == 'broadcast':
            from database.models import SessionLocal, User
            s = SessionLocal(); users = s.query(User).all(); c = 0
            for u in users:
                try: await context.bot.send_message(u.telegram_id, text); c += 1
                except: pass
            s.close(); await update.message.reply_text(f"✅ {c} usuários")
        
        elif state == 'recharge_value':
            try:
                amount = float(text)
                min_val = float(db.get_setting('deposit_min', '2'))
                max_val = float(db.get_setting('deposit_max', '150'))
                if amount < min_val: await update.message.reply_text(f"❌ Mín: R$ {min_val:.2f}")
                elif amount > max_val: await update.message.reply_text(f"❌ Máx: R$ {max_val:.2f}")
                else:
                    await update.message.reply_text("⏳ Gerando pagamento...")
                    await generate_pix(update, context, user, amount)
            except: await update.message.reply_text("❌ Inválido!")
        
        elif state.startswith('multi_buy_'):
            try:
                qty = int(text)
                pid = int(state.replace('multi_buy_', ''))
                p = db.get_product(pid)
                db_user = db.get_user(user.id)
                total = p.price * qty
                bal = db_user.balance if db_user else 0
                
                if qty > p.stock:
                    await update.message.reply_text(f"❌ Estoque: {p.stock}")
                elif bal < total:
                    falta = total - bal
                    text = f"❌ *Saldo insuficiente!*\n\n💰 Seu saldo: R$ {bal:.2f}\n💵 Valor total: R$ {total:.2f}\n📉 Faltam: R$ {falta:.2f}\n\n💡 Deseja gerar um PIX?"
                    keyboard = [
                        [InlineKeyboardButton(f"Gerar PIX de R$ {total:.2f}", callback_data=f'pixbuy_{total}')],
                        [InlineKeyboardButton("Cancelar", callback_data=f'prod_{pid}')]
                    ]
                    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                else:
                    for i in range(qty):
                        db.subtract_balance(user.id, p.price)
                        db.decrease_stock(pid)
                    await update.message.reply_text(f"✅ {qty}x {p.name} comprados!")
            except: await update.message.reply_text("❌ Inválido!")
        
        elif state == 'gift_code':
            from services.gift_service import GiftService
            gs = GiftService()
            if gs.redeem(text.strip().upper(), user.id):
                await update.message.reply_text("✅ Gift resgatado!")
            else:
                await update.message.reply_text("❌ Inválido!")
            gs.close()
        
        elif state == 'edit_whatsapp':
            db_user = db.get_user(user.id)
            if text.lower() == 'remover':
                db_user.whatsapp = None
            else:
                db_user.whatsapp = text
            db.db.commit()
            await update.message.reply_text("✅ Salvo!")
        
        elif state == 'add_product':
            p = text.split('|')
            if len(p) >= 3:
                db.add_product(p[0].strip(), float(p[1]), int(p[2]), p[3].strip() if len(p)>3 else 'Geral')
                await update.message.reply_text("✅ Produto!")
        
        elif state == 'gift':
            try:
                from services.gift_service import GiftService
                gs = GiftService(); g = gs.create_gift(float(text))
                await update.message.reply_text(f"✅ Gift: {g.code}"); gs.close()
            except: await update.message.reply_text("❌ Inválido")
        
        elif state in field_map:
            db.set_setting(field_map[state], text)
            await update.message.reply_text("✅ Salvo!")
        else:
            await update.message.reply_text("✅ OK!")
        
        del waiting[user.id]
        return
    
    await start(update, context)

def main():
    print("🐕 INICIANDO...")
    init_db()
    print("✅ Pronto!")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', admin))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Online!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

if __name__ == '__main__':
    main()

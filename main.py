import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
from database.models import init_db
from database.db_manager import DBManager

db = DBManager()
waiting = {}

# ============ HELPERS ============

def build_keyboard():
    p1 = db.get_setting('btn1_pos', 'full')
    p2 = db.get_setting('btn2_pos', 'left')
    p3 = db.get_setting('btn3_pos', 'right')
    p4 = db.get_setting('btn4_pos', 'full')
    p5 = db.get_setting('btn5_pos', 'left')
    p6 = db.get_setting('btn6_pos', 'right')
    p7 = db.get_setting('btn7_pos', 'left')
    p8 = db.get_setting('btn8_pos', 'right')
    
    b1 = db.get_setting('btn1_text', '🛍️ Comprar')
    b2 = db.get_setting('btn2_text', '👤 Perfil')
    b3 = db.get_setting('btn3_text', '💰 Recarregar')
    b4 = db.get_setting('btn4_text', '💼 Afiliado')
    b5 = db.get_setting('btn5_text', '🏆 Top')
    b6 = db.get_setting('btn6_text', '🔍 Pesquisar')
    b7 = db.get_setting('btn7_text', '👤 Atendimento')
    b8 = db.get_setting('btn8_text', 'ℹ️ Sobre')
    
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

def welcome_text(user, db_user):
    w = db.get_setting('welcome_text', 'Bem-vindo!')
    return w.replace('{id}', str(user.id)).replace('{saldo}', f'R$ {db_user.balance:.2f}').replace('{nome}', user.first_name or 'Usuário')

# ============ START ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
    img = db.get_setting('welcome_image', '')
    kb = build_keyboard()
    reply = InlineKeyboardMarkup(kb)
    w = welcome_text(user, db_user)
    
    if img:
        try: await update.message.reply_photo(photo=img, caption=w, reply_markup=reply)
        except: await update.message.reply_text(w, reply_markup=reply)
    else:
        await update.message.reply_text(w, reply_markup=reply)

# ============ CALLBACK ============

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    user = q.from_user
    db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
    bal = db_user.balance if db_user else 0
    
    # ============ MENU PRINCIPAL ============
    if d == 'm1': await show_catalog(q, user, bal)
    elif d == 'm2': await show_profile(q, user, db_user, bal)
    elif d == 'm3': await show_recharge(q, user, bal)
    elif d == 'm4': await show_affiliate(q, user)
    elif d == 'm5': await q.edit_message_text("🏆 Em breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]))
    elif d == 'm6': await q.edit_message_text("🔍 Em breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]))
    elif d == 'm7': await q.edit_message_text(f"👤 Atendimento\n{db.get_setting('support_link','@suporte')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]))
    elif d == 'm8': await q.edit_message_text(f"ℹ️ {db.get_setting('about_text','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]))
    
    # ============ CATÁLOGO ============
    elif d.startswith('cat_'): await show_products(q, d.replace('cat_',''), bal)
    elif d.startswith('prod_'): await show_product_detail(q, int(d.replace('prod_','')), db_user, bal)
    elif d.startswith('buy_'): await buy_product(q, int(d.replace('buy_','')), db_user, bal)
    elif d.startswith('multi_'): await multi_buy_start(q, int(d.replace('multi_','')))
    elif d.startswith('pixbuy_'): await pix_from_buy(q, float(d.replace('pixbuy_','')), user, bal)
    
    # ============ PERFIL ============
    elif d == 'history': await show_history(q, user)
    elif d == 'gift_redeem':
        waiting[user.id] = 'gift_code'
        await q.edit_message_text("🎁 Digite o código:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]))
    elif d == 'edit_data':
        waiting[user.id] = 'edit_whatsapp'
        await q.edit_message_text("📱 Envie WhatsApp ou 'remover':", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]))
    
    # ============ RECARGA ============
    elif d == 'recarga_pix':
        min_v = db.get_setting('deposit_min','2')
        bonus = db.get_setting('bonus_percentage','0')
        bonus_min = db.get_setting('bonus_min_value','10')
        txt = db.get_setting('pix_ask_text','ℹ️ Informe o valor:\n\n🔻 Mín: R$ {min}\n🎁 Bônus: {bonus}%\n❗️ Mín bônus: R$ {bonus_min}')
        txt = txt.replace('{min}',min_v).replace('{bonus}',bonus).replace('{bonus_min}',bonus_min)
        waiting[user.id] = 'recharge_value'
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Cancelar", callback_data='m3')]]))
    
    # ============ VOLTAR ============
    elif d == 'back':
        w = welcome_text(user, db_user)
        await q.edit_message_text(w, reply_markup=InlineKeyboardMarkup(build_keyboard()))
    
    # ============ ADMIN ============
    elif d == 'adm_config':
        kb = [
            [InlineKeyboardButton("⚙️ GERAL", callback_data='adm_config_general')],
            [InlineKeyboardButton("👑 ADMINS", callback_data='adm_config_admins')],
            [InlineKeyboardButton("💼 AFILIADOS", callback_data='adm_config_affiliate')],
            [InlineKeyboardButton("👥 USUÁRIOS", callback_data='adm_config_users')],
            [InlineKeyboardButton("💳 PIX", callback_data='adm_config_pix')],
            [InlineKeyboardButton("📦 LOGINS", callback_data='adm_config_logins')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='adm_back')]
        ]
        await q.edit_message_text("⚙️ Configurações", reply_markup=InlineKeyboardMarkup(kb))
    
    elif d == 'adm_config_general':
        kb = [
            [InlineKeyboardButton("📝 TEXTO", callback_data='adm_welcome')],
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
        await q.edit_message_text("⚙️ Geral", reply_markup=InlineKeyboardMarkup(kb))
    
    elif d == 'adm_config_pix':
        kb = [
            [InlineKeyboardButton("🔑 TOKEN", callback_data='adm_mp_token')],
            [InlineKeyboardButton("📥 MÍN", callback_data='adm_deposit_min')],
            [InlineKeyboardButton("📤 MÁX", callback_data='adm_deposit_max')],
            [InlineKeyboardButton("⏰ EXPIRA", callback_data='adm_expiration')],
            [InlineKeyboardButton("🎁 BÔNUS", callback_data='adm_bonus')],
            [InlineKeyboardButton("📊 MÍN BÔNUS", callback_data='adm_bonus_min')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='adm_config')]
        ]
        await q.edit_message_text("💳 PIX", reply_markup=InlineKeyboardMarkup(kb))
    
    elif d == 'adm_back':
        s = db.get_stats()
        await q.edit_message_text(f"📊 Dashboard\n👥 {s['users']}\n💰 R$ {s.get('total_revenue',0):.2f}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Config", callback_data='adm_config')]]))
    
    elif d == 'adm_actions':
        kb = [
            [InlineKeyboardButton("📦 PRODUTO", callback_data='adm_add_product')],
            [InlineKeyboardButton("📤 TRANSMITIR", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🎁 GIFT", callback_data='adm_gift')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='adm_back')]
        ]
        await q.edit_message_text("🔧 Ações", reply_markup=InlineKeyboardMarkup(kb))
    
    # Admin edit triggers
    elif d == 'adm_welcome': waiting[user.id]='welcome'; await q.edit_message_text("📝 Texto:")
    elif d == 'adm_image': waiting[user.id]='image'; await q.edit_message_text("🖼️ URL:")
    elif d == 'adm_support': waiting[user.id]='support'; await q.edit_message_text("📞 Suporte:")
    elif d == 'adm_recarga_text': waiting[user.id]='recarga_text'; await q.edit_message_text("💰 Texto recarga:")
    elif d == 'adm_pix_ask_text': waiting[user.id]='pix_ask_text'; await q.edit_message_text("💠 Texto PIX:")
    elif d.startswith('adm_btn'): 
        n = d.replace('adm_btn','')
        waiting[user.id]=f'btn{n}'; await q.edit_message_text(f"🔘 B{n}:")
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

# ============ CATÁLOGO ============

async def show_catalog(q, user, bal):
    products = db.get_products()
    text = f"📱 *Lari Contas | Catálogo de Serviços*\n🔗🔗🔗🔗🔗🔗🔗🔗🔗🔗🔗\n\n💰| Saldo da Carteira: R$ {bal:.2f}\n\n⬇️ Selecione uma categoria abaixo:"
    cats = list(set(p.category for p in products if p.category))
    kb = [[InlineKeyboardButton(c, callback_data=f'cat_{c}')] for c in cats]
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data='back')])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def show_products(q, cat, bal):
    products = db.get_products(cat)
    text = f"📱 *{cat}*\n\n💰| Saldo: R$ {bal:.2f}\n\n⬇️ Selecione um produto:"
    kb = [[InlineKeyboardButton(f"{p.name} — R$ {p.price:.2f}", callback_data=f'prod_{p.id}')] for p in products]
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data='m1')])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def show_product_detail(q, pid, db_user, bal):
    p = db.get_product(pid)
    if not p:
        await q.edit_message_text("Produto não encontrado.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m1')]]))
        return
    
    text = f"🔥 *OPORTUNIDADE EXCLUSIVA*\n🚀 *{p.name}*\n\n"
    text += f"🟢 DISPONÍVEL AGORA\n├ 💵 Preço: R$ {p.price:.2f}\n├ 💰 Seu Saldo: R$ {bal:.2f}\n└ 📦 Estoque: {p.stock}\n\n"
    if p.description: text += f"📝 Descrição:\n{p.description}\n\n"
    text += f"📊 Estatísticas:\n⚡️ Vendidas: {p.total_sold}\n👀 Visualizando: 19\n\n🛡 Garantia: 30 dias\n✅ Compra segura."
    
    kb = []
    if p.stock > 0:
        kb.append([InlineKeyboardButton("💳 Comprar", callback_data=f'buy_{pid}')])
        kb.append([InlineKeyboardButton("🛒 Comprar mais de um", callback_data=f'multi_{pid}')])
    kb.append([InlineKeyboardButton("⬅️ Voltar", callback_data=f'cat_{p.category}')])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def buy_product(q, pid, db_user, bal):
    p = db.get_product(pid)
    if not p: return
    if bal < p.price:
        falta = p.price - bal
        text = f"❌ *Saldo insuficiente!*\n\n💰 Seu saldo: R$ {bal:.2f}\n💵 Valor: R$ {p.price:.2f}\n📉 Faltam: R$ {falta:.2f}\n\n💡 Gerar PIX de R$ {p.price:.2f}?"
        kb = [
            [InlineKeyboardButton(f"💠 Gerar PIX de R$ {p.price:.2f}", callback_data=f'pixbuy_{p.price}')],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f'prod_{pid}')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        return
    if p.stock <= 0:
        await q.edit_message_text("❌ Esgotado!"); return
    
    db.subtract_balance(db_user.id, p.price)
    db.decrease_stock(pid)
    from services.login_service import LoginService
    ls = LoginService()
    login = ls.get_available(p.name)
    email = login.email if login else ''; password = login.password if login else ''
    if login: ls.mark_sold(login.id, db_user.id)
    db.create_purchase(db_user.id, p.name, p.price, email, password, '')
    ls.close()
    
    text = f"✅ *Comprado!*\n📦 {p.name}\n💰 R$ {p.price:.2f}"
    if email: text += f"\n📧 {email}\n🔐 {password}"
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')

async def multi_buy_start(q, pid):
    p = db.get_product(pid)
    if not p: return
    waiting[q.from_user.id] = f'multi_buy_{pid}'
    await q.message.reply_text(f"Quantos logins deseja comprar?\n\n📦 Estoque disponível: {p.stock}\n\n💡 Digite /cancelar para sair.")

async def pix_from_buy(q, amount, user, bal):
    await q.edit_message_text("⏳ Gerando pagamento...")
    await generate_pix(q.message, user, amount, bal)

# ============ PERFIL ============

async def show_profile(q, user, db_user, bal):
    tel = db_user.whatsapp or 'Não cadastrado'
    text = f"👤 *Meu perfil*\n\n🔍 Veja aqui os detalhes da sua conta:\n\n"
    text += f"👤 Informações:\n🆔 ID: {user.id}\n💰 Saldo: R$ {bal:.2f}\n📲 WhatsApp: {tel}\n\n"
    text += f"─── 📊 Movimentações:\nー 🛒 Compras: {db_user.total_purchases}\nー 💰 Gasto: R$ {db_user.total_spent:.2f}\n"
    text += f"ー 💠 Pix: R$ {db_user.total_recharged:.2f}\nー 🎁 Gifts: R$ {db_user.gifts_redeemed:.2f}"
    
    kb = [
        [InlineKeyboardButton("📜 Histórico", callback_data='history')],
        [InlineKeyboardButton("🎁 Gift Card", callback_data='gift_redeem')],
        [InlineKeyboardButton("✏️ Alterar dados", callback_data='edit_data')],
        [InlineKeyboardButton("⬅️ Voltar", callback_data='back')]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def show_history(q, user):
    purchases = db.get_user_purchases(user.id)
    if purchases:
        text = "📜 *Histórico*\n\n"
        for p in purchases[:10]:
            text += f"📦 {p.product_name} - R$ {p.amount:.2f}\n📅 {p.purchase_date.strftime('%d/%m/%Y')}\n\n"
    else:
        text = "Nenhuma compra."
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m2')]]), parse_mode='Markdown')

# ============ RECARGA ============

async def show_recharge(q, user, bal):
    txt = db.get_setting('recarga_text','📍 Pix Rápido')
    text = f"🆔 ID: {user.id}\n💰 Saldo: R$ {bal:.2f}\n\n{txt}"
    kb = [
        [InlineKeyboardButton("💠 Pix Rápido", callback_data='recarga_pix')],
        [InlineKeyboardButton("↩️ Voltar", callback_data='back')]
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ============ AFILIADO ============

async def show_affiliate(q, user):
    await q.edit_message_text(f"💼 *Afiliado*\n\n🔗 t.me/bot?start={user.id}\n💰 Comissão: 10%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')

# ============ PIX ============

async def generate_pix(msg, user, amount, bal):
    from services.pix_service import PixService
    ps = PixService()
    result = ps.gerar_pix(user.id, amount, "Recarga")
    
    if result['sucesso']:
        bonus_pct = float(db.get_setting('bonus_percentage','0'))
        bonus_min = float(db.get_setting('bonus_min_value','10'))
        bonus = amount*(bonus_pct/100) if amount>=bonus_min and bonus_pct>0 else 0
        total = amount+bonus
        
        caption = f"💰 *Comprar Saldo com Pix Automático*\n\n"
        caption += f"⏱️ Expira em: {result['expiracao_minutos']} Minutos\n💵 Valor: R$ {amount:.2f}\n✨ ID: {result['pix_id']}\n\n"
        caption += f"📃 Código válido para apenas um pagamento.\n\n"
        caption += f"💎 Pix Copia e Cola:\n`{result['copia_cola']}`\n\n💡 Clique para copiar.\n\n"
        caption += f"📊 Dados:\n— 💰 Saldo: R$ {bal:.2f}\n"
        if bonus>0: caption += f"— 🎁 Bônus: R$ {bonus:.2f}\n"
        caption += f"— 💸 Após pagamento: R$ {bal+total:.2f}\n\n🇧🇷 Liberação instantânea."
        
        kb = [
            [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'check_{result["pix_id"]}')],
            [InlineKeyboardButton("📋 Copiar PIX", callback_data='none')]
        ]
        
        if result.get('qr_code_imagem'):
            await msg.reply_photo(photo=result['qr_code_imagem'], caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        else:
            await msg.reply_text(caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    ps.close()

# ============ ADMIN ============

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Não é admin!"); return
    s = db.get_stats()
    kb = [
        [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='adm_config')],
        [InlineKeyboardButton("🔧 AÇÕES", callback_data='adm_actions')],
    ]
    await update.message.reply_text(f"👑 Admin\n👥 {s['users']}\n💰 R$ {s.get('total_revenue',0):.2f}", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ============ MENSAGENS ============

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
            for i,p in enumerate(text.split('|')[:8],1):
                if p.strip() in ['full','left','right']: db.set_setting(f'btn{i}_pos',p.strip())
            await update.message.reply_text("✅ Posições salvas!")
        elif state == 'broadcast':
            from database.models import SessionLocal, User as U
            s=SessionLocal(); users=s.query(U).all(); c=0
            for u in users:
                try: await context.bot.send_message(u.telegram_id,text); c+=1
                except: pass
            s.close(); await update.message.reply_text(f"✅ {c}")
        elif state == 'recharge_value':
            try:
                amount=float(text)
                min_v=float(db.get_setting('deposit_min','2'))
                max_v=float(db.get_setting('deposit_max','150'))
                if amount<min_v: await update.message.reply_text(f"❌ Mín R$ {min_v:.2f}")
                elif amount>max_v: await update.message.reply_text(f"❌ Máx R$ {max_v:.2f}")
                else:
                    await update.message.reply_text("⏳ Gerando...")
                    db_user=db.get_user(user.id)
                    await generate_pix(update.message,user,amount,db_user.balance if db_user else 0)
            except: await update.message.reply_text("❌ Inválido!")
        elif state.startswith('multi_buy_'):
            try:
                qty=int(text); pid=int(state.replace('multi_buy_',''))
                p=db.get_product(pid); db_user=db.get_user(user.id); bal=db_user.balance if db_user else 0
                total=p.price*qty
                if qty>p.stock: await update.message.reply_text(f"❌ Estoque: {p.stock}")
                elif bal<total:
                    falta=total-bal
                    kb=[[InlineKeyboardButton(f"💠 Gerar PIX de R$ {total:.2f}",callback_data=f'pixbuy_{total}')],[InlineKeyboardButton("❌ Cancelar",callback_data=f'prod_{pid}')]]
                    await update.message.reply_text(f"❌ Saldo insuficiente!\n💰 R$ {bal:.2f}\n💵 R$ {total:.2f}\n📉 Faltam R$ {falta:.2f}\n\n💡 Gerar PIX?",reply_markup=InlineKeyboardMarkup(kb),parse_mode='Markdown')
                else:
                    for _ in range(qty): db.subtract_balance(user.id,p.price); db.decrease_stock(pid)
                    await update.message.reply_text(f"✅ {qty}x {p.name}!")
            except: await update.message.reply_text("❌ Inválido!")
        elif state == 'gift_code':
            from services.gift_service import GiftService
            gs=GiftService()
            await update.message.reply_text("✅ Resgatado!" if gs.redeem(text.strip().upper(),user.id) else "❌ Inválido!"); gs.close()
        elif state == 'edit_whatsapp':
            db_user=db.get_user(user.id)
            db_user.whatsapp = None if text.lower()=='remover' else text
            db.db.commit(); await update.message.reply_text("✅ Salvo!")
        elif state == 'add_product':
            p=text.split('|')
            if len(p)>=3: db.add_product(p[0].strip(),float(p[1]),int(p[2]),p[3].strip() if len(p)>3 else 'Geral'); await update.message.reply_text("✅ Produto!")
        elif state == 'gift':
            try:
                from services.gift_service import GiftService
                gs=GiftService(); g=gs.create_gift(float(text)); await update.message.reply_text(f"✅ {g.code}"); gs.close()
            except: await update.message.reply_text("❌ Inválido")
        elif state in field_map:
            db.set_setting(field_map[state],text); await update.message.reply_text("✅ Salvo!")
        else: await update.message.reply_text("✅ OK!")
        del waiting[user.id]; return
    
    await start(update,context)

def main():
    print("🐕 INICIANDO..."); init_db(); print("✅ Pronto!")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start',start))
    app.add_handler(CommandHandler('admin',admin))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))
    print("✅ Online!")
    app.run_polling(allowed_updates=Update.ALL_TYPES,close_loop=False)

if __name__=='__main__': main()

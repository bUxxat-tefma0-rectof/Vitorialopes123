import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
from database.models import init_db
from database.db_manager import DBManager

db = DBManager()
waiting = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
    
    w = db.get_setting('welcome_text', 'Bem-vindo!')
    # Substituir variáveis
    w = w.replace('{id}', str(user.id))
    w = w.replace('{saldo}', f'R$ {db_user.balance:.2f}')
    w = w.replace('{nome}', user.first_name or 'Usuário')
    w = w.replace('{username}', f'@{user.username}' if user.username else '')
    
    img = db.get_setting('welcome_image', '')
    
    keyboard = [
        [InlineKeyboardButton(db.get_setting('btn1_text', '🛍️ Comprar'), callback_data='m1')],
        [InlineKeyboardButton(db.get_setting('btn2_text', '👤 Perfil'), callback_data='m2'),
         InlineKeyboardButton(db.get_setting('btn3_text', '💰 Recarregar'), callback_data='m3')],
        [InlineKeyboardButton(db.get_setting('btn4_text', '💼 Afiliado'), callback_data='m4')],
        [InlineKeyboardButton(db.get_setting('btn5_text', '🏆 Top'), callback_data='m5'),
         InlineKeyboardButton(db.get_setting('btn6_text', '🔍 Pesquisar'), callback_data='m6')],
        [InlineKeyboardButton(db.get_setting('btn7_text', '👤 Atendimento'), callback_data='m7'),
         InlineKeyboardButton(db.get_setting('btn8_text', 'ℹ️ Sobre'), callback_data='m8')],
    ]
    
    reply = InlineKeyboardMarkup(keyboard)
    
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
    
    if d == 'm1':
        await q.edit_message_text("🛍️ *Catálogo*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm2':
        user = q.from_user
        db_user = db.get_user(user.id)
        bal = db_user.balance if db_user else 0
        await q.edit_message_text(f"👤 *Meu Perfil*\n\n🆔 ID: {user.id}\n💰 Saldo: R$ {bal:.2f}\n📱 WhatsApp: {db_user.whatsapp if db_user else 'Nao cadastrado'}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm3':
        await q.edit_message_text("💰 *Recarregar Saldo*\n\n💠 Pix Rápido disponível!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💠 Gerar PIX", callback_data='pix_start')], [InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm4':
        user = q.from_user
        await q.edit_message_text(f"💼 *Afiliado*\n\n🔗 Seu link:\nt.me/SEUBOT?start={user.id}\n💰 Comissão: 10%\n👥 Indicados: 0", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm5':
        await q.edit_message_text("🏆 *Top Compradores*\n\n🥇 Em breve!\n🥈 Em breve!\n🥉 Em breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm6':
        await q.edit_message_text("🔍 *Pesquisar*\n\nDigite o nome do produto:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm7':
        sup = db.get_setting('support_link', '@suporte')
        await q.edit_message_text(f"👤 *Atendimento*\n\n📱 {sup}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm8':
        about = db.get_setting('about_text', 'Bot de vendas.')
        await q.edit_message_text(f"ℹ️ *Sobre*\n\n{about}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'back':
        user = q.from_user
        db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
        w = db.get_setting('welcome_text', 'Bem-vindo!')
        w = w.replace('{id}', str(user.id))
        w = w.replace('{saldo}', f'R$ {db_user.balance:.2f}')
        w = w.replace('{nome}', user.first_name or 'Usuário')
        keyboard = [
            [InlineKeyboardButton(db.get_setting('btn1_text', '🛍️ Comprar'), callback_data='m1')],
            [InlineKeyboardButton(db.get_setting('btn2_text', '👤 Perfil'), callback_data='m2'),
             InlineKeyboardButton(db.get_setting('btn3_text', '💰 Recarregar'), callback_data='m3')],
            [InlineKeyboardButton(db.get_setting('btn4_text', '💼 Afiliado'), callback_data='m4')],
        ]
        await q.edit_message_text(w, reply_markup=InlineKeyboardMarkup(keyboard))
    elif d == 'pix_start':
        await q.edit_message_text("💠 *Gerar PIX*\n\nDigite o valor para recarregar:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m3')]]), parse_mode='Markdown')
    
    # ============ ADMIN ============
    elif d == 'admin_config':
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS", callback_data='admin_config_general')],
            [InlineKeyboardButton("👑 CONFIGURAR ADMINS", callback_data='admin_config_admins')],
            [InlineKeyboardButton("💼 CONFIGURAR AFILIADOS", callback_data='admin_config_affiliate')],
            [InlineKeyboardButton("👥 CONFIGURAR USUARIOS", callback_data='admin_config_users')],
            [InlineKeyboardButton("💳 CONFIGURAR PIX", callback_data='admin_config_pix')],
            [InlineKeyboardButton("📦 CONFIGURAR LOGINS", callback_data='admin_config_logins')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await q.edit_message_text("⚙️ *CONFIGURAÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_general':
        keyboard = [
            [InlineKeyboardButton("📝 MUDAR TEXTO", callback_data='adm_welcome')],
            [InlineKeyboardButton("🖼️ MUDAR IMAGEM", callback_data='adm_image')],
            [InlineKeyboardButton("📞 MUDAR SUPORTE", callback_data='adm_support')],
            [InlineKeyboardButton("🔘 B1", callback_data='adm_btn1'), InlineKeyboardButton("🔘 B2", callback_data='adm_btn2')],
            [InlineKeyboardButton("🔘 B3", callback_data='adm_btn3'), InlineKeyboardButton("🔘 B4", callback_data='adm_btn4')],
            [InlineKeyboardButton("🔘 B5", callback_data='adm_btn5'), InlineKeyboardButton("🔘 B6", callback_data='adm_btn6')],
            [InlineKeyboardButton("🔘 B7", callback_data='adm_btn7'), InlineKeyboardButton("🔘 B8", callback_data='adm_btn8')],
            [InlineKeyboardButton("📐 POSIÇÕES", callback_data='adm_pos')],
            [InlineKeyboardButton("🔧 MANUTENÇÃO", callback_data='admin_toggle_maintenance')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("⚙️ *GERAL*\n\nVariáveis: {id} {saldo} {nome} {username}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_admins':
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR", callback_data='adm_add_admin')],
            [InlineKeyboardButton("➖ REMOVER", callback_data='adm_remove_admin')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("👑 *ADMINS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_affiliate':
        settings = db.get_all_settings()
        keyboard = [
            [InlineKeyboardButton(f"SISTEMA: {settings.get('affiliate_system','on')}", callback_data='admin_toggle_affiliate')],
            [InlineKeyboardButton("💰 MUDAR COMISSÃO", callback_data='adm_commission')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("💼 *AFILIADOS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_users':
        keyboard = [
            [InlineKeyboardButton("📤 TRANSMITIR", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🔍 PESQUISAR", callback_data='adm_search_user')],
            [InlineKeyboardButton("🎁 BÔNUS", callback_data='adm_registration_bonus')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("👥 *USUÁRIOS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_pix':
        keyboard = [
            [InlineKeyboardButton("🔑 TOKEN", callback_data='adm_mp_token')],
            [InlineKeyboardButton("📥 MÍN", callback_data='adm_deposit_min')],
            [InlineKeyboardButton("📤 MÁX", callback_data='adm_deposit_max')],
            [InlineKeyboardButton("⏰ EXPIRA", callback_data='adm_expiration')],
            [InlineKeyboardButton("🎁 BÔNUS", callback_data='adm_bonus')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("💳 *PIX*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_logins':
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR", callback_data='adm_add_login')],
            [InlineKeyboardButton("➖ REMOVER", callback_data='adm_remove_login')],
            [InlineKeyboardButton("💣 ZERAR", callback_data='adm_clear_stock')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("📦 *LOGINS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_back':
        stats = db.get_stats()
        text = f"📊 *DASHBOARD*\n\n👥 {stats['users']}\n💰 R$ {stats.get('total_revenue',0):.2f}\n🛒 {stats['sales']}"
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
            [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_actions':
        keyboard = [
            [InlineKeyboardButton("📦 PRODUTO", callback_data='adm_add_product')],
            [InlineKeyboardButton("📤 TRANSMITIR", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🎁 GIFT", callback_data='adm_gift')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_back')]
        ]
        await q.edit_message_text("🔧 *AÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_toggle_maintenance':
        c = db.get_setting('maintenance_mode','off')
        db.set_setting('maintenance_mode','on' if c=='off' else 'off')
        await q.edit_message_text(f"✅ Manutenção: {'on' if c=='off' else 'off'}")
    
    elif d == 'admin_toggle_affiliate':
        c = db.get_setting('affiliate_system','on')
        db.set_setting('affiliate_system','on' if c=='off' else 'off')
        await q.edit_message_text(f"✅ Afiliado: {'on' if c=='off' else 'off'}")
    
    # Edit actions
    elif d == 'adm_welcome': waiting[q.from_user.id]='welcome'; await q.edit_message_text("📝 Novo texto:\n\nVariáveis: {id} {saldo} {nome} {username}")
    elif d == 'adm_image': waiting[q.from_user.id]='image'; await q.edit_message_text("🖼️ URL da imagem:")
    elif d == 'adm_support': waiting[q.from_user.id]='support'; await q.edit_message_text("📞 Link de suporte:")
    elif d == 'adm_btn1': waiting[q.from_user.id]='btn1'; await q.edit_message_text("🔘 Botão 1:")
    elif d == 'adm_btn2': waiting[q.from_user.id]='btn2'; await q.edit_message_text("🔘 Botão 2:")
    elif d == 'adm_btn3': waiting[q.from_user.id]='btn3'; await q.edit_message_text("🔘 Botão 3:")
    elif d == 'adm_btn4': waiting[q.from_user.id]='btn4'; await q.edit_message_text("🔘 Botão 4:")
    elif d == 'adm_btn5': waiting[q.from_user.id]='btn5'; await q.edit_message_text("🔘 Botão 5:")
    elif d == 'adm_btn6': waiting[q.from_user.id]='btn6'; await q.edit_message_text("🔘 Botão 6:")
    elif d == 'adm_btn7': waiting[q.from_user.id]='btn7'; await q.edit_message_text("🔘 Botão 7:")
    elif d == 'adm_btn8': waiting[q.from_user.id]='btn8'; await q.edit_message_text("🔘 Botão 8:")
    elif d == 'adm_pos': waiting[q.from_user.id]='pos'; await q.edit_message_text("📐 Posições (8):\nfull|left|right|full|left|right|left|right")
    elif d == 'adm_mp_token': waiting[q.from_user.id]='mp_token'; await q.edit_message_text("🔑 Token MP:")
    elif d == 'adm_deposit_min': waiting[q.from_user.id]='deposit_min'; await q.edit_message_text("📥 Mínimo:")
    elif d == 'adm_deposit_max': waiting[q.from_user.id]='deposit_max'; await q.edit_message_text("📤 Máximo:")
    elif d == 'adm_expiration': waiting[q.from_user.id]='expiration'; await q.edit_message_text("⏰ Expiração (min):")
    elif d == 'adm_bonus': waiting[q.from_user.id]='bonus'; await q.edit_message_text("🎁 Bônus (%):")
    elif d == 'adm_commission': waiting[q.from_user.id]='commission'; await q.edit_message_text("💰 Comissão (%):")
    elif d == 'adm_registration_bonus': waiting[q.from_user.id]='registration_bonus'; await q.edit_message_text("🎁 Bônus registro:")
    elif d == 'adm_broadcast': waiting[q.from_user.id]='broadcast'; await q.edit_message_text("📤 Mensagem:")
    elif d == 'adm_search_user': waiting[q.from_user.id]='search_user'; await q.edit_message_text("🔍 ID:")
    elif d == 'adm_add_product': waiting[q.from_user.id]='add_product'; await q.edit_message_text("📦 NOME|PREÇO|ESTOQUE|CATEGORIA")
    elif d == 'adm_gift': waiting[q.from_user.id]='gift'; await q.edit_message_text("🎁 Valor:")
    elif d == 'adm_add_login': waiting[q.from_user.id]='add_login'; await q.edit_message_text("📦 SERVICO|EMAIL|SENHA")
    elif d == 'adm_remove_login': waiting[q.from_user.id]='remove_login'; await q.edit_message_text("➖ SERVICO")
    elif d == 'adm_clear_stock': waiting[q.from_user.id]='clear_stock'; await q.edit_message_text("⚠️ CONFIRMAR para zerar:")
    elif d == 'adm_add_admin': waiting[q.from_user.id]='add_admin'; await q.edit_message_text("➕ ID:")
    elif d == 'adm_remove_admin': waiting[q.from_user.id]='remove_admin'; await q.edit_message_text("➖ ID:")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Não é admin!")
        return
    stats = db.get_stats()
    text = f"📊 *DASHBOARD*\n\n👥 {stats['users']}\n💰 R$ {stats.get('total_revenue',0):.2f}\n🛒 {stats['sales']}"
    keyboard = [
        [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
        [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text.startswith('/'): return
    
    if user.id == ADMIN_ID and user.id in waiting:
        state = waiting[user.id]
        field_map = {
            'welcome':'welcome_text','image':'welcome_image','support':'support_link',
            'btn1':'btn1_text','btn2':'btn2_text','btn3':'btn3_text','btn4':'btn4_text',
            'btn5':'btn5_text','btn6':'btn6_text','btn7':'btn7_text','btn8':'btn8_text',
            'mp_token':'mp_access_token','deposit_min':'deposit_min','deposit_max':'deposit_max',
            'expiration':'pix_expiration','bonus':'bonus_percentage','commission':'commission_percentage',
            'registration_bonus':'registration_bonus',
        }
        if state == 'pos':
            for i,p in enumerate(text.split('|')[:8],1):
                if p.strip() in ['full','left','right']: db.set_setting(f'btn{i}_pos',p.strip())
            await update.message.reply_text("✅ Posições salvas!")
        elif state == 'broadcast':
            from database.models import SessionLocal, User
            s=SessionLocal(); users=s.query(User).all(); c=0
            for u in users:
                try: await context.bot.send_message(u.telegram_id,text); c+=1
                except: pass
            s.close(); await update.message.reply_text(f"✅ {c} usuários")
        elif state == 'add_product':
            p=text.split('|')
            if len(p)>=3: db.add_product(p[0].strip(),float(p[1]),int(p[2]),p[3].strip() if len(p)>3 else 'Geral'); await update.message.reply_text("✅ Produto!")
        elif state == 'gift':
            try:
                from services.gift_service import GiftService
                gs=GiftService(); g=gs.create_gift(float(text)); await update.message.reply_text(f"✅ {g.code}"); gs.close()
            except: await update.message.reply_text("❌ Valor inválido")
        elif state == 'search_user':
            try:
                u=db.get_user(int(text))
                if u: await update.message.reply_text(f"👤 {u.telegram_id}\n💰 R$ {u.balance:.2f}\n🛒 {u.total_purchases}")
                else: await update.message.reply_text("❌ Não encontrado")
            except: await update.message.reply_text("❌ Inválido")
        elif state == 'clear_stock':
            if text.upper()=='CONFIRMAR':
                from services.login_service import LoginService
                ls=LoginService(); c=ls.clear_stock(); await update.message.reply_text(f"✅ {c} removidos"); ls.close()
        elif state in field_map:
            db.set_setting(field_map[state],text); await update.message.reply_text("✅ Salvo!")
        else: await update.message.reply_text("✅ OK!")
        del waiting[user.id]
        return
    await start(update, context)

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

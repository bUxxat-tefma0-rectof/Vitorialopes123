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
    img = db.get_setting('welcome_image', '')
    
    text = f"{w}\n\n💠 Seus Dados:\n├👤 ID: {user.id}\n└💰 Saldo: R$ {db_user.balance:.2f}"
    
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
    
    # IMAGEM + TEXTO GRUDADOS (imagem em cima, texto embaixo)
    if img:
        try:
            await update.message.reply_photo(photo=img, caption=text, reply_markup=reply)
        except:
            await update.message.reply_text(text, reply_markup=reply)
    else:
        await update.message.reply_text(text, reply_markup=reply)

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
        text = f"{w}\n\n💠 ID: {user.id}\n💰 Saldo: R$ {db_user.balance:.2f}"
        keyboard = [
            [InlineKeyboardButton(db.get_setting('btn1_text', '🛍️ Comprar'), callback_data='m1')],
            [InlineKeyboardButton(db.get_setting('btn2_text', '👤 Perfil'), callback_data='m2'),
             InlineKeyboardButton(db.get_setting('btn3_text', '💰 Recarregar'), callback_data='m3')],
            [InlineKeyboardButton(db.get_setting('btn4_text', '💼 Afiliado'), callback_data='m4')],
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif d == 'pix_start':
        await q.edit_message_text("💠 *Gerar PIX*\n\nDigite o valor para recarregar:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='m3')]]), parse_mode='Markdown')
    
    # ============ ADMIN CALLBACKS ============
    elif d == 'admin_config':
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS", callback_data='admin_config_general')],
            [InlineKeyboardButton("👑 CONFIGURAR ADMINS", callback_data='admin_config_admins')],
            [InlineKeyboardButton("💼 CONFIGURAR AFILIADOS", callback_data='admin_config_affiliate')],
            [InlineKeyboardButton("👥 CONFIGURAR USUARIOS", callback_data='admin_config_users')],
            [InlineKeyboardButton("💳 CONFIGURAR PIX", callback_data='admin_config_pix')],
            [InlineKeyboardButton("📦 CONFIGURAR LOGINS", callback_data='admin_config_logins')],
            [InlineKeyboardButton("🔍 CONFIGURAR PESQUISA", callback_data='admin_config_search')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await q.edit_message_text("⚙️ *MENU DE CONFIGURAÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_general':
        settings = db.get_all_settings()
        text = f"⚙️ *CONFIGURAÇÕES GERAIS*\n\n📝 Boas-vindas: {settings.get('welcome_text','')[:40]}...\n🔗 Suporte: {settings.get('support_link','')}\n🔧 Manutenção: {settings.get('maintenance_mode','off')}"
        keyboard = [
            [InlineKeyboardButton("📝 MUDAR TEXTO", callback_data='adm_welcome')],
            [InlineKeyboardButton("🖼️ MUDAR IMAGEM", callback_data='adm_image')],
            [InlineKeyboardButton("📞 MUDAR SUPORTE", callback_data='adm_support')],
            [InlineKeyboardButton("🔘 BOTÃO 1", callback_data='adm_btn1'), InlineKeyboardButton("🔘 BOTÃO 2", callback_data='adm_btn2')],
            [InlineKeyboardButton("🔘 BOTÃO 3", callback_data='adm_btn3'), InlineKeyboardButton("🔘 BOTÃO 4", callback_data='adm_btn4')],
            [InlineKeyboardButton("🔘 BOTÃO 5", callback_data='adm_btn5'), InlineKeyboardButton("🔘 BOTÃO 6", callback_data='adm_btn6')],
            [InlineKeyboardButton("🔘 BOTÃO 7", callback_data='adm_btn7'), InlineKeyboardButton("🔘 BOTÃO 8", callback_data='adm_btn8')],
            [InlineKeyboardButton("📐 MUDAR POSIÇÕES", callback_data='adm_pos')],
            [InlineKeyboardButton("🔧 MANUTENÇÃO ON/OFF", callback_data='admin_toggle_maintenance')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_admins':
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR ADM", callback_data='adm_add_admin')],
            [InlineKeyboardButton("➖ REMOVER ADM", callback_data='adm_remove_admin')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("👑 *CONFIGURAR ADMINS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_affiliate':
        settings = db.get_all_settings()
        text = f"💼 *AFILIADOS*\n\nSistema: {settings.get('affiliate_system','on')}\nComissão: {settings.get('commission_percentage','20')}%"
        keyboard = [
            [InlineKeyboardButton(f"SISTEMA ({settings.get('affiliate_system','on')})", callback_data='admin_toggle_affiliate')],
            [InlineKeyboardButton("💰 MUDAR COMISSÃO", callback_data='adm_commission')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_users':
        settings = db.get_all_settings()
        text = f"👥 *USUÁRIOS*\n\nBônus registro: R$ {settings.get('registration_bonus','0.00')}"
        keyboard = [
            [InlineKeyboardButton("📤 TRANSMITIR", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🔍 PESQUISAR", callback_data='adm_search_user')],
            [InlineKeyboardButton("🎁 BÔNUS REGISTRO", callback_data='adm_registration_bonus')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_pix':
        settings = db.get_all_settings()
        text = f"💳 *PIX*\n\nToken: {'✅' if settings.get('mp_access_token') else '❌'}\nMín: R$ {settings.get('deposit_min','1')}\nMáx: R$ {settings.get('deposit_max','150')}\nExpira: {settings.get('pix_expiration','15')}min"
        keyboard = [
            [InlineKeyboardButton("🔑 MUDAR TOKEN", callback_data='adm_mp_token')],
            [InlineKeyboardButton("📥 MUDAR MÍN", callback_data='adm_deposit_min')],
            [InlineKeyboardButton("📤 MUDAR MÁX", callback_data='adm_deposit_max')],
            [InlineKeyboardButton("⏰ MUDAR EXPIRA", callback_data='adm_expiration')],
            [InlineKeyboardButton("🎁 MUDAR BÔNUS", callback_data='adm_bonus')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_logins':
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR LOGIN", callback_data='adm_add_login')],
            [InlineKeyboardButton("➖ REMOVER LOGIN", callback_data='adm_remove_login')],
            [InlineKeyboardButton("💣 ZERAR ESTOQUE", callback_data='adm_clear_stock')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("📦 *CONFIGURAR LOGINS*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_config_search':
        keyboard = [
            [InlineKeyboardButton("📸 ADICIONAR IMAGEM", callback_data='adm_add_image')],
            [InlineKeyboardButton("🗑️ REMOVER IMAGEM", callback_data='adm_remove_image')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='admin_config')]
        ]
        await q.edit_message_text("🔍 *CONFIGURAR PESQUISA*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_back':
        stats = db.get_stats()
        text = f"📊 *DASHBOARD*\n\n👥 Users: {stats['users']}\n💰 Receita: R$ {stats.get('total_revenue',0):.2f}\n🛒 Vendas: {stats['sales']}"
        keyboard = [
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
            [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
            [InlineKeyboardButton("📊 TRANSAÇÕES", callback_data='admin_transactions')]
        ]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_actions':
        keyboard = [
            [InlineKeyboardButton("📦 Adicionar Produto", callback_data='adm_add_product')],
            [InlineKeyboardButton("📤 Transmitir", callback_data='adm_broadcast')],
            [InlineKeyboardButton("🎁 Gift Card", callback_data='adm_gift')],
            [InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]
        ]
        await q.edit_message_text("🔧 *AÇÕES*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif d == 'admin_transactions':
        await q.edit_message_text("📊 *TRANSAÇÕES*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='admin_back')]]), parse_mode='Markdown')
    
    elif d == 'admin_toggle_maintenance':
        current = db.get_setting('maintenance_mode', 'off')
        new = 'on' if current == 'off' else 'off'
        db.set_setting('maintenance_mode', new)
        await q.edit_message_text(f"✅ Manutenção: {new}")
    
    elif d == 'admin_toggle_affiliate':
        current = db.get_setting('affiliate_system', 'on')
        new = 'on' if current == 'off' else 'off'
        db.set_setting('affiliate_system', new)
        await q.edit_message_text(f"✅ Afiliado: {new}")
    
    # ============ EDIT ACTIONS ============
    elif d == 'adm_welcome': waiting[q.from_user.id] = 'welcome'; await q.edit_message_text("📝 Envie o novo texto:")
    elif d == 'adm_image': waiting[q.from_user.id] = 'image'; await q.edit_message_text("🖼️ Envie a URL da imagem:")
    elif d == 'adm_support': waiting[q.from_user.id] = 'support'; await q.edit_message_text("📞 Envie o link de suporte:")
    elif d == 'adm_btn1': waiting[q.from_user.id] = 'btn1'; await q.edit_message_text("🔘 Texto Botão 1:")
    elif d == 'adm_btn2': waiting[q.from_user.id] = 'btn2'; await q.edit_message_text("🔘 Texto Botão 2:")
    elif d == 'adm_btn3': waiting[q.from_user.id] = 'btn3'; await q.edit_message_text("🔘 Texto Botão 3:")
    elif d == 'adm_btn4': waiting[q.from_user.id] = 'btn4'; await q.edit_message_text("🔘 Texto Botão 4:")
    elif d == 'adm_btn5': waiting[q.from_user.id] = 'btn5'; await q.edit_message_text("🔘 Texto Botão 5:")
    elif d == 'adm_btn6': waiting[q.from_user.id] = 'btn6'; await q.edit_message_text("🔘 Texto Botão 6:")
    elif d == 'adm_btn7': waiting[q.from_user.id] = 'btn7'; await q.edit_message_text("🔘 Texto Botão 7:")
    elif d == 'adm_btn8': waiting[q.from_user.id] = 'btn8'; await q.edit_message_text("🔘 Texto Botão 8:")
    elif d == 'adm_pos': waiting[q.from_user.id] = 'pos'; await q.edit_message_text("📐 Posições (8):\nfull|left|right|full|left|right|left|right")
    elif d == 'adm_mp_token': waiting[q.from_user.id] = 'mp_token'; await q.edit_message_text("🔑 Token Mercado Pago:")
    elif d == 'adm_deposit_min': waiting[q.from_user.id] = 'deposit_min'; await q.edit_message_text("📥 Valor mínimo:")
    elif d == 'adm_deposit_max': waiting[q.from_user.id] = 'deposit_max'; await q.edit_message_text("📤 Valor máximo:")
    elif d == 'adm_expiration': waiting[q.from_user.id] = 'expiration'; await q.edit_message_text("⏰ Expiração (min):")
    elif d == 'adm_bonus': waiting[q.from_user.id] = 'bonus'; await q.edit_message_text("🎁 Bônus (%):")
    elif d == 'adm_commission': waiting[q.from_user.id] = 'commission'; await q.edit_message_text("💰 Comissão (%):")
    elif d == 'adm_registration_bonus': waiting[q.from_user.id] = 'registration_bonus'; await q.edit_message_text("🎁 Bônus registro:")
    elif d == 'adm_broadcast': waiting[q.from_user.id] = 'broadcast'; await q.edit_message_text("📤 Mensagem para todos:")
    elif d == 'adm_search_user': waiting[q.from_user.id] = 'search_user'; await q.edit_message_text("🔍 ID do usuário:")
    elif d == 'adm_add_product': waiting[q.from_user.id] = 'add_product'; await q.edit_message_text("📦 NOME|PREÇO|ESTOQUE|CATEGORIA")
    elif d == 'adm_gift': waiting[q.from_user.id] = 'gift'; await q.edit_message_text("🎁 Valor do Gift Card:")
    elif d == 'adm_add_login': waiting[q.from_user.id] = 'add_login'; await q.edit_message_text("📦 SERVICO|EMAIL|SENHA")
    elif d == 'adm_remove_login': waiting[q.from_user.id] = 'remove_login'; await q.edit_message_text("➖ SERVICO|EMAIL")
    elif d == 'adm_clear_stock': waiting[q.from_user.id] = 'clear_stock'; await q.edit_message_text("⚠️ Digite CONFIRMAR para zerar:")
    elif d == 'adm_add_admin': waiting[q.from_user.id] = 'add_admin'; await q.edit_message_text("➕ ID do novo admin:")
    elif d == 'adm_remove_admin': waiting[q.from_user.id] = 'remove_admin'; await q.edit_message_text("➖ ID do admin:")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Não é admin!")
        return
    
    stats = db.get_stats()
    text = f"📊 *DASHBOARD*\n\n👥 Users: {stats['users']}\n💰 Receita: R$ {stats.get('total_revenue',0):.2f}\n🛒 Vendas: {stats['sales']}"
    keyboard = [
        [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data='admin_config')],
        [InlineKeyboardButton("🔧 AÇÕES", callback_data='admin_actions')],
        [InlineKeyboardButton("📊 TRANSAÇÕES", callback_data='admin_transactions')],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text.startswith('/'): return
    
    if user.id == ADMIN_ID and user.id in waiting:
        state = waiting[user.id]
        
        field_map = {
            'welcome': 'welcome_text', 'image': 'welcome_image', 'support': 'support_link',
            'btn1': 'btn1_text', 'btn2': 'btn2_text', 'btn3': 'btn3_text', 'btn4': 'btn4_text',
            'btn5': 'btn5_text', 'btn6': 'btn6_text', 'btn7': 'btn7_text', 'btn8': 'btn8_text',
            'mp_token': 'mp_access_token', 'deposit_min': 'deposit_min', 'deposit_max': 'deposit_max',
            'expiration': 'pix_expiration', 'bonus': 'bonus_percentage', 'commission': 'commission_percentage',
            'registration_bonus': 'registration_bonus',
        }
        
        if state == 'pos':
            parts = text.split('|')
            for i, p in enumerate(parts[:8], 1):
                if p.strip() in ['full','left','right']:
                    db.set_setting(f'btn{i}_pos', p.strip())
            await update.message.reply_text("✅ Posições salvas!")
        elif state == 'broadcast':
            from database.models import SessionLocal, User
            session = SessionLocal()
            users = session.query(User).all()
            count = 0
            for u in users:
                try: await context.bot.send_message(u.telegram_id, text); count += 1
                except: pass
            session.close()
            await update.message.reply_text(f"✅ {count} usuários")
        elif state == 'add_product':
            parts = text.split('|')
            if len(parts) >= 3:
                db.add_product(parts[0].strip(), float(parts[1]), int(parts[2]), parts[3].strip() if len(parts)>3 else 'Geral')
                await update.message.reply_text("✅ Produto adicionado!")
        elif state == 'gift':
            try:
                from services.gift_service import GiftService
                gs = GiftService()
                gift = gs.create_gift(float(text))
                await update.message.reply_text(f"✅ Gift: `{gift.code}` - R$ {text}", parse_mode='Markdown')
                gs.close()
            except: await update.message.reply_text("❌ Valor inválido")
        elif state == 'search_user':
            try:
                u = db.get_user(int(text))
                if u: await update.message.reply_text(f"👤 ID: {u.telegram_id}\n💰 R$ {u.balance:.2f}\n🛒 {u.total_purchases} compras")
                else: await update.message.reply_text("❌ Não encontrado")
            except: await update.message.reply_text("❌ ID inválido")
        elif state == 'clear_stock':
            if text.upper() == 'CONFIRMAR':
                from services.login_service import LoginService
                ls = LoginService()
                c = ls.clear_stock()
                await update.message.reply_text(f"✅ {c} logins removidos!")
                ls.close()
        elif state in field_map:
            db.set_setting(field_map[state], text)
            await update.message.reply_text(f"✅ Salvo!")
        else:
            await update.message.reply_text("✅ Comando processado!")
        
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

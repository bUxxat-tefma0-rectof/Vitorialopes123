import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler as TgMessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN, ADMIN_ID
from database.models import init_db
from database.db_manager import DBManager

db = DBManager()
waiting = {}

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
    
    if d == 'm1':
        await q.edit_message_text("🛍️ *Catálogo*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm2':
        db_user = db.get_user(user.id)
        bal = db_user.balance if db_user else 0
        tel = db_user.whatsapp if db_user and db_user.whatsapp else 'Não cadastrado'
        await q.edit_message_text(f"👤 *Meu Perfil*\n\n🆔 ID: {user.id}\n💰 Saldo: R$ {bal:.2f}\n📱 WhatsApp: {tel}\n🛒 Compras: {db_user.total_purchases if db_user else 0}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm3':
        db_user = db.get_user(user.id)
        bal = db_user.balance if db_user else 0
        recarga_text = db.get_setting('recarga_text', '📍 Opte por 💠 Pix Rápido para que seu saldo seja creditado imediatamente.\n\n💡 Selecione uma opção para recarregar:')
        
        text = f"🆔| ID da Carteira: {user.id}\n💰| Saldo Disponível: R$ {bal:.2f}\n\n{recarga_text}"
        
        btn_pix = db.get_setting('recarga_btn_pix', '💠 Pix Rápido')
        btn_voltar = db.get_setting('recarga_btn_voltar', '↩️ Voltar')
        
        keyboard = [
            [InlineKeyboardButton(btn_pix, callback_data='recarga_pix')],
            [InlineKeyboardButton(btn_voltar, callback_data='back')]
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
    
    elif d == 'm4':
        await q.edit_message_text(f"💼 *Afiliado*\n\n🔗 Seu link:\nt.me/SEUBOT?start={user.id}\n💰 Comissão: 10%\n👥 Indicados: 0", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm5':
        await q.edit_message_text("🏆 *Top Compradores*\n\n🥇 Em breve!\n🥈 Em breve!\n🥉 Em breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm6':
        await q.edit_message_text("🔍 *Pesquisar*\n\nDigite o nome do produto.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm7':
        sup = db.get_setting('support_link', '@suporte')
        await q.edit_message_text(f"👤 *Atendimento*\n\n📱 {sup}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'm8':
        about = db.get_setting('about_text', 'Larizinha Store')
        await q.edit_message_text(f"ℹ️ *Sobre*\n\n{about}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    
    elif d == 'back':
        db_user = db.get_user(user.id) or db.create_user(user.id, user.username, user.first_name)
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
            [InlineKeyboardButton("📝 MUDAR TEXTO", callback_data='adm_welcome')],
            [InlineKeyboardButton("🖼️ MUDAR IMAGEM", callback_data='adm_image')],
            [InlineKeyboardButton("📞 MUDAR SUPORTE", callback_data='adm_support')],
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
    elif d == 'adm_welcome': waiting[user.id]='welcome'; await q.edit_message_text("📝 Texto boas-vindas:")
    elif d == 'adm_image': waiting[user.id]='image'; await q.edit_message_text("🖼️ URL imagem:")
    elif d == 'adm_support': waiting[user.id]='support'; await q.edit_message_text("📞 Suporte:")
    elif d == 'adm_recarga_text': waiting[user.id]='recarga_text'; await q.edit_message_text("💰 Texto recarga:")
    elif d == 'adm_pix_ask_text': waiting[user.id]='pix_ask_text'; await q.edit_message_text("💠 Texto PIX:\n\nVariáveis: {min} {bonus} {bonus_min}")
    elif d == 'adm_btn1': waiting[user.id]='btn1'; await q.edit_message_text("🔘 B1:")
    elif d == 'adm_btn2': waiting[user.id]='btn2'; await q.edit_message_text("🔘 B2:")
    elif d == 'adm_btn3': waiting[user.id]='btn3'; await q.edit_message_text("🔘 B3:")
    elif d == 'adm_btn4': waiting[user.id]='btn4'; await q.edit_message_text("🔘 B4:")
    elif d == 'adm_btn5': waiting[user.id]='btn5'; await q.edit_message_text("🔘 B5:")
    elif d == 'adm_btn6': waiting[user.id]='btn6'; await q.edit_message_text("🔘 B6:")
    elif d == 'adm_btn7': waiting[user.id]='btn7'; await q.edit_message_text("🔘 B7:")
    elif d == 'adm_btn8': waiting[user.id]='btn8'; await q.edit_message_text("🔘 B8:")
    elif d == 'adm_pos': waiting[user.id]='pos'; await q.edit_message_text("📐 Posições (8):\nfull|left|right|full|left|right|left|right")
    elif d == 'adm_mp_token': waiting[user.id]='mp_token'; await q.edit_message_text("🔑 Token MP:")
    elif d == 'adm_deposit_min': waiting[user.id]='deposit_min'; await q.edit_message_text("📥 Mínimo:")
    elif d == 'adm_deposit_max': waiting[user.id]='deposit_max'; await q.edit_message_text("📤 Máximo:")
    elif d == 'adm_expiration': waiting[user.id]='expiration'; await q.edit_message_text("⏰ Expiração (min):")
    elif d == 'adm_bonus': waiting[user.id]='bonus'; await q.edit_message_text("🎁 Bônus (%):")
    elif d == 'adm_bonus_min': waiting[user.id]='bonus_min'; await q.edit_message_text("📊 Mín p/ bônus:")
    elif d == 'adm_commission': waiting[user.id]='commission'; await q.edit_message_text("💰 Comissão (%):")
    elif d == 'adm_broadcast': waiting[user.id]='broadcast'; await q.edit_message_text("📤 Mensagem:")
    elif d == 'adm_add_product': waiting[user.id]='add_product'; await q.edit_message_text("📦 NOME|PREÇO|ESTOQUE|CATEGORIA")
    elif d == 'adm_gift': waiting[user.id]='gift'; await q.edit_message_text("🎁 Valor:")
    elif d == 'adm_add_admin': waiting[user.id]='add_admin'; await q.edit_message_text("➕ ID:")
    elif d == 'adm_remove_admin': waiting[user.id]='remove_admin'; await q.edit_message_text("➖ ID:")

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
                
                if amount < min_val:
                    await update.message.reply_text(f"❌ Valor mínimo: R$ {min_val:.2f}")
                elif amount > max_val:
                    await update.message.reply_text(f"❌ Valor máximo: R$ {max_val:.2f}")
                else:
                    await update.message.reply_text("⏳ Gerando pagamento...")
                    
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
                            [InlineKeyboardButton("🔄 Aguardando Pagamento", callback_data=f'pix_check_{result["pix_id"]}')],
                            [InlineKeyboardButton("📋 Copiar PIX", callback_data=f'pix_copy_{result["pix_id"]}')]
                        ]
                        
                        if result.get('qr_code_imagem'):
                            await update.message.reply_photo(photo=result['qr_code_imagem'], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                        else:
                            await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"❌ Erro ao gerar PIX")
                    ps.close()
            except:
                await update.message.reply_text("❌ Valor inválido!")
        
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

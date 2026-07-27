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
    
    # TEXTO PRIMEIRO
    await update.message.reply_text(text, reply_markup=reply)
    
    # IMAGEM COLADA DEPOIS
    if img:
        try:
            await update.message.reply_photo(photo=img)
        except:
            pass

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
        await q.edit_message_text(f"👤 *Meu Perfil*\n\n🆔 ID: {user.id}\n💰 Saldo: R$ {bal:.2f}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm3':
        await q.edit_message_text("💰 *Recarregar*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm4':
        await q.edit_message_text(f"💼 *Afiliado*\n\nSeu link: t.me/bot?start={q.from_user.id}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm5':
        await q.edit_message_text("🏆 *Top*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm6':
        await q.edit_message_text("🔍 *Pesquisar*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm7':
        await q.edit_message_text("👤 *Atendimento*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
    elif d == 'm8':
        await q.edit_message_text("ℹ️ *Sobre*\n\nEm breve!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data='back')]]), parse_mode='Markdown')
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
    elif d == 'adm_welcome':
        waiting[q.from_user.id] = 'welcome'
        await q.edit_message_text("📝 Envie o novo texto:")
    elif d == 'adm_image':
        waiting[q.from_user.id] = 'image'
        await q.edit_message_text("🖼️ Envie a URL da imagem:")
    elif d == 'adm_btn1':
        waiting[q.from_user.id] = 'btn1'
        await q.edit_message_text("🔘 Texto Botão 1:")
    elif d == 'adm_btn2':
        waiting[q.from_user.id] = 'btn2'
        await q.edit_message_text("🔘 Texto Botão 2:")
    elif d == 'adm_btn3':
        waiting[q.from_user.id] = 'btn3'
        await q.edit_message_text("🔘 Texto Botão 3:")
    elif d == 'adm_btn4':
        waiting[q.from_user.id] = 'btn4'
        await q.edit_message_text("🔘 Texto Botão 4:")
    elif d == 'adm_btn5':
        waiting[q.from_user.id] = 'btn5'
        await q.edit_message_text("🔘 Texto Botão 5:")
    elif d == 'adm_btn6':
        waiting[q.from_user.id] = 'btn6'
        await q.edit_message_text("🔘 Texto Botão 6:")
    elif d == 'adm_btn7':
        waiting[q.from_user.id] = 'btn7'
        await q.edit_message_text("🔘 Texto Botão 7:")
    elif d == 'adm_btn8':
        waiting[q.from_user.id] = 'btn8'
        await q.edit_message_text("🔘 Texto Botão 8:")
    elif d == 'adm_pos':
        waiting[q.from_user.id] = 'pos'
        await q.edit_message_text("📐 Posições (8):\nfull|left|right|full|left|right|left|right")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Não é admin!")
        return
    keyboard = [
        [InlineKeyboardButton("📝 MUDAR TEXTO", callback_data='adm_welcome')],
        [InlineKeyboardButton("🖼️ MUDAR IMAGEM", callback_data='adm_image')],
        [InlineKeyboardButton("🔘 B1", callback_data='adm_btn1'), InlineKeyboardButton("🔘 B2", callback_data='adm_btn2')],
        [InlineKeyboardButton("🔘 B3", callback_data='adm_btn3'), InlineKeyboardButton("🔘 B4", callback_data='adm_btn4')],
        [InlineKeyboardButton("🔘 B5", callback_data='adm_btn5'), InlineKeyboardButton("🔘 B6", callback_data='adm_btn6')],
        [InlineKeyboardButton("🔘 B7", callback_data='adm_btn7'), InlineKeyboardButton("🔘 B8", callback_data='adm_btn8')],
        [InlineKeyboardButton("📐 POSIÇÕES", callback_data='adm_pos')],
    ]
    await update.message.reply_text("👑 *ADMIN*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text.startswith('/'): return
    
    if user.id == ADMIN_ID and user.id in waiting:
        state = waiting[user.id]
        if state == 'welcome': db.set_setting('welcome_text', text); await update.message.reply_text("✅ Salvo!")
        elif state == 'image': db.set_setting('welcome_image', text); await update.message.reply_text("✅ Salvo!")
        elif state.startswith('btn'):
            db.set_setting(f'btn{state.replace("btn","")}_text', text)
            await update.message.reply_text("✅ Salvo!")
        elif state == 'pos':
            parts = text.split('|')
            for i, p in enumerate(parts[:8], 1):
                if p.strip() in ['full','left','right']:
                    db.set_setting(f'btn{i}_pos', p.strip())
            await update.message.reply_text("✅ Salvo!")
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

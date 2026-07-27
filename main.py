import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config.settings import BOT_TOKEN
from database.models import init_db
from database.db_manager import DBManager

db = DBManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = db.get_user(user.id)
    if not db_user:
        db_user = db.create_user(user.id, user.username, user.first_name)
    
    welcome = db.get_setting('welcome_text', 'Bem-vindo!')
    image = db.get_setting('welcome_image', '')
    support = db.get_setting('support_link', '')
    
    text = welcome
    text += f"\n\nSeus Dados:\nID: {user.id}\nSaldo: R$ {db_user.balance:.2f}"
    
    keyboard = []
    
    btn1 = db.get_setting('btn1_text', 'Comprar Produtos')
    btn2 = db.get_setting('btn2_text', 'Meu Perfil')
    btn3 = db.get_setting('btn3_text', 'Recarregar')
    btn4 = db.get_setting('btn4_text', 'Afiliado')
    
    pos1 = db.get_setting('btn1_pos', 'full')
    pos2 = db.get_setting('btn2_pos', 'left')
    pos3 = db.get_setting('btn3_pos', 'right')
    pos4 = db.get_setting('btn4_pos', 'full')
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    row1 = [InlineKeyboardButton(btn1, callback_data='menu_products')]
    
    row2 = []
    if pos2 in ['left', 'full']:
        row2.append(InlineKeyboardButton(btn2, callback_data='menu_profile'))
    if pos3 in ['right', 'full']:
        row2.append(InlineKeyboardButton(btn3, callback_data='menu_recharge'))
    
    row3 = [InlineKeyboardButton(btn4, callback_data='menu_affiliate')]
    
    keyboard = [r for r in [row1, row2, row3] if r]
    
    reply = InlineKeyboardMarkup(keyboard)
    
    if image:
        await update.message.reply_photo(photo=image, caption=text, reply_markup=reply)
    else:
        await update.message.reply_text(text, reply_markup=reply)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    print("Iniciando bot...")
    init_db()
    print("Banco pronto!")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot rodando!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

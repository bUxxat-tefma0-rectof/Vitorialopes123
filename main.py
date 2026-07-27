def run(self):
    print("🐕 INICIANDO BOT...")
    init_db()
    print("✅ Banco pronto!")
    
    self.app = Application.builder().token(BOT_TOKEN).build()
    self.app.add_handler(CommandHandler('start', self.start_command))
    self.app.add_handler(CommandHandler('admin', self.admin_handlers.admin_panel))
    self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    self.app.add_handler(TgMessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    self.scheduler = Scheduler(self.app.bot)
    self.scheduler.start()
    
    self.webhook = WebhookServer(self.app.bot)
    self.webhook.run(port=5000)
    
    print("✅ Bot iniciado!")
    self.app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

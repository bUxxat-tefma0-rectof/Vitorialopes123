from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.alert_service import AlertService
from services.backup_service import BackupService
from database.db_manager import DBManager
from datetime import datetime

class Scheduler:
    def __init__(self, bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.alert_service = AlertService()
        self.backup_service = BackupService()
        self.db = DBManager()
    
    def start(self):
        self.scheduler.add_job(self.check_expired_pix, 'interval', minutes=1)
        self.scheduler.add_job(self.check_alerts, 'interval', minutes=5)
        self.scheduler.add_job(self.do_backup, 'interval', hours=1)
        self.scheduler.add_job(self.clean_expired_purchases, 'interval', hours=6)
        self.scheduler.start()
        print("✅ Agendador iniciado!")
    
    async def check_expired_pix(self):
        from database.models import SessionLocal, PixRecharge
        db = SessionLocal()
        
        expired = db.query(PixRecharge).filter(
            PixRecharge.status == 'pending',
            PixRecharge.expires_at < datetime.now()
        ).all()
        
        for pix in expired:
            pix.status = 'expired'
            try:
                await self.bot.send_message(
                    pix.user_id,
                    f"⏰ PIX expirado!\n\n"
                    f"🆔 ID: {pix.pix_id}\n"
                    f"💰 Valor: R$ {pix.amount:.2f}\n\n"
                    f"Gere um novo PIX pelo menu."
                )
            except:
                pass
        
        db.commit()
        db.close()
    
    async def check_alerts(self):
        await self.alert_service.check_and_notify(self.bot)
    
    async def do_backup(self):
        result = self.backup_service.create_backup()
        if result:
            print(f"💾 Backup: {result}")
    
    async def clean_expired_purchases(self):
        from database.models import SessionLocal, Purchase
        db = SessionLocal()
        
        expired = db.query(Purchase).filter(
            Purchase.expiration_date < datetime.now(),
            Purchase.status == 'active'
        ).all()
        
        for p in expired:
            p.status = 'expired'
        
        db.commit()
        db.close()
    
    def stop(self):
        self.scheduler.shutdown()

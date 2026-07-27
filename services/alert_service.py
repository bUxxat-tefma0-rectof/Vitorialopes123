from database.db_manager import DBManager

class AlertService:
    def __init__(self):
        self.db = DBManager()
    
    def add_alert(self, user_id, product_id):
        from database.models import SessionLocal, Alert
        db = SessionLocal()
        
        existing = db.query(Alert).filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            existing.active = True
        else:
            alert = Alert(user_id=user_id, product_id=product_id, active=True)
            db.add(alert)
        
        db.commit()
        db.close()
        return True
    
    def remove_alert(self, user_id, product_id):
        from database.models import SessionLocal, Alert
        db = SessionLocal()
        
        alert = db.query(Alert).filter_by(user_id=user_id, product_id=product_id).first()
        if alert:
            alert.active = False
            db.commit()
            db.close()
            return True
        
        db.close()
        return False
    
    def get_user_alerts(self, user_id):
        from database.models import SessionLocal, Alert, Product
        db = SessionLocal()
        
        alerts = db.query(Alert).filter_by(user_id=user_id, active=True).all()
        products = []
        for alert in alerts:
            product = db.query(Product).filter_by(id=alert.product_id).first()
            if product:
                products.append(product)
        
        db.close()
        return products
    
    def check_and_notify(self, bot):
        from database.models import SessionLocal, Alert, Product
        db = SessionLocal()
        
        active_alerts = db.query(Alert).filter_by(active=True).all()
        
        for alert in active_alerts:
            product = db.query(Product).filter_by(id=alert.product_id).first()
            if product and product.stock > 0:
                try:
                    bot.send_message(
                        alert.user_id,
                        f"🔔 Alerta!\n\nO produto *{product.name}* foi abastecido!\n\nEstoque: {product.stock} unid.\nPreco: R$ {product.price:.2f}"
                    )
                    alert.active = False
                except:
                    pass
        
        db.commit()
        db.close()
    
    def close(self):
        self.db.close()

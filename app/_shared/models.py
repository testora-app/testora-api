from datetime import datetime

from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        db.session.commit()

    def delete(self):
        self.is_deleted = 1
        db.session.commit()
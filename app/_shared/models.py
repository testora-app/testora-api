from datetime import datetime, timezone

from app.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def save(self):
        db.session.commit()

    def delete(self):
        self.is_deleted = 1
        db.session.commit()
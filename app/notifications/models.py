from app._shared.models import BaseModel
from app.extensions import db


class Recipient(BaseModel):
    __tablename__ = 'recipient'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(50), nullable=False)
    device_ids = db.Column(db.JSON, nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    notifications = db.relationship("Notification", backref='recipient')

    __table_args__ = (
        db.UniqueConstraint("category", "email", name="unique_category_email"),
        db.UniqueConstraint(
            "category", "phone_number", name="unique_category_phone_number"
        ),
    )

    def to_json(self):
        return {
            "category": self.category,
            "device_ids": self.device_ids,
            "email": self.email,
            "phone_number": self.phone_number,
        }
    


class Notification(BaseModel):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    attachments = db.Column(db.JSON, nullable=True)
    school_id = db.Column(db.Integer, nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'), nullable=True)


    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'alert_type': self.alert_type,
            'attachments': self.attachments if self.attachments else None,
            'school_id': self.school_id,
        }
    
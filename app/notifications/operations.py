from app.notifications.models import Recipient, Notification
from app._shared.operations import BaseManager

from typing import List


class RecipientManager(BaseManager):
    def create_recipient(self, category, device_ids, email, phone_number) -> Recipient:
        new_recipient = Recipient(
            category=category,
            device_ids=device_ids,
            email=email,
            phone_number=phone_number
        )

        self.save(new_recipient, upsert=True)
        return new_recipient

    def get_recipients(self) -> List[Recipient]:
        return Recipient.query.all()
    
    def get_recipient_by_email(self, email, category) -> Recipient:
        return Recipient.query.filter_by(email=email, category=category).first()
    
    

class NotificationManager(BaseManager):
    def create_notification(self, title, content, alert_type, recipient_id, school_id=None, 
                            attachments=None) -> Notification:
        new_notification = Notification(
            title=title,
            content=content,
            alert_type=alert_type,
            recipient_id=recipient_id,
            school_id=school_id,
            attachments=attachments
        )
        self.save(new_notification)
        return new_notification
    

    def get_recipient_notifications(self, recipient_id) -> List[Notification]:
        return Notification.query.filter_by(recipient_id=recipient_id).all()
    




recipient_manager = RecipientManager()
notification_manager = NotificationManager()

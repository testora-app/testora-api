from app.extensions import db
from app._shared.models import BaseModel

from typing import List

class BaseManager(object):
    @staticmethod
    def save(entity: BaseModel):
        db.session.add(entity)
        db.session.commit()

    @staticmethod
    def save_multiple(entities: List[BaseModel]):
        db.session.add_all(entities)
        db.session.commit()

    

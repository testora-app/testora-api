from app.extensions import db
from app._shared.models import BaseModel

from typing import List

class BaseManager(object):
    @staticmethod
    def save(entity: BaseModel, upsert=False):
        if upsert:
            db.session.merge(entity)
        else:
            db.session.add(entity)
        db.session.commit()

    @staticmethod
    def save_multiple(entities: List[BaseModel]):
        db.session.add_all(entities)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    

from app.extensions import db
from app._shared.models import BaseModel

from typing import List
from logging import info as log_info


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
        try:
            db.session.begin_nested()  # Creates a savepoint
            db.session.add_all(entities)
            db.session.commit()
        except Exception as e:
            log_info(entities)
            db.session.rollback()
            raise e

    @staticmethod
    def commit():
        db.session.commit()

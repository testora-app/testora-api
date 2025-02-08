# crud operations for all 3

from flask_sqlalchemy.pagination import Pagination

from app.admin.models import Admin, Subject, Topic, Theme
from app._shared.operations import BaseManager
from app._shared.services import hash_password

from typing import Dict, List


class AdminManager(BaseManager):
    def create_admin(self, username, email, password, is_super_admin=False):
        new_admin = Admin(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_super_admin=is_super_admin,
        )
        self.save(new_admin)

        return new_admin

    def get_admins(self) -> List[Admin]:
        return Admin.query.all()

    def get_admin_by_email(self, email) -> Admin:
        return Admin.query.filter_by(email=email).first()

    def get_admin_by_id(self, id) -> Admin:
        return Admin.query.get(id)


class SubjectManager(BaseManager):
    def create_subjects(self, entries: List[Dict]) -> List[Subject]:
        entities: List[Subject] = []
        for entry in entries:
            entities.append(
                Subject(
                    name=entry["name"],
                    short_name=entry["short_name"],
                    curriculum=entry["curriculum"],
                )
            )
        self.save_multiple(entities)
        return entities

    def get_subjects(self) -> List[Subject]:
        return Subject.query.filter_by(is_deleted=False).all()

    def get_subjects_paginated(self, page, per_page) -> Pagination:
        return Subject.query.filter_by(is_deleted=False).paginate(
            page=page, per_page=per_page
        )

    def get_subject_by_id(self, id) -> Subject:
        return Subject.query.filter_by(id=id).first()

    def get_subjects_by_ids(self, ids) -> List[Subject]:
        return Subject.query.filter(Subject.id.in_(ids)).all()

    def get_subject_by_curriculum(self, curr) -> List[Subject]:
        return Subject.query.filter_by(curriculum=curr).all()


class TopicManager(BaseManager):
    def create_topics(self, entries: List[Dict]) -> List[Topic]:
        entities: List[Topic] = []
        for entry in entries:
            entities.append(
                Topic(
                    name=entry["name"],
                    short_name=entry["short_name"],
                    level=entry["level"],
                    theme_id=entry["theme_id"],
                    subject_id=entry["subject_id"],
                )
            )

        self.save_multiple(entities)
        return entities

    def get_topics(self) -> List[Topic]:
        return Topic.query.filter_by(is_deleted=False).all()

    def get_topic_by_id(self, id) -> Topic:
        return Topic.query.filter_by(id=id).first()

    def get_topic_by_subject(self, subject_id) -> List[Topic]:
        return Topic.query.filter_by(subject_id=subject_id).all()
    
    def get_topic_by_theme(self, theme_id) -> List[Topic]:
        return Topic.query.filter_by(theme_id=theme_id).all()

    def get_topic_by_level(self, level) -> List[Topic]:
        return Topic.query.filter_by(level=level).all()

    def get_topic_by_subject_level(self, subject_id, level) -> List[Topic]:
        return Topic.query.filter_by(subject_id=subject_id, level=level).all()


class ThemeManager(BaseManager):
    def create_themes(self, entries: List[Dict]) -> List[Theme]:
        entities: List[Theme] = []
        for entry in entries:
            entities.append(
                Theme(
                    name=entry["name"],
                    short_name=entry["short_name"],
                    subject_id=entry["subject_id"],
                )
            )

        self.save_multiple(entities)
        return entities

    def get_themes(self) -> List[Theme]:
        return Theme.query.filter_by(is_deleted=False).all()

    def get_theme_by_id(self, id) -> Theme:
        return Theme.query.filter_by(id=id).first()

    def get_theme_by_subject(self, subject_id) -> List[Theme]:
        return Theme.query.filter_by(subject_id=subject_id).all()


admin_manager = AdminManager()
subject_manager = SubjectManager()
topic_manager = TopicManager()
theme_manager = ThemeManager()

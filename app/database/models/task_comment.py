from datetime import datetime

from app.api.validations.task_comment import COMMENT_MAX_LENGTH
from app.database.sqlalchemy_extension import db


class TaskCommentModel(db.Model):

    __tablename__ = "tasks_comments"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    task_id = db.Column(db.Integer, db.ForeignKey("tasks_list.id"))
    relation_id = db.Column(db.Integer, db.ForeignKey("mentorship_relations.id"))
    creation_date = db.Column(db.Float, nullable=False)
    modification_date = db.Column(db.Float)
    comment = db.Column(db.String(COMMENT_MAX_LENGTH), nullable=False)

    def __init__(self, user_id, task_id, relation_id, comment):

        self.user_id = user_id
        self.task_id = task_id
        self.relation_id = relation_id
        self.comment = comment

        self.creation_date = datetime.utcnow().timestamp()

    def json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "relation_id": self.relation_id,
            "creation_date": self.creation_date,
            "modification_date": self.modification_date,
            "comment": self.comment,
        }

    def __repr__(self):
        return (
            f"User's id is {self.user_id}. Task's id is {self.task_id}. "
            f"Comment was created on: {self.creation_date}\n"
            f"Comment: {self.comment}"
        )

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all_by_task_id(cls, task_id, relation_id):
        return cls.query.filter_by(task_id=task_id, relation_id=relation_id).all()

    @classmethod
    def find_all_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    def modify_comment(self, comment):
        self.comment = comment
        self.modification_date = datetime.utcnow().timestamp()

    @classmethod
    def is_empty(cls):
        return cls.query.first() is None

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

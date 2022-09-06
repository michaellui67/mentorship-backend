from app.database.models.tasks_list import TasksListModel
from app.database.models.user import UserModel
from app.database.sqlalchemy_extension import db
from app.utils.enum_utils import MentorshipRelationState


class MentorshipRelationModel(db.Model):

    __tablename__ = "mentorship_relations"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action_user_id = db.Column(db.Integer, nullable=False)
    mentor = db.relationship(
        UserModel,
        backref="mentor_relations",
        primaryjoin="MentorshipRelationModel.mentor_id == UserModel.id",
    )
    mentee = db.relationship(
        UserModel,
        backref="mentee_relations",
        primaryjoin="MentorshipRelationModel.mentee_id == UserModel.id",
    )

    creation_date = db.Column(db.Float, nullable=False)
    accept_date = db.Column(db.Float)
    start_date = db.Column(db.Float)
    end_date = db.Column(db.Float)

    state = db.Column(db.Enum(MentorshipRelationState), nullable=False)
    notes = db.Column(db.String(400))

    tasks_list_id = db.Column(db.Integer, db.ForeignKey("tasks_list.id"))
    tasks_list = db.relationship(
        TasksListModel, uselist=False, backref="mentorship_relation"
    )

    def __init__(
        self,
        action_user_id,
        mentor_user,
        mentee_user,
        creation_date,
        end_date,
        state,
        notes,
        tasks_list,
    ):

        self.action_user_id = action_user_id
        self.mentor = mentor_user
        self.mentee = mentee_user
        self.creation_date = creation_date
        self.end_date = end_date
        self.state = state
        self.notes = notes
        self.tasks_list = tasks_list

    def json(self):
        return {
            "id": self.id,
            "action_user_id": self.action_user_id,
            "mentor_id": self.mentor_id,
            "mentee_id": self.mentee_id,
            "creation_date": self.creation_date,
            "accept_date": self.accept_date,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "state": self.state,
            "notes": self.notes,
        }

    @classmethod
    def find_by_id(cls, _id) -> "MentorshipRelationModel":
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def is_empty(cls) -> bool:
        return cls.query.first() is None

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        self.tasks_list.delete_from_db()
        db.session.delete(self)
        db.session.commit()

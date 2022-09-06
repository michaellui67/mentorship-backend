from datetime import date
from enum import Enum, unique

from app.database.db_types.JsonCustomType import JsonCustomType
from app.database.sqlalchemy_extension import db


class TasksListModel(db.Model):

    __tablename__ = "tasks_list"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    tasks = db.Column(JsonCustomType)
    next_task_id = db.Column(db.Integer)

    def __init__(self, tasks: "TasksListModel" = None):

        if tasks is None:
            self.tasks = []
            self.next_task_id = 1
        else:
            if isinstance(tasks, list):
                self.tasks = []
                self.next_task_id = len(tasks) + 1
            else:
                raise ValueError(TypeError)

    def add_task(
        self, description: str, created_at: date, is_done=False, completed_at=None
    ) -> None:

        task = {
            TasksFields.ID.value: self.next_task_id,
            TasksFields.DESCRIPTION.value: description,
            TasksFields.IS_DONE.value: is_done,
            TasksFields.CREATED_AT.value: created_at,
            TasksFields.COMPLETED_AT.value: completed_at,
        }
        self.next_task_id += 1
        self.tasks = self.tasks + [task]

    def delete_task(self, task_id: int) -> None:

        new_list = list(
            filter(lambda task: task[TasksFields.ID.value] != task_id, self.tasks)
        )

        self.tasks = new_list
        self.save_to_db()

    def update_task(
        self,
        task_id: int,
        description: str = None,
        is_done: bool = None,
        completed_at: date = None,
    ) -> None:

        new_list = []
        for task in self.tasks:
            if task[TasksFields.ID.value] == task_id:
                new_task = task.copy()
                if description is not None:
                    new_task[TasksFields.DESCRIPTION.value] = description

                if is_done is not None:
                    new_task[TasksFields.IS_DONE.value] = is_done

                if completed_at is not None:
                    new_task[TasksFields.COMPLETED_AT.value] = completed_at

                new_list = new_list + [new_task]
                continue

            new_list = new_list + [task]

        self.tasks = new_list
        self.save_to_db()

    def find_task_by_id(self, task_id: int):

        task = list(
            filter(lambda task: task[TasksFields.ID.value] == task_id, self.tasks)
        )
        if len(task) == 0:
            return None
        else:
            return task[0]

    def is_empty(self) -> bool:

        return len(self.tasks) == 0

    def json(self):

        return {
            "id": self.id,
            "mentorship_relation_id": self.mentorship_relation_id,
            "tasks": self.tasks,
            "next_task_id": self.next_task_id,
        }

    def __repr__(self):

        return f"Task | id = {self.id}; tasks = {self.tasks}; next task id = {self.next_task_id}"

    @classmethod
    def find_by_id(cls, _id: int):

        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()


@unique
class TasksFields(Enum):
    ID = "id"
    DESCRIPTION = "description"
    IS_DONE = "is_done"
    COMPLETED_AT = "completed_at"
    CREATED_AT = "created_at"

    def values(self):
        return list(map(str, self))

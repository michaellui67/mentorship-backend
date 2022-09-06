from flask_restx import Api

from app.api.resources.admin import admin_ns as admin_namespace
from app.api.resources.mentorship_relation import (
    mentorship_relation_ns as mentorship_namespace,
)
from app.api.resources.task import task_ns as task_namespace
from app.api.resources.task_comment import task_comment_ns as task_comment_namespace

from app.api.resources.user import users_ns as user_namespace

api = Api(
    title="Mentorship System API",
    version="1.0",
    description="API documentation for the backend of Mentorship System."
)
api.namespaces.clear()

api.add_namespace(user_namespace, path="/")

api.add_namespace(admin_namespace, path="/")

api.add_namespace(mentorship_namespace, path="/")

api.add_namespace(task_namespace, path="/")

api.add_namespace(task_comment_namespace, path="/")

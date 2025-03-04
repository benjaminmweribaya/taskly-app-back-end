from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import Enum
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")

    tasklists = db.relationship("TaskList", backref="user", cascade="all, delete-orphan")
    tasks_assigned = db.relationship("TaskAssignment", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")
    notifications_enabled = db.Column(db.Boolean, default=True)  

    serialize_rules = (
        "-password",
        "-tasks_assigned.user",
        "-tasklists",
        "-comments.user",
        "-notifications.user"
    )


class TaskList(db.Model, SerializerMixin):
    __tablename__ = "tasklists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tasks = db.relationship("Task", backref="tasklist", cascade="all, delete-orphan")

    serialize_rules = (
        "-user",
        "-tasks.tasklist"
    )


class Task(db.Model, SerializerMixin):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(Enum("low", "medium", "high", name="priority_levels"), default="medium")
    status = db.Column(Enum("pending", "in-progress", "completed", name="task_status"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasklist_id = db.Column(db.Integer, db.ForeignKey("tasklists.id"), nullable=False)
    
    assignments = db.relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="task", cascade="all, delete-orphan")

    serialize_rules = (
        "-tasklist",
        "-assignments",
        "-comments.task"
    )


class TaskAssignment(db.Model, SerializerMixin):
    __tablename__ = "task_assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)

    user = db.relationship("User", back_populates="tasks_assigned")
    task = db.relationship("Task", back_populates="assignments")

    serialize_rules = ("-user", "-task")


class Comment(db.Model, SerializerMixin):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    serialize_rules = ("-task", "-user")


class Notification(db.Model, SerializerMixin):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)  

    serialize_rules = ("-user",)


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)

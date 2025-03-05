from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.dialects.postgresql import ENUM
from datetime import datetime

db = SQLAlchemy()

# Enum types
priority_enum = ENUM("low", "medium", "high", "urgent", name="priority_levels", create_type=True)
status_enum = ENUM("pending", "in-progress", "completed", "todo", name="task_status", create_type=True)

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
    priority = db.Column(priority_enum, nullable=False, default="medium")
    status = db.Column(status_enum, nullable=False, default="todo") 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasklist_id = db.Column(db.Integer, db.ForeignKey("tasklists.id", ondelete="CASCADE"), nullable=False)
    
    assignments = db.relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="task", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="task", cascade="all, delete-orphan")

    serialize_rules = (
        "-tasklist",
        "-assignments",
        "-comments.task",
        "-notifications.task"
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

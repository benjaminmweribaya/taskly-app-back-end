from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    tablename = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    tasklists = db.relationship("TaskList", backref="user", cascade="all, delete-orphan")
    tasks_assigned = db.relationship("TaskAssignment", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")

    serialize_rules = ("-password", "-tasks_assigned.user", "-tasklists.user", "-comments.user", "-notifications.user")


class TaskList(db.Model, SerializerMixin):
    tablename = "tasklists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tasks = db.relationship("Task", backref="tasklist", cascade="all, delete-orphan")

    serialize_rules = ("-user.tasklists", "-tasks.tasklist")


class Task(db.Model, SerializerMixin):
    tablename = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasklist_id = db.Column(db.Integer, db.ForeignKey("tasklists.id"), nullable=False)
    
    assignments = db.relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="task", cascade="all, delete-orphan")

    serialize_rules = ("-tasklist.tasks", "-assignments.task", "-comments.task")


class TaskAssignment(db.Model, SerializerMixin):
    tablename = "task_assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="tasks_assigned")
    task = db.relationship("Task", back_populates="assignments")

    serialize_rules = ("-user.tasks_assigned", "-task.assignments")


class Comment(db.Model, SerializerMixin):
    tablename = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    serialize_rules = ("-task.comments", "-user.comments")


class Notification(db.Model, SerializerMixin):
    tablename = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    serialize_rules = ("-user.notifications",)

from flask import Blueprint, jsonify, request
from models import db, Task
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

task_stats_bp = Blueprint("task_stats_bp", __name__)

@task_stats_bp.route("/api/task-stats", methods=["GET"])
@jwt_required()
def get_task_stats():
    user_id = get_jwt_identity()  

    total_completed = Task.query.filter_by(status="completed").count()
    total_pending = Task.query.filter_by(status="pending").count()
    total_in_progress = Task.query.filter_by(status="in-progress").count()
    total_overdue = Task.query.filter(Task.due_date < datetime.utcnow(), Task.status != "completed").count()

    return jsonify({
        "completed": total_completed,
        "pending": total_pending,
        "inProgress": total_in_progress,
        "overdue": total_overdue
    })

@task_stats_bp.route("/api/upcoming-tasks", methods=["GET"])
@jwt_required()
def get_upcoming_tasks():
    user_id = get_jwt_identity()

    upcoming_tasks = Task.query.filter(Task.due_date >= datetime.utcnow()).order_by(Task.due_date.asc()).limit(5).all()
    return jsonify([{
        "id": task.id,
        "title": task.title,
        "dueDate": task.due_date.strftime("%Y-%m-%d %H:%M:%S") if task.due_date else "No Deadline"
    } for task in upcoming_tasks])


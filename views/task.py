from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task , User ,TaskList ,TaskAssignment
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
task_bp = Blueprint("task_bp", __name__)

def is_admin(user):
    return user.role == "admin"

def get_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def validate_tasklist(tasklist_id):
    return TaskList.query.get(tasklist_id)

# Create a new task
@task_bp.route("/tasks", methods=["POST"])
@jwt_required()
def add_task():
    """Creates a new task."""
    user = get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    tasklist = validate_tasklist(data.get("tasklist_id"))
    if not tasklist:
        return jsonify({"error": "TaskList not found"}), 404

    new_task = Task(
        title=data.get["title"],
        description=data.get("description"),
        due_date=datetime.strptime(data["due_date"], "%Y-%m-%d") if "due_date" in data else None,
        priority=data.get("priority", "medium"),
        status=data.get("status", "pending"),
        created_at=datetime.utcnow(),
        tasklist_id="tasklist_id"
    )

    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict(), 201)


@task_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    """Fetches tasks with filtering options."""
    user = get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    priority = request.args.get("priority")
    status = request.args.get("status")
    due_date = request.args.get("due_date")
    
    query = Task.query
    
    if priority:
        query = query.filter_by(priority=priority)
    if status:
        query = query.filter_by(status=status)
    if due_date:
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
            query = query.filter(Task.due_date == due_date_obj)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}, 400)
    
    tasks = query.all()
    if not tasks:
        return jsonify({"message": "No tasks found matching the filters"}), 404
    return jsonify([task.to_dict() for task in tasks]), 200

# Update a task
@task_bp.route("/tasks/<int:task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    """Updates an existing task with permission checks."""
    user = get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    task = Task.query.filter_by(id=task_id).first_or_404(description="Task not found")
    assignment = TaskAssignment.query.filter_by(task_id=task.id, user_id=user.id).first()
    if user.id != task.tasklist.user_id and not is_admin(user) and not assignment:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    if "status" in data:
        task.status = data["status"]
    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "due_date" in data:
        task.due_date = data["due_date"]
    if "priority" in data:
        task.priority = data["priority"]

    db.session.commit()
    return jsonify(task.to_dict()), 200


# Ensure only admins or task creators can delete tasks
@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    """Deletes a task with authorization."""
    user = get_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    task = Task.query.filter_by(id=task_id).first_or_404(description="Task not found")
    if user.id != task.tasklist.user_id and not is_admin(user):
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"}), 200

# feature task in the landing page
@task_bp.route("/tasks/featured", methods=["GET"])
def get_featured_tasks():
    featured_tasks = []

    for priority in ["low", "medium", "high"]:
        task = Task.query.filter_by(priority=priority).order_by(Task.created_at.desc()).first()
        if task:
            featured_tasks.append(task.to_dict())

    return jsonify(featured_tasks), 200

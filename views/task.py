from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task , User
from datetime import datetime

task_bp = Blueprint("task_bp", __name__)

# Create a new task
@task_bp.route("/tasks", methods=["POST"])
@jwt_required()
def add_task():
    data = request.get_json()
    new_task = Task(
        title=data["title"],
        description=data.get("description"),
        due_date=data.get("due_date"),
        priority=data.get("priority", "medium"),
        status=data.get("status", "pending"),
        created_at=datetime.utcnow(),
        tasklist_id=data["tasklist_id"]
    )
    db.session.add(new_task)
    db.session.commit()
    return make_response(new_task.to_dict()), 201

# Retrieve all tasks (supports filtering)
@task_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    query = Task.query
    priority = request.args.get("priority")
    status = request.args.get("status")
    due_date = request.args.get("due_date")
    
    if priority:
        query = query.filter_by(priority=priority)
    if status:
        query = query.filter_by(status=status)
    if due_date:
        query = query.filter(Task.due_date == due_date)
    
    tasks = query.all()
    if not tasks:
        return make_response({"message": "No tasks found matching the filters"}), 404
    return make_response([task.to_dict() for task in tasks]), 200

# Retrieve a specific task
@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return make_response({"error": "Task not found"}), 404
    return make_response(task.to_dict()), 200


# Update a task
@task_bp.route("/tasks/<int:task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    task = Task.query.get(task_id)
    if not task:
        return make_response({"error": "Task not found"}), 404

    # Ensure only authorized users can update
    is_creator = task.tasklist.user_id == current_user_id
    is_admin = current_user.role == "admin"
    is_assigned = any(assignment.user_id == current_user_id for assignment in task.assignments)

    data = request.get_json()

    # Admins & creators can update anything
    if is_admin or is_creator:
        if "priority" in data:
            task.priority = data["priority"]
        if "due_date" in data:
            task.due_date = data["due_date"]
    
    # Assigned users can only update status
    if is_admin or is_creator or is_assigned:
        if "status" in data:
            task.status = data["status"]
    else:
        return make_response({"error": "You are not authorized to update this task"}), 403

    db.session.commit()
    return make_response(task.to_dict()), 200


# Delete a task
@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return make_response({"error": "Task not found"}), 404
    
    db.session.delete(task)
    db.session.commit()
    return make_response({"message": "Task deleted successfully"}), 200

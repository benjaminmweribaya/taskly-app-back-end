from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task , User ,TaskList ,TaskAssignment
from datetime import datetime

task_bp = Blueprint("task_bp", __name__)

ADMIN_EMAILS = ["sera12@gmail.com"]

# Create a new task
@task_bp.route("/tasks", methods=["POST"])
@jwt_required()
def add_task():
    data = request.get_json()

    # Convert due_date from string to datetime 
    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d")
        except ValueError:
            return make_response({"error": "Invalid date format. Use YYYY-MM-DD."}, 400)

    new_task = Task(
        title=data["title"],
        description=data.get("description"),
        due_date=due_date, 
        priority=data.get("priority", "medium"),
        status=data.get("status", "pending"),
        created_at=datetime.utcnow(),
        tasklist_id=data["tasklist_id"]
    )

    db.session.add(new_task)
    db.session.commit()
    return make_response(new_task.to_dict(), 201)

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

    if not current_user:
        return make_response({"error": "User not found"}), 404

    task = Task.query.get(task_id)
    if not task:
        return make_response({"error": "Task not found"}), 404

    # Fetch the related tasklist properly
    tasklist = TaskList.query.filter_by(id=task.tasklist_id).first()  # Ensure we fetch the tasklist
    is_creator = tasklist and tasklist.user_id == current_user_id
    is_admin = current_user.email in ADMIN_EMAILS
    is_assigned = TaskAssignment.query.filter_by(task_id=task.id, user_id=current_user_id).first() is not None  

    print(f"DEBUG: User: {current_user.email}, Admin: {is_admin}, Creator: {is_creator}, Assigned: {is_assigned}")

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

# feature task in the landing page
@task_bp.route("/tasks/featured", methods=["GET"])
def get_featured_tasks():
    featured_tasks = []

    for priority in ["low", "medium", "high"]:
        task = Task.query.filter_by(priority=priority).order_by(Task.created_at.desc()).first()
        if task:
            featured_tasks.append(task.to_dict())

    return make_response(featured_tasks), 200

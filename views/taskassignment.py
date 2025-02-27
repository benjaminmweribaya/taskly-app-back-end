from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task, TaskAssignment, User, TaskList

taskassignment_bp = Blueprint("taskassignment_bp", __name__)

# Assign multiple users to a task (only for Admins or Task Creators)
@taskassignment_bp.route("/tasks/<int:task_id>/assign", methods=["POST"])
@jwt_required()
def assign_users_to_task(task_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Get task
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Check if the user is an admin OR the creator of the task's tasklist
    tasklist = TaskList.query.filter_by(id=task.tasklist_id, user_id=current_user_id).first()

    if current_user.role != "admin" and not tasklist:
        return jsonify({"error": "You are not authorized to assign users to this task"}), 403

    # Get user IDs from request
    data = request.get_json()
    user_ids = data.get("user_ids", [])

    # Assign users
    assigned_users = []
    for user_id in user_ids:
        user = User.query.get(user_id)
        if user:
            assignment = TaskAssignment(task_id=task.id, user_id=user.id)
            db.session.add(assignment)
            assigned_users.append(user.to_dict())

    db.session.commit()
    return jsonify({"success": "Users assigned successfully", "assigned_users": assigned_users}), 200


# Remove a user from a task (only for Admins or Task Creators)
@taskassignment_bp.route("/tasks/<int:task_id>/assign/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_user_from_task(task_id, user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Get task
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Check if the user is an admin OR the creator of the task's tasklist
    tasklist = TaskList.query.filter_by(id=task.tasklist_id, user_id=current_user_id).first()

    if current_user.role != "admin" and not tasklist:
        return jsonify({"error": "You are not authorized to remove users from this task"}), 403

    # Find and delete the assignment
    assignment = TaskAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
    if not assignment:
        return jsonify({"error": "User is not assigned to this task"}), 404

    db.session.delete(assignment)
    db.session.commit()

    return jsonify({"message": "User removed from task successfully"}), 200

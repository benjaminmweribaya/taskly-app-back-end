from flask import Blueprint, request, jsonify
from models import db, TaskList, Task
from flask_jwt_extended import jwt_required, get_jwt_identity


tasklist_bp = Blueprint('tasklist', __name__, url_prefix='/tasklists')

@tasklist_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_tasklist():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)  
    per_page = request.args.get("per_page", 5, type=int) 
    tasklist = TaskList.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)

    if not tasklist:
        return jsonify({"error": "Task list not found"}), 404
    
    return jsonify([
        {
            "id": tasklist.id, 
            "name": tasklist.name,
            "tasks": [{"id": task.id, "title": task.title} for task in tasklist.tasks]
        } 
        for tasklist in tasklist
    ]), 200


@tasklist_bp.route('/<int:tasklist_id>', methods=['GET'])
@jwt_required()
def get_tasklist(tasklist_id):
    user_id = get_jwt_identity()
    tasklist = TaskList.query.filter_by(id=tasklist_id, user_id=user_id).first()

    if not tasklist:
        return jsonify({"error": "Task list not found"}), 404

    return jsonify({
        "id": tasklist.id, 
        "name": tasklist.name,
        "tasks": [{"id": task.id, "title": task.title} for task in tasklist.tasks]
    }), 200


@tasklist_bp.route('/', methods=['POST'])
@jwt_required()
def create_tasklist():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({"error": "Task list name is required"}), 400

    new_tasklist = TaskList(name=data['name'], user_id=user_id)
    db.session.add(new_tasklist)
    db.session.commit()

    return jsonify({
        "message": "Task list created successfully", 
        "id": new_tasklist.id,
        "name": new_tasklist.name,
        "tasks": []
    }), 201

# Update a task list
@tasklist_bp.route('/<int:tasklist_id>', methods=['PUT'])
@jwt_required()
def update_tasklist(tasklist_id):
    user_id = get_jwt_identity()
    tasklist = TaskList.query.filter_by(id=tasklist_id, user_id=user_id).first()

    if not tasklist:
        return jsonify({"error": "Task list not found"}), 404

    data = request.get_json()
    if 'name' in data:
        tasklist.name = data['name']

    db.session.commit()
    return jsonify({"message": "Task list updated successfully"}), 200

# Delete a task list
@tasklist_bp.route('/<int:tasklist_id>', methods=['DELETE'])
@jwt_required()
def delete_tasklist(tasklist_id):
    user_id = get_jwt_identity()
    tasklist = TaskList.query.filter_by(id=tasklist_id, user_id=user_id).first()

    if not tasklist:
        return jsonify({"error": "Task list not found"}), 404

    db.session.delete(tasklist)
    db.session.commit()
    return jsonify({"message": "Task list deleted successfully"}), 200

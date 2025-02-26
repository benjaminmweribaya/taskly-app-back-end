from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from functools import wraps

user_bp = Blueprint("user_bp", __name__)

# Admin Role Required Decorator
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != "admin":
            return make_response({"error": "Admin access required"}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper

# Get all users (Admin only)
@user_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    users = User.query.all()
    return make_response([user.to_dict() for user in users]), 200

# Get a specific user by ID
@user_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return make_response({"error": "User not found"}), 404
    return make_response(user.to_dict()), 200

# Update user profile
@user_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return make_response({"error": "User not found"}), 404

    current_user_id = get_jwt_identity()
    if user.id != current_user_id:
        return make_response({"error": "Unauthorized"}), 403

    data = request.get_json()
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    
    db.session.commit()
    return make_response({"success": "User updated successfully", "user": user.to_dict()}), 200

# Delete user (Admin only)
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return make_response({"error": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return make_response({"success": "User deleted successfully"}), 200

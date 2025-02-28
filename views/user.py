from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User , TaskList
from functools import wraps

user_bp = Blueprint("user_bp", __name__)


ADMIN_EMAILS = ["sera12@gmail.com"]  # Add more emails if needed

# Admin Role Required Decorator
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)

        if not current_user or current_user.email not in ADMIN_EMAILS:
            return make_response({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return wrapper

# Get all users (Admin and users who created a tasklist only)
@user_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Allow only admins or users who created a tasklist
    created_tasklist = TaskList.query.filter_by(user_id=current_user_id).first()

    if current_user.email in ADMIN_EMAILS or created_tasklist:
        users = User.query.all()
        return make_response(
            [{"id": user.id, "username": user.username, "email": user.email} for user in users]
        ), 200

    return make_response({"error": "You are not authorized to view users"}), 403

# Get a specific user by ID
@user_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return make_response({"error": "User not found"}), 404

    # Return only id, username, and email
    return make_response({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200

# Update user profile
@user_bp.route("/users/updateprofile", methods=["PATCH"])
@jwt_required()
def update_user():
    user_id = get_jwt_identity()
    user = db.session.get(User,user_id)  

    if not user:
        return make_response({"error": "User not found"}), 404  

    data = request.get_json()
    username = data.get("username", user.username)
    email = data.get("email", user.email)

    user.username = username
    user.email = email

    db.session.commit()
    return make_response({"success": "User updated successfully"}), 200


#Delete user account
@user_bp.route("/users/deleteacccount", methods=["DELETE"])
@jwt_required()
def delete_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)  

    if not user:
        return make_response({"error": "User not found"}), 404  

    db.session.delete(user)
    db.session.commit()

    return make_response({"success": "Account deleted successfully"}), 200

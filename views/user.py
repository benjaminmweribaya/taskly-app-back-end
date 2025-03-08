from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User 
from functools import wraps

user_bp = Blueprint("user_bp", __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = db.session.get(User, user_id)

        if not current_user or current_user.role != "admin":
            return make_response({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return jwt_required()(wrapper)  

@user_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    users = User.query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "users": [
            {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
            for user in users.items
        ],
        "total": users.total,
        "pages": users.pages,
        "current_page": users.page,
        "next_page": users.next_num if users.has_next else None,
        "prev_page": users.prev_num if users.has_prev else None
    }), 200


# Get a specific user by ID
@user_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return make_response({"error": "User not found"}), 404

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

    # Ensure new email is unique
    if email != user.email and User.query.filter_by(email=email).first():
        return make_response({"error": "Email already in use"}), 400

    user.username = username
    user.email = email

    db.session.commit()
    return make_response({"success": "User updated successfully"}), 200


#Delete user account
@user_bp.route("/users/deleteaccount", methods=["DELETE"])
@jwt_required()
def delete_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)  

    if not user:
        return make_response({"error": "User not found"}), 404  

    db.session.delete(user)
    db.session.commit()

    return make_response({"success": "Account deleted successfully"}), 200

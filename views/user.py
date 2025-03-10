from flask import Blueprint, request, make_response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User , Workspace , WorkspaceInvite
from flask_mail import Mail, Message
from functools import wraps
import secrets

user_bp = Blueprint("user_bp", __name__)

mail = Mail()

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

@user_bp.route("/invite", methods=["POST"])
@jwt_required()
def invite_user():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    user_id = get_jwt_identity()
    inviter = db.session.get(User, user_id)
    
    if not inviter:
        return jsonify({"error": "Invalid user"}), 404

    workspace = db.session.get(Workspace, inviter.workspace_id) # Adjust based on your logic

    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404
    
    existing_invite = WorkspaceInvite.query.filter_by(email=email, workspace_id=workspace.id).first()
    if existing_invite and existing_invite.status == "pending":
        return jsonify({"error": "Invite already sent"}), 400

    invite_token = secrets.token_urlsafe(32)  # Generate a unique invite token
    invite = WorkspaceInvite(email=email, workspace_id=workspace.id, invited_by=inviter.id, token=invite_token)
    
    db.session.add(invite)
    db.session.commit()

    invite_url = f"https://taskly-app-iota.vercel.app//invite/{invite_token}"  # Update with the correct frontend route

    msg = Message("Workspace Invitation", sender="your-email@example.com", recipients=[email])
    msg.body = f"You've been invited to join {workspace.name}.\nClick here to accept: {invite_url}"
    mail.send(msg)

    return jsonify({"message": "Invitation email sent successfully"}), 200

@user_bp.route("/invite/accept/<int:token>", methods=["POST"])
@jwt_required()
def accept_invite(token):
    invite = WorkspaceInvite.query.filter_by(token=token, status="pending").first()

    if not invite:
        return jsonify({"error": "Invalid or expired invite"}), 404

    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    user.workspace_id = invite.workspace_id  # Add user to workspace
    invite.status = "accepted"

    db.session.commit()

    return jsonify({"message": "Joined workspace successfully!"}), 200

@user_bp.route("/workspace/<int:workspace_id>/members", methods=["GET"])
@jwt_required()
def get_workspace_members(workspace_id):
    workspace = db.session.get(Workspace, workspace_id)

    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    members = User.query.filter_by(workspace_id=workspace.id).all()
    invites = WorkspaceInvite.query.filter_by(workspace_id=workspace.id, status="pending").all()

    return jsonify({
        "members": [{"id": m.id, "username": m.username, "email": m.email} for m in members],
        "pending_invites": [{"email": i.email, "invited_by": i.inviter.username} for i in invites]
    }), 200
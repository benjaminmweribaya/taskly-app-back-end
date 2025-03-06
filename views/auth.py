from flask import make_response, request, Blueprint, jsonify
from models import db, User, TokenBlocklist
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt

auth_bp= Blueprint("auth_bp", __name__)

#signup
@auth_bp.route("/register",methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return make_response(jsonify({"error": "All fields are required"}), 400)
    
    if User.query.filter_by(username=username).first():
        return make_response(jsonify({"error": "Username already exists"}), 409)
    if User.query.filter_by(email=email).first():
        return make_response(jsonify({"error": "Email already exists"}), 409)

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return make_response(jsonify({"success": "User registered successfully"}), 201)

# Login (allow username or email)
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("identifier")
    password = data.get("password")

    if not identifier or not password:
        return make_response(jsonify({"error": "Username/Email and password are required"}), 400)
    
    user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=12))
        refresh_token = create_refresh_token(identity=str(user.id))
        return make_response(jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200)

    return make_response(jsonify({"error": "Invalid email or password"}), 400)


# Refresh Token
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=12))
    return make_response(jsonify({"access_token": new_access_token}), 200)


# Get the logged in user details
@auth_bp.route("/profile", methods=["GET"])    
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user:
        return make_response(jsonify({"username": user.username, "email": user.email}), 200)
    else:
        return make_response(jsonify({"error": "User doesn't exist"}), 404)


# Logout
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    
    if TokenBlocklist.query.filter_by(jti=jti).first():
        return make_response(jsonify({"error": "Token already blacklisted"}), 400)
    
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    return make_response(jsonify({"success": "Logged out successfully"}), 200)

    
from flask import make_response, request, Blueprint
from models import db, User, TokenBlocklist
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

auth_bp= Blueprint("auth_bp", __name__)

#signup
@auth_bp.route("/register",methods=["POST"])
def add_user():
    data = request.get_json()
    username = data["username"]
    email = data["email"]
    password = generate_password_hash(data["password"])
    

    check_name = User.query.filter_by(username=username).first()
    check_email = User.query.filter_by(email=email).first()

    if check_name:
        return make_response({"error": "Username already exists"})
    else:
        if check_email:
            return make_response({"error": "Email already exists"})
        else:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()

            return make_response({"success": "user registered successfully"})

# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        response = make_response({"access_token": access_token})
    else:
        response = make_response({"error": "Invalid email or password"}), 400

    return response


# Get the logged in user details
@auth_bp.route("/profile")    
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user:
        return make_response({"username": user.username, "email": user.email})
    else:
        return make_response({"error": "User doesn't exist"})


# Logout
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    if jti:
        db.session.add(TokenBlocklist(jti=jti, created_at=now))
        db.session.commit()
        return make_response({"success":"Logged out successfully"})
    else:
        return make_response({"error": "User wasn't logged in"})
    
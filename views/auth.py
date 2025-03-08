from flask import make_response, request, Blueprint, jsonify, url_for
from models import db, User, TokenBlocklist, Workspace
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
import uuid
#mport secrets
from flask_mail import Mail, Message
#from flask_dance.contrib.google import make_google_blueprint, google
import os

auth_bp= Blueprint("auth_bp", __name__)

reset_tokens = {}  
mail = Mail()

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
    #send_verification_email(email, verification_token)
    #verification_token = str(uuid.uuid4()) 

    workspace = Workspace(name=f"{username}'s Workspace")
    db.session.add(workspace)
    db.session.commit()
 
    new_user = User(username=username, email=email, password=hashed_password, workspace_id=workspace.id)  #is_verified=False #verification_token=verification_token)
    db.session.add(new_user)
    db.session.commit()

    return make_response(jsonify({
        "success": "User registered successfully", 
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "workspace_id": new_user.workspace_id
        }
    }), 201)

@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({"error": "Invalid verification token"}), 400

    user.is_verified = True
    user.verification_token = None 
    db.session.commit()

    return jsonify({"success": "Email verified successfully. You can now log in."}), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("identifier")
    password = data.get("password")

    if not identifier or not password:
        return make_response(jsonify({"error": "Username/Email and password are required"}), 400)
    
    user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()

    #if user and not user.is_verified:
        #return jsonify({"error": "Please verify your email before logging in."}), 403

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=12))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return make_response(jsonify({
            "access_token": access_token, 
            "refresh_token": refresh_token, 
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "workspace_id": user.workspace_id
            }
        }), 200)

    return make_response(jsonify({"error": "Invalid email or password"}), 400)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=12))
    return make_response(jsonify({"access_token": new_access_token}), 200)


@auth_bp.route("/profile", methods=["GET"])    
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if user:
        return make_response(jsonify({"username": user.username, "email": user.email}), 200)
    else:
        return make_response(jsonify({"error": "User doesn't exist"}), 404)


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

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    reset_token = str(uuid.uuid4())  
    user.reset_token = reset_token
    user.token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    send_reset_email(user, reset_token)

    return jsonify({"message": "Password reset link sent to your email"}), 200

@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    data = request.get_json()
    new_password = data.get("new_password")

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.token_expiry or user.token_expiry < datetime.utcnow():
        return jsonify({"error": "Invalid or expired token"}), 400

    user.password = generate_password_hash(new_password)
    user.reset_token = None  
    user.token_expiry = None
    db.session.commit()

    return jsonify({"success": "Password updated successfully"}), 200

def send_reset_email(user, token):
    reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
    msg = Message("Password Reset Request", sender=os.getenv("MAIL_USERNAME"), recipients=[user.email])
    msg.body = f"Click the following link to reset your password: {reset_url}\nIf you did not request this, please ignore this email."
    mail.send(msg)

# Google OAuth
#google_bp = make_google_blueprint(client_id=os.getenv("GOOGLE_CLIENT_ID"),
                                  #client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                                  #redirect_to="auth_bp.google_login")

#auth_bp.register_blueprint(google_bp, url_prefix="/login")

#@auth_bp.route("/google-login")
#def google_login():
    #if not google.authorized:
        #return jsonify({"error": "Google authorization failed"}), 401

    #resp = google.get("/oauth2/v2/userinfo")
    #user_info = resp.json()
    #email = user_info.get("email")
    #username = user_info.get("name")

    #user = User.query.filter_by(email=email).first()
    #if not user:
        #random_password = secrets.token_urlsafe(16)  
        #hashed_password = generate_password_hash(random_password)
        #user = User(username=username, email=email, password=hashed_password, is_verified=True)  
    #else:
        #if not user.password:  
            #user.username = username

    #db.session.add(user)
    #db.session.commit()

    #access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=12))
    #return jsonify({"access_token": access_token, "message": "Google authentication successful"}), 200

# Helper function to send email verification
#def send_verification_email(email, token):
    #verification_url = url_for('auth_bp.verify_email', token=token, _external=True)
    #msg = Message("Verify Your Email", sender=os.getenv("MAIL_USERNAME"), recipients=[email])
    #msg.body = f"Click the following link to verify your email: {verification_url}\nIf you did not sign up, please ignore this email."
    #mail.send(msg)

    #return jsonify({"message": "Verification email sent"}), 200


    
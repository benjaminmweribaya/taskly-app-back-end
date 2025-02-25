from flask import make_response, request, Blueprint
from models import db, User, TokenBlocklist
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

auth_bp= Blueprint("auth_bp", __name__)

#signup
@auth_bp.route("/signup",methods=["POST"])
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




from flask import Flask
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import timedelta
from models import db,TokenBlocklist
import os

app = Flask(__name__)

#migration initialization
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taskly.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL


# Configure JWT before initializing it
app.config["JWT_SECRET_KEY"] = "uihrfxnkcnpeu"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)


db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*")
jwt = JWTManager(app)


#configure jwt 
jwt.init_app(app)

from views import *

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(tasklist_bp)
app.register_blueprint(task_bp)
app.register_blueprint(taskassignment_bp)
app.register_blueprint(comments_bp)
app.register_blueprint(notifications_bp)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()

    return token is not None

@app.route("/")
def index():
    return jsonify({"message":"Welcome to taskly app backend server"})

if __name__ == "__main__":
    socketio.run(app, debug=True)
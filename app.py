from flask import Flask
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import timedelta
from models import db,TokenBlocklist
from flask_cors import CORS
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": os.getenv("CORS_ALLOWED_ORIGINS", "*")}})

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taskly.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-default-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)


db.init_app(app)
migrate = Migrate(app, db)
#socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
jwt = JWTManager(app)

from views import *

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(tasklist_bp)
app.register_blueprint(task_bp)
app.register_blueprint(task_assignment_bp)
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
    port = int(os.getenv("PORT", 5000)) 
    #socketio.run(app, host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") != "production", allow_unsafe_werkzeug=True, use_reloader=False)
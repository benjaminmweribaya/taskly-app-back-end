from flask import Flask
from flask_migrate import Migrate
from models import db
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_jwt_extended import JWTManager
from datetime import timedelta
from models import db,TokenBlocklist

app = Flask(__name__)
#migration initialization
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskly.db"


migrate = Migrate(app, db)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
jwt = JWTManager(app)


# Import and register blueprints
from views.auth import auth_bp
from views.tasklist import tasklist_bp
from views.comments import comments_bp
from views.notifications import notifications_bp

app.register_blueprint(auth_bp)
app.register_blueprint(tasklist_bp)
app.register_blueprint(comments_bp)
app.register_blueprint(notifications_bp)

if __name__ == "__main__":
    socketio.run(app, debug=True)

#configure jwt 
jwt = JWTManager(app)
jwt.init_app(app)

app.config["JWT_SECRET_KEY"] = "uihrfxnkcnpeu"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

from views import *

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(tasklist_bp)
app.register_blueprint()
app.register_blueprint(comments_bp)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()

    return token is not None

@app.route("/")
def index():
    return jsonify({"msg":"Welcome to taskly app backend server"})

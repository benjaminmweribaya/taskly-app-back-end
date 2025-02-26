from flask import Flask
from flask_migrate import Migrate
from models import db
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

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
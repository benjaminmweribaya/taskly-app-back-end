from flask import Flask
from flask_migrate import Migrate
from models import db

app = Flask(__name__)

#migration initialization
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskly.db"

migrate = Migrate(app, db)
db.init_app(app)
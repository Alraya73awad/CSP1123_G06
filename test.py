from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'
# Initialize database
db = SQLAlchemy(app)

class Bot(db.Model):
    __tablename__ = "bots"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    algorithm = db.Column(db.String(50), nullable=False)

    hp = db.Column(db.Integer, default=100)
    atk = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=10)
    speed = db.Column(db.Integer, default=10)
    logic = db.Column(db.Integer, default=10)
    luck = db.Column(db.Integer, default=10)
    energy = db.Column(db.Integer, default=100)

    def __repr__(self):
        return f"<Bot {self.name}>"
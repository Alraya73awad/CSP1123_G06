<<<<<<< HEAD
from extensions import db
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Game stats
    xp = db.Column(db.Integer, default=0)
    tokens = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f"<User {self.username}>"
    

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    attack = db.Column(db.Integer, default=0)
    defense = db.Column(db.Integer, default=0)
    speed = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='bots')
=======
from app import db

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
>>>>>>> main

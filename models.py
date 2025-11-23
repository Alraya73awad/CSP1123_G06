from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Game stats 
    xp = db.Column(db.Integer, default=0)
    tokens = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

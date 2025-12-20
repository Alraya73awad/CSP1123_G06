from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    xp = db.Column(db.Integer, default=0)
    tokens = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    bots = db.relationship("Bot", backref="user", lazy=True)

    def get_id(self):
        return str(self.id)


class Bot(db.Model):
    __tablename__ = "bot"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    attack = db.Column(db.Integer, default=0)
    defense = db.Column(db.Integer, default=0)
    speed = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
from datetime import datetime 

    def __repr__(self):
        return f"<Bot {self.name}>"
    
    def award_battle_rewards(self, user, result):
        xp_gain = {"win": 50, "lose": 20, "draw": 30}
        token_gain = {"win": 10, "lose": 3, "draw": 5}

        old_level = user.level

        user.xp += xp_gain[result]
        user.tokens += token_gain[result]

        while user.xp >= user.level * 100:
            user.xp -= user.level * 100
            user.level += 1

        db.session.commit()

        return user.level > old_level  # True = level-up happened
    def __repr__(self):
        return f"<Bot {self.name}>"

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    bot1_id = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)
    bot2_id = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)

    bot1_name = db.Column(db.String(50), nullable=False)
    bot2_name = db.Column(db.String(50), nullable=False)

    winner = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship(
        "HistoryLog",
        backref="history",
        cascade="all, delete-orphan"
    )

class HistoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    history_id = db.Column(
        db.Integer,
        db.ForeignKey("history.id"),
        nullable=False
    )

    type = db.Column(db.String(20))  # round, attack, status, defeat, etc
    text = db.Column(db.Text)

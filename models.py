from extensions import db
from datetime import datetime 

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
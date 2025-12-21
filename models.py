from extensions import db
from datetime import datetime

class Bot(db.Model):
    __tablename__ = "bots"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    hp = db.Column(db.Integer,default=100)
    energy = db.Column(db.Integer, default= 100)
    proc = db.Column(db.Integer, default= 10)
    defense = db.Column(db.Integer, default= 10)
    clk = db.Column(db.Integer, default= 10)
    luck = db.Column(db.Integer, default= 10)
    logic = db.Column(db.Integer, default= 10)
    algorithm_id = db.Column(db.String(50))

    # Relationship: one bot can have many modules
    modules = db.relationship("Modules", backref="bot", lazy=True)


class Modules(db.Model):
    __tablename__ = "modules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=False)
    power_boost = db.Column(db.Integer, default=0)
    defense_boost = db.Column(db.Integer, default=0)
    speed_boost = db.Column(db.Integer, default=0)

    # Foreign key to Bot
    bot_id = db.Column(db.Integer, db.ForeignKey("bots.id"))


class BattleBot:
    def __init__(self, bot_model: Bot):
        self.name = bot_model.name
        self.id = bot_model.id
        self.hp = bot_model.hp
        self.energy = bot_model.energy
        self.proc = bot_model.proc
        self.defense = bot_model.defense
        self.clk = bot_model.clk
        self.luck = bot_model.luck
        self.algorithm_id = bot_model.algorithm_id

    def is_alive(self):
        return self.hp > 0 and self.energy > 0

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



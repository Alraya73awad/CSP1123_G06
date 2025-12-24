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
    weapon_id = db.Column(db.Integer, db.ForeignKey("weapons.id"))
    weapon = db.relationship("Weapon", backref="bots")

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

class Weapon(db.Model):
    __tablename__ = "weapons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    atk_bonus = db.Column(db.Integer, default=0)
    tier = db.Column(db.Integer, default=1)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=5)

    def effective_atk(self):
        tier_stats = {
            1: {"base": 5, "per_level": 1},
            2: {"base": 8, "per_level": 2},
            3: {"base": 16, "per_level": 5},
            4: {"base": 33, "per_level": 7},
            5: {"base": 55, "per_level": 14},
            6: {"base": 100, "per_level": 20},
        }

        stats = tier_stats[self.tier]

        return stats["base"] + (self.level - 1) * stats["per_level"]

from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = "user"

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
    special_effect = db.Column(db.String(100), nullable=True)
    extra_attacks = db.Column(db.Integer, default=0)
    ability_used = db.Column(db.Boolean, default=False)
    special_damage = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    weapon_id = db.Column(db.Integer, db.ForeignKey("weapons.id"), nullable=True)
    weapon = db.relationship("Weapon", backref="bots")

    def __repr__(self):
        return f"<Bot {self.name}>"

def __repr__(self):
        return f"<Bot {self.name}>"

def award_battle_rewards(self, user, result):
        xp_gain = {"win": 50, "lose": 20, "draw": 30}
        token_gain = {"win": 10, "lose": 3, "draw": 5}

        old_level = user.level

        user.xp += xp_gain.get(result, 0)
        user.tokens += token_gain.get(result, 0)

        while user.xp >= user.level * 100:
            user.xp -= user.level * 100
            user.level += 1

        db.session.commit()
        return user.level > old_level

class History(db.Model):
    __tablename__ = "history"

    id = db.Column(db.Integer, primary_key=True)

    bot1_id = db.Column(db.Integer, db.ForeignKey("bot.id"), nullable=False)
    bot2_id = db.Column(db.Integer, db.ForeignKey("bot.id"), nullable=False)

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
    __tablename__ = "history_log"

    id = db.Column(db.Integer, primary_key=True)

    history_id = db.Column(
        db.Integer,
        db.ForeignKey("history.id"),
        nullable=False
    )

    type = db.Column(db.String(20))
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


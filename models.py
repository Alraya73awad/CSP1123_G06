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

    rating = db.Column(db.Integer, default=600)  # ELO-style rating
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    
    @property
    def win_rate(self):
        total = self.wins + self.losses
        if total == 0:
            return 0
        return (self.wins / total) * 100

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

    @property
    def equipped_weapon(self):
        for ow in self.equipped_weapon_ownership:
            if ow.equipped:
                return ow
        return None

    @property
    def total_proc(self):
        base = self.atk
        ow = self.equipped_weapon
        if ow and ow.weapon:
            return base + ow.weapon.effective_atk()
        return base

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

    seed = db.Column(db.Integer, nullable=False)

    # Bot 1 stats snapshot
    bot1_hp = db.Column(db.Integer)
    bot1_energy = db.Column(db.Integer)
    bot1_proc = db.Column(db.Integer)
    bot1_defense = db.Column(db.Integer)
    bot1_clk = db.Column(db.Integer)
    bot1_luck = db.Column(db.Integer)
    bot1_weapon_atk = db.Column(db.Integer, default=0)
    bot1_weapon_type = db.Column(db.String(20))
    
    # Bot 2 stats snapshot
    bot2_hp = db.Column(db.Integer)
    bot2_energy = db.Column(db.Integer)
    bot2_proc = db.Column(db.Integer)
    bot2_defense = db.Column(db.Integer)
    bot2_clk = db.Column(db.Integer)
    bot2_luck = db.Column(db.Integer)
    bot2_weapon_atk = db.Column(db.Integer, default=0)
    bot2_weapon_type = db.Column(db.String(20))

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

class WeaponOwnership(db.Model):
    __tablename__ = "weapon_ownership"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    weapon_id = db.Column(
        db.Integer,
        db.ForeignKey("weapons.id"),
        nullable=False
    )

    # Which bot this weapon is equipped to (NULL = unequipped)
    bot_id = db.Column(
        db.Integer,
        db.ForeignKey("bot.id"),
        nullable=True
    )

    equipped = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship("User", backref="weapon_inventory")
    weapon = db.relationship("Weapon")
    bot = db.relationship("Bot", backref="equipped_weapon_ownership")

    def effective_atk(self):
        return self.weapon.effective_atk()
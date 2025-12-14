from extention import db

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








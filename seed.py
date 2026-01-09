from app import app
from extensions import db
from models import Bot

def seed_game_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        bots = [
            Bot(name="Vexor", algorithm="VEX-01", hp=50,atk=12, defense=9, speed=10, logic=10, luck=10, energy=100,
                special_effect="Core Meltdown"),         
            Bot(name="Bastion", algorithm="BASL-09", hp=50, atk=10, defense=12, speed=9, logic=10, luck=10, energy=100,
                special_effect="Fortify Matrix"),       
            Bot(name="Equilibrium", algorithm="EQUA-12", hp=50, atk=10, defense=10, speed=10, logic=10, luck=10, energy=100,
                special_effect="System Balance"),       
            Bot(name="Adaptive", algorithm="ADAPT-X", hp=50,atk=9, defense=10, speed=10, logic=10, luck=10, energy=100,
                special_effect="Evolve Protocol"),        
            Bot(name="Rush", algorithm="RUSH-09", hp=50, atk=10, defense=9, speed=12, logic=10, luck=10, energy=100,
                special_effect="Time Dilation"),        
            Bot(name="Chaos", algorithm="CHAOS-RND", hp=50, atk=10, defense=10, speed=10, logic=10, luck=10, energy=100,
                special_effect="Entropy Burst")          
        ]

        db.session.add_all(bots)
        db.session.commit()

        for bot in Bot.query.all():
            print(f"{bot.name} ({bot.algorithm}) -> ATK: {bot.atk}, DEF: {bot.defense}, SPD: {bot.speed}, Effect: {bot.special_effect}")

if __name__ == "__main__":
    seed_game_data()
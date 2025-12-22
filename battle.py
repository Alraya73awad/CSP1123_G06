import random
from app import create_app
from extensions import db
from models import Bot

app = create_app()

class BattleBot:
    def __init__(self, bot_model: Bot):
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

def log_line(log, type, text):
    log.append((type.strip().lower(), text))


def calculate_turn_order(botA, botB, log):
    if botA.clk> botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)  # random order if equal


def calculate_damage(attacker, defender, log):
    # Base damage
    base_proc = attacker.proc - (defender.defense * 0.5)
    if base_proc < 0:
        base_proc = 0

    # Critical hit check
    crit_trigger = random.randint(1, 100) <= attacker.luck
    crit_rate = 1 if crit_trigger else 0

    # Dodge check
    dodge_chance = 0
    if defender.clk > attacker.clk:
        dodge_chance = (attacker.clk - defender.clk) * (attacker.luck / 100)
        dodge_roll = random.random()
        if dodge_roll < dodge_chance:
            log_line(log, "dodge",f"{defender.name} dodged the attack!")
            return 0

    if crit_trigger:
        print(f"💥 Critical Hit! {attacker.algorithm_id} lands a devastating strike!")

    # Final damage
    final_damage = base_proc + (base_proc * crit_rate)
    return final_damage


def battle_round(botA, botB, log):
    turn_order = calculate_turn_order(botA, botB, log)

    for attacker in turn_order:
        defender = botA if attacker == botB else botB

        if not defender.is_alive():
            break

        attacker.energy -= 10
        if attacker.energy < 0:
            attacker.energy = 0

        if not attacker.is_alive():
            print(f"{attacker.algorithm_id} has been defeated (out of energy)!")
            return defender.algorithm_id

        damage = calculate_damage(attacker, defender, log)
        defender.hp -= damage

        log_line(log, "attack",f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")
        if defender.hp < 0:
            defender.hp = 0
        log_line(log, "status",f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        if not defender.is_alive():
            log_line(log, "defeat",f"{defender.name} has been defeated!")
            return attacker.name

def full_battle(botA, botB):
    log = []
    round_num = 1
    while botA.is_alive() and botB.is_alive():
        log_line(log, "round",f"\n (Round {round_num})")
        winner = battle_round(botA, botB, log)
        if winner:
            log_line(log, "battleover",f"\nBattle Over! Winner: {winner}")
            print(log)
            return winner, log 
            break
        round_num += 1


# Test battle using DB bots
if __name__ == "__main__":
    with app.app_context():
        # Fetch two bots from DB by name or ID
        bot1_model = Bot.query.filter_by(name="VEX").first()
        bot2_model = Bot.query.filter_by(name="BASL").first()

        if not bot1_model or not bot2_model:
            print("Bots not found in database. Seed them first!")
        else:
            bot1 = BattleBot(bot1_model)
            bot2 = BattleBot(bot2_model)

            full_battle(bot1, bot2)

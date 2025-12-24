import random

class BattleBot:
    def __init__(self, name, hp, energy, proc, defense, speed=0, clk=0 , luck=0, weapon_atk = 0, weapon_type = None):
        self.name = name
        self.hp = hp
        self.energy = energy
        self.proc = proc       # Attack power
        self.defense = defense
        self.speed = speed
        self.clk = clk         # Reflex/clock stat
        self.luck = luck       # % chance for crit/dodge
        self.weapon_atk = weapon_atk
        self.weapon_type = weapon_type

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
    base_proc = get_effective_proc(attacker) - (defender.defense * 0.7)
    if base_proc < 0:
        base_proc = 0
    
    # Ranged damage
    if attacker.weapon_type == "ranged":
        variance = random.uniform(0.85, 1.15)
        base_proc *= variance

    # Critical hit check
    crit_trigger = random.randint(1, 100) <= attacker.luck
    crit_rate = 1 if crit_trigger else 0
    if crit_trigger:
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} lands a devastating strike!")

    # Dodge check
    dodge_chance = 0
    if defender.clk > attacker.clk:
        dodge_chance = (defender.clk - attacker.clk) * (defender.luck / 100)
        if random.random() < dodge_chance:
            log_line(log, "dodge",f"{defender.name} dodged the attack!")
            return 0

    # Final damage
    final_damage = base_proc + (base_proc * crit_rate)
    return final_damage

# adding weapon dmg to proc
def get_effective_proc(bot):
    base = bot.proc
    weapon = bot.weapon_atk if bot.weapon_atk else 0
    return base + weapon

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
            log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
            return defender.name

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

#test battle
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10, clk=14, luck=15)
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12, clk=14, luck=10)
    winner = full_battle(bot1, bot2)
  

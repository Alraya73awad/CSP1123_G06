import random

class BattleBot:
    def __init__(self=10, name=10, energy=10, proc=10, defense=10, speed=10, clk=10 , luck=10, hp=100):
        self.name = name
        self.hp = hp
        self.energy = energy
        self.proc = proc       # Attack power
        self.defense = defense
        self.speed = speed
        self.clk = clk         # Reflex/clock stat
        self.luck = luck       # % chance for crit/dodge

    def is_alive(self):
        return self.hp > 0 and self.energy > 0


def calculate_turn_order(botA, botB, log):
    if botA.clk> botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)  # random order if equal


def calculate_damage(attacker, defender, log):
    # Base damage
    base_proc = attacker.proc - (defender.defense * 0.7)
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
            log.append(f"{defender.name} dodged the attack!")
            return 0

    # Final damage
    final_damage = base_proc + (base_proc * crit_rate)
    return final_damage


def battle_round(botA, botB, log):
    turn_order = calculate_turn_order(botA, botB, log)

    for attacker in turn_order:
        defender = botA if attacker == botB else botB

        if not defender.is_alive():
            break

        damage = calculate_damage(attacker, defender, log)
        defender.hp -= damage

        log.append(f"{attacker.name} attacks {defender.name} for {damage} damage!")
        if defender.hp < 0:
            defender.hp = 0
        log.append(f"{defender.name} HP: {defender.hp}, Energy: {defender.energy}")

        if not defender.is_alive():
            log.append(f"{defender.name} has been defeated!")
            return attacker.name

def full_battle(botA, botB):
    log = []
    round_num = 1
    while botA.is_alive() and botB.is_alive():
        log.append(f"\n (Round {round_num})")
        winner = battle_round(botA, botB, log)
        if winner:
            log.append(f"\nBattle Over! Winner: {winner}")
            print(log)
            return winner, log 
            break
        round_num += 1

#test battle
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10, clk=14, luck=15)
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12, clk=14, luck=10)
    winner = full_battle(bot1, bot2)
  

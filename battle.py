import random
from constants import ALGORITHM_XP_MULTIPLIER

class BattleBot:
    def __init__(self, name, hp, energy, proc, defense, speed=0, clk=0 , luck=0, weapon_atk=0, weapon_type=None):
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

        # Performance tracking for stat points
        self.damage_dealt = 0
        self.critical_hits = 0
        self.dodges = 0
        self.rounds_alive = 0

    def is_alive(self):
        return self.hp > 0 and self.energy > 0

def log_line(log, log_type, text):
    log.append((log_type.strip().lower(), text))

def calculate_turn_order(botA, botB, log):
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)

def get_effective_proc(bot):
    return bot.proc + (bot.weapon_atk or 0)

def calculate_damage(attacker, defender, log):
    base_proc = get_effective_proc(attacker) - (defender.defense * 0.7)
    if base_proc < 0:
        base_proc = 0

    # Ranged variance
    if attacker.weapon_type == "ranged":
        base_proc *= random.uniform(0.85, 1.15)

    # Critical hit check
    is_crit = False
    if random.randint(1, 100) <= attacker.luck:
        is_crit = True
        attacker.critical_hits += 1
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} strikes {defender.name}!")

    # Dodge check
    dodge_chance = 0
    if defender.clk > attacker.clk:
        dodge_chance = (defender.clk - attacker.clk) * (defender.luck / 100)
        if random.random() < dodge_chance:
            defender.dodges += 1
            log_line(log, "dodge", f"{defender.name} dodged the attack!")
            return 0, is_crit

    final_damage = base_proc * (2 if is_crit else 1)
    return final_damage, is_crit

def battle_round(botA, botB, log):
    # Track rounds alive
    botA.rounds_alive += 1
    botB.rounds_alive += 1

    turn_order = calculate_turn_order(botA, botB, log)

    for attacker in turn_order:
        defender = botB if attacker == botA else botA

        if not defender.is_alive():
            continue

        attacker.energy = max(attacker.energy - 10, 0)
        if not attacker.is_alive():
            log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
            return defender.name

        damage, is_crit = calculate_damage(attacker, defender, log)
        attacker.damage_dealt += damage
        defender.hp = max(defender.hp - damage, 0)
        log_line(log, "attack", f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")
        log_line(log, "status", f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        if not defender.is_alive():
            log_line(log, "defeat", f"{defender.name} has been defeated!")
            return attacker.name

def calculate_bot_stat_points(bot, result):
    points = 0
    if result == "win":
        points += 5
    else:
        points += 2

    # Performance bonus
    points += int(bot.damage_dealt // 50)  # 1 point per 50 damage
    points += bot.critical_hits            # 1 point per crit
    points += bot.dodges                   # 1 point per dodge
    points += bot.rounds_alive // 2        # 1 point every 2 rounds survived

    return points

def full_battle(botA, botB):
    log = []
    round_num = 1
    winner_name = None

    while botA.is_alive() and botB.is_alive():
        log_line(log, "round", f"\n(Round {round_num})")
        winner_name = battle_round(botA, botB, log)
        if winner_name:
            log_line(log, "battleover", f"\nBattle Over! Winner: {winner_name}")
            break
        round_num += 1

    # Stat points
    if winner_name == botA.name:
        botA_points = calculate_bot_stat_points(botA, "win")
        botB_points = calculate_bot_stat_points(botB, "lose")
    else:
        botB_points = calculate_bot_stat_points(botB, "win")
        botA_points = calculate_bot_stat_points(botA, "lose")

    return {
        "winner": winner_name,
        "log": log,
        "botA_points": botA_points,
        "botB_points": botB_points
    }

# Example usage
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10, clk=14, luck=15)
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12, clk=14, luck=10)
    result = full_battle(bot1, bot2)

    print(f"Winner: {result['winner']}")
    print(f"XP Gained: {result['xp_gained']}")
    print(f"Bot1 Stat Points Earned: {result['botA_points']}")
    print(f"Bot2 Stat Points Earned: {result['botB_points']}")

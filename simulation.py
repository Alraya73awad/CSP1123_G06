import random
from app import create_app
from extensions import db
from models import Bot

app = create_app()

#Arenas
ARENAS = ["open","close"]

class BattleBot:
    def __init__(self, hp, energy, proc, defense, clk, luck, algorithm_id, weapon_type):
        self.hp = hp
        self.energy = energy
        self.proc = proc
        self.defense = defense
        self.clk = clk
        self.luck = luck
        self.algorithm_id = algorithm_id
        self.weapon_type = weapon_type 

    def is_alive(self):
        return self.hp > 0 and self.energy > 0


def calculate_turn_order(botA, botB, arena):
    # Arena-based weapon priority
    if arena == "open":
        if botA.weapon_type == "ranged" and botB.weapon_type == "melee":
            return [botA, botB]
        if botB.weapon_type == "ranged" and botA.weapon_type == "melee":
            return [botB, botA]

    if arena == "close":
        if botA.weapon_type == "melee" and botB.weapon_type == "ranged":
            return [botA, botB]
        if botB.weapon_type == "melee" and botA.weapon_type == "ranged":
            return [botB, botA]
    
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)  # random order if equal


def calculate_damage(attacker, defender):
    # Base damage
    base_proc = attacker.proc - (defender.defense * 0.5)
    if base_proc < 0:
        base_proc = 0

    # Ranged damage
    if attacker.weapon_type == "ranged":
        variance = random.uniform(0.85, 1.15)
        base_proc *= variance

    # Critical hit check
    crit_trigger = random.randint(1, 100) <= attacker.luck
    crit_rate = 1 if crit_trigger else 0

    # Dodge check
    dodge_chance = 0
    if defender.clk > attacker.clk:
        dodge_chance = (defender.clk - attacker.clk) * (defender.luck / 100)
        if random.random() < dodge_chance:
            #print(f"{defender.algorithm_id} dodged the attack!")
            return 0

    #if crit_trigger:
        #print(f"💥 Critical Hit! {attacker.algorithm_id} lands a devastating strike!")

    # Final damage
    final_damage = base_proc + (base_proc * crit_rate)
    return final_damage


def battle_round(botA, botB, arena):
    turn_order = calculate_turn_order(botA, botB, arena)

    for attacker in turn_order:
        defender = botA if attacker == botB else botB

        if not defender.is_alive():
            break

        attacker.energy -= 10
        if attacker.energy < 0:
            attacker.energy = 0

        if not attacker.is_alive():
            #print(f"{attacker.algorithm_id} has been defeated (out of energy)!")
            return defender.algorithm_id

        damage = calculate_damage(attacker, defender)
        defender.hp -= damage

        #print(f"{attacker.algorithm_id} attacks {defender.algorithm_id} for {damage} damage!")
        #print(f"{attacker.algorithm_id} Energy: {attacker.energy}")
        if defender.hp < 0:
            defender.hp = 0
        #print(f"{defender.algorithm_id} HP: {round(defender.hp, 0)}, Energy: {defender.energy}")

        if not defender.is_alive():
            #print(f"{defender.algorithm_id} has been defeated!")
            return attacker.algorithm_id


def full_battle(botA, botB):
    round_num = 1
    arena = random.choice(ARENAS)
    while botA.is_alive() and botB.is_alive():
        #print(f"\n (Round {round_num})")
        winner = battle_round(botA, botB, arena)
        if winner:
            #print(f"\nBattle Over! Winner: {winner}")
            return winner, round_num
            break
        round_num += 1


# Test battle using DB bots
if __name__ == "__main__":
    from simulation import BattleBot, full_battle

    NUM_MATCHES = 10000

    baseline_wins = 0
    weapon_wins = 0
    total_rounds = 0

    for _ in range(NUM_MATCHES):

        # Baseline bot (no weapon)
        baseline = BattleBot(
            hp=630,
            energy=630,
            proc=63,
            defense=63,
            clk=10,
            luck=10,
            algorithm_id="Baseline",
            weapon_type = None
        )

        # Weapon bot
        weapon_bot = BattleBot(
            hp=630,
            energy=630,
            proc=65,   #weapon atk  
            defense=63,
            clk=10,
            luck=10,
            algorithm_id="Weapon",
            weapon_type = "ranged"
        )

        winner, rounds = full_battle(baseline, weapon_bot)

        total_rounds += rounds

        if winner == "Baseline":
            baseline_wins += 1
        else:
            weapon_wins += 1

    # Results
    print("=== Simulation Results ===")
    print(f"Matches run: {NUM_MATCHES}")
    print(f"Baseline win rate: {baseline_wins / NUM_MATCHES:.2%}")
    print(f"Weapon win rate: {weapon_wins / NUM_MATCHES:.2%}")
    print(f"Average rounds per match: {total_rounds / NUM_MATCHES:.2f}")

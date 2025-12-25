import random


class BattleBot:
    def __init__(
        self,
        name,
        energy=10,
        proc=10,
        defense=10,
        speed=10,
        clk=10,
        luck=10,
        hp=100
    ):
        self.name = name
        self.hp = hp
        self.energy = energy
        self.proc = proc
        self.defense = defense
        self.speed = speed
        self.clk = clk
        self.luck = luck

    def is_alive(self):
        return self.hp > 0 and self.energy > 0


# ---------------- LOGGING ----------------
def log_line(log, type, text):
    log.append((type.strip().lower(), text))


#turn order
def calculate_turn_order(botA, botB):
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)


# damage
def calculate_damage(attacker, defender, log):
    base_damage = attacker.proc - (defender.defense * 0.7)
    base_damage = max(0, int(base_damage))

    # Critical hit
    if random.randint(1, 100) <= attacker.luck:
        base_damage = int(base_damage * 1.5)
        log_line(log, "crit", f"{attacker.name} lands a critical hit!")

    defender.hp -= base_damage
    attacker.energy -= 1

    log_line(
        log,
        "attack",
        f"{attacker.name} deals {base_damage} damage to {defender.name}"
    )

    return base_damage


# full battke
def full_battle(botA, botB):
    log = []

    log_line(log, "start", f"Battle starts: {botA.name} vs {botB.name}")

    while botA.is_alive() and botB.is_alive():
        turn_order = calculate_turn_order(botA, botB)

        for attacker in turn_order:
            defender = botB if attacker == botA else botA

            if not attacker.is_alive() or not defender.is_alive():
                break

            calculate_damage(attacker, defender, log)

    # Determine winner
    if botA.is_alive():
        winner = botA
        loser = botB
    else:
        winner = botB
        loser = botA

    log_line(log, "end", f"{winner.name} defeats {loser.name}")

    return {
        "winner": winner.name,
        "loser": loser.name,
        "log": log
    }

    if not defender.is_alive():
        #break

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
  

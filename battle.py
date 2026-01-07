import random

class BattleBot:
    def __init__(self, name, hp, energy, proc, defense, speed=0, clk=0 , luck=0, weapon_atk = 0, weapon_type = None , special_effect=None):
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
        self.special_effect = special_effect
        self.extra_attacks = 0
        self.ability_used = False


    def is_alive(self):
        return self.hp > 0 and self.energy > 0

def log_line(log, type, text):
    log.append((type.strip().lower(), text))


def calculate_turn_order(botA, botB, log, rng):
    if botA.clk> botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return rng.sample([botA, botB], 2)  # random order if equal

def use_ability(attacker, defender, log, round_num=1, rng=None):
    if attacker.ability_used:
        return  # already triggered once

    if not (attacker.hp < 40 or round_num == 6):
        return  # condition not met yet

    attacker.ability_used = True  # mark as used

    if attacker.special_effect == "Core Meltdown":
        attacker.proc = int(attacker.proc * 1.15)
        attacker.defense = int(attacker.defense * 0.9)
        log_line(log, "special", f"🔥 {attacker.name} activates Core Meltdown, sacrificing defense for raw power!")

    elif attacker.special_effect == "Fortify Matrix":
        attacker.defense = int(attacker.defense * 1.2)
        attacker.speed = int(attacker.speed * 0.9)
        log_line(log, "special", f"🛡️ {attacker.name} engages Fortify Matrix, becoming a fortress but slowing down!")

    elif attacker.special_effect == "System Balance":
        attacker.hp += int(attacker.hp * 0.1)
        attacker.energy += int(attacker.energy * 0.1)
        log_line(log, "special", f"⚖️ {attacker.name} restores equilibrium, regaining vitality and energy!")
        
    elif attacker.special_effect == "Evolve Protocol":
        stats = ["hp", "atk", "defense", "speed", "logic", "luck", "energy"]

        chosen_stats = rng.sample(stats, 2)

        
        for stat in chosen_stats:
            current_value = getattr(attacker, stat)      
            boosted_val = int(current_value * 1.10)          
            setattr(attacker, stat, boosted_val)           

        log_line(log, "special", f"🔄 {attacker.name} adapts mid-battle with Evolve Protocol, boosting {chosen_stats[0].upper()} and {chosen_stats[1].upper()} by 10%!")

    elif attacker.special_effect == "Time Dilation":
        attacker.extra_attacks = 1
        log_line(log, "special", f"⏳ {attacker.name} bends time with Time Dilation, preparing to strike twice!")

    elif attacker.special_effect == "Evolve Protocol":
        stats = ["hp", "atk", "defense", "speed", "logic", "luck", "energy"]
        chosen_stats = rng.sample(stats, 2)
        for stat in chosen_stats:
            current_val = getattr(attacker, stat)
            boosted_val = int(current_val * 1.10)
            setattr(attacker, stat, boosted_val)
        log_line(log, "special",
                 f"🔄 {attacker.name} adapts mid-battle with Evolve Protocol, boosting {chosen_stats[0].upper()} and {chosen_stats[1].upper()} by 10%!")


def calculate_damage(attacker, defender, log, rng):
    # Base damage
    base_proc = get_effective_proc(attacker) - (defender.defense * 0.7)
    if base_proc < 0:
        base_proc = 0
    
    # Ranged damage
    if attacker.weapon_type == "ranged":
        variance = rng.uniform(0.85, 1.15)
        base_proc *= variance

    # Critical hit check
    crit_trigger = rng.randint(1, 100) <= attacker.luck
    crit_rate = 1 if crit_trigger else 0
    if crit_trigger:
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} lands a devastating strike!")

    # Dodge check
    dodge_chance = 0
    if defender.clk > attacker.clk:
        dodge_chance = (defender.clk - attacker.clk) * (defender.luck / 100)
        if rng.random() < dodge_chance:
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

def battle_round(botA, botB, log, rng):
    turn_order = calculate_turn_order(botA, botB, log, rng)

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

        use_ability(attacker, defender, log=log, rng=rng)
        damage = calculate_damage(attacker, defender, log, rng)
        defender.hp -= damage

        log_line(log, "attack",f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")
        if defender.hp < 0:
            defender.hp = 0
        log_line(log, "status",f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        
        if attacker.extra_attacks > 0 and defender.is_alive():
            attacker.extra_attacks -= 1
            extra_dmg = calculate_damage(attacker, defender, log, rng)
            defender.hp -= extra_dmg
            log_line(log, "attack", f"{attacker.name} strikes again with Time Dilation for {extra_dmg:.2f} damage!")

        if not defender.is_alive():
            log_line(log, "defeat",f"{defender.name} has been defeated!")
            return attacker.name

def full_battle(botA, botB, seed=None):
    if seed is None:
        seed = random.randint(0, 999999999)
    
    rng = random.Random(seed)
    log = []
    round_num = 1
    while botA.is_alive() and botB.is_alive():
        log_line(log, "round", f" (Round {round_num})\n")
        winner = battle_round(botA, botB, log, rng)
        if winner:
            log_line(log, "battleover", f"\nBattle Over! Winner: {winner}")
            print(log)
            return winner, log, seed
        round_num += 1

#test battle
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10, clk=14, luck=10, special_effect="Time Dilation")
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12, clk=14, luck=10, special_effect="Evolve Protocol")
    winner = full_battle(bot1, bot2)
  

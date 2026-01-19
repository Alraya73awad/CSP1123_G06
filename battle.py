import random


class BattleBot:
    def __init__(self, name, hp, energy, proc, defense, speed=0, clk=0, luck=0, weapon=None,
                 weapon_atk=0, weapon_type=None, special_effect=None):
        self.name = name
        self.hp = hp
        self.energy = energy
        self.proc = proc       # Attack power
        self.defense = defense
        self.speed = speed
        self.clk = clk         # Reflex/clock stat
        self.luck = luck       # % chance for crit/dodge
        self.weapon = weapon
        self.weapon_atk = weapon_atk
        self.weapon_type = weapon_type  # "ranged" or "melee"
        self.special_effect = special_effect
        self.extra_attacks = 0
        self.ability_used = False

    def is_alive(self):
        return self.hp > 0 and self.energy > 0

ARENA_FLAVOR = {
    "ironclash": "⚔️ Welcome to the Ironclash Colosseum — a savage pit where melee warriors gain the upper hand, while ranged bots struggle to keep their distance.",
    "skyline": "🌌 Enter the Skyline Expanse — a vast battlefield of open skies where ranged fighters dominate with precision, leaving melee bots exposed.",
    "neutral": "🌀 The Neutral Arena stands silent — no terrain favors, no hidden edges, only raw willpower decides the victor.",
    "frozen": "❄️ The Frozen Wastes stretch bleak and icy — footing is treacherous, winds howl, and fortress AIs endure while both melee and ranged fighters struggle to land their blows."

}


ARENA_EFFECTS = {
    "ironclash": {
        "favored": "melee",
        "damage_bonus": 1.10,
        "whiff_melee": 0.05,
        "whiff_ranged": 0.15,
        "spd_mod": 1.0,
        "def_mod": 1.0
    },
    "skyline": {
        "favored": "ranged",
        "damage_bonus": 1.10,
        "whiff_melee": 0.15,
        "whiff_ranged": 0.05,
        "spd_mod": 1.0,
        "def_mod": 1.0
    },
    "neutral": {
        "favored": None,
        "damage_bonus": 1.0,
        "whiff_melee": 0.1,
        "whiff_ranged": 0.1,
        "spd_mod": 1.0,
        "def_mod": 1.0
    },
    "frozen": {
        "favored": None,
        "damage_bonus": 1.0,
        "whiff_melee": 0.07,   # slippery footing
        "whiff_ranged": 0.07,  # cold winds
        "spd_mod": 0.90,       # –10% SPD
        "def_mod": 1.10        # +10% DEF
    }
}

def log_line(log, type, text):
    log.append((type.strip().lower(), text))


def arena_name(arena):
    if arena is None:
        return "Neutral"
    return str(arena).title()


def calculate_turn_order(botA, botB):
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return random.sample([botA, botB], 2)  # random order if equal

def apply_arena_modifiers(bot, arena):
    effects = ARENA_EFFECTS.get(arena, ARENA_EFFECTS["neutral"])
    bot.clk = int(bot.clk * effects["spd_mod"])
    bot.defense = int(bot.defense * effects["def_mod"])

def get_effective_proc(bot):
    return bot.proc + (bot.weapon_atk if bot.weapon_atk else 0)
    
    
def use_ability(attacker, defender, log, round_num=1):
    if attacker.ability_used:
        return
    if not (attacker.hp < 40 or round_num == 6):
        return

    attacker.ability_used = True

    if attacker.special_effect == "Core Meltdown":
        attacker.proc = int(attacker.proc * 1.15)
        attacker.defense = int(attacker.defense * 0.9)
        log_line(log, "special",
                 f"🔥 {attacker.name} activates Core Meltdown, sacrificing defense for raw power!")

    elif attacker.special_effect == "Fortify Matrix":
        attacker.defense = int(attacker.defense * 1.2)
        attacker.speed = int(attacker.speed * 0.9)
        log_line(log, "special",
                 f"🛡️ {attacker.name} engages Fortify Matrix, becoming a fortress but slowing down!")

    elif attacker.special_effect == "System Balance":
        attacker.hp += int(attacker.hp * 0.1)
        attacker.energy += int(attacker.energy * 0.1)
        log_line(log, "special",
                 f"⚖️ {attacker.name} restores equilibrium, regaining vitality and energy!")

    elif attacker.special_effect == "Evolve Protocol":
        stats = ["hp", "proc", "defense", "speed", "luck", "energy"]
        chosen_stats = random.sample(stats, 2)
        for stat in chosen_stats:
            current_value = getattr(attacker, stat)
            boosted_val = int(current_value * 1.10)
            setattr(attacker, stat, boosted_val)
        log_line(log, "special",
                 f"🔄 {attacker.name} adapts mid-battle with Evolve Protocol, boosting "
                 f"{chosen_stats[0].upper()} and {chosen_stats[1].upper()} by 10%!")

    elif attacker.special_effect == "Time Dilation":
        attacker.extra_attacks = 1
        log_line(log, "special",
                 f"⏳ {attacker.name} bends time with Time Dilation, preparing to strike twice!")


def calculate_damage(attacker, defender, log, arena=None):
    base_proc = get_effective_proc(attacker) - (defender.defense * 0.7)
    base_proc = max(base_proc, 0)

    # Arena whiff chance
    whiff_chance = 0.1
    if arena == "ranged":
        whiff_chance = 0.05 if attacker.weapon_type == "ranged" else 0.1
    elif arena == "melee":
        whiff_chance = 0.05 if attacker.weapon_type == "melee" else 0.1

    if random.random() < whiff_chance:
        log_line(log, "whiff", f"💨 {attacker.name} misses in the {arena_name(arena)} Arena!")
        return 0

    # Ranged variance
    if attacker.weapon_type == "ranged":
        variance = random.uniform(0.85, 1.15)
        base_proc *= variance

    # Critical hit
    if random.randint(1, 100) <= attacker.luck:
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} lands a devastating strike!")
        base_proc *= 2

    # Dodge
    if defender.clk > attacker.clk:
        dodge_chance = (defender.clk - attacker.clk) * (defender.luck / 100)
        if random.random() < dodge_chance:
            log_line(log, "dodge", f"🌀 {defender.name} dodged the attack!")
            return 0

    

    apply_arena_modifiers(attacker, arena)
    apply_arena_modifiers(defender, arena)

    return base_proc


def battle_round(botA, botB, log, arena="neutral", round_num=1):
    turn_order = calculate_turn_order(botA, botB)

    for attacker in turn_order:
        defender = botA if attacker == botB else botB

        if not defender.is_alive():
            break

        attacker.energy -= 10
        attacker.energy = max(attacker.energy, 0)

        if not attacker.is_alive():
            log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
            return defender.name

        use_ability(attacker, defender, log, round_num)

        damage = calculate_damage(attacker, defender, log, arena=arena)
        defender.hp -= damage
        if defender.hp < 0:
            defender.hp = 0

        if attacker.weapon:
            log_line(log, "attack", f"{attacker.name} strikes with {attacker.weapon} for {damage:.2f} damage!")
        else:
            log_line(log, "attack", f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")

        log_line(log, "status", f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        if attacker.extra_attacks > 0 and defender.is_alive():
            attacker.extra_attacks -= 1
            extra_dmg = calculate_damage(attacker, defender, log, arena=arena)
            defender.hp -= extra_dmg
            if defender.hp < 0:
                defender.hp = 0
            log_line(log, "attack", f"{attacker.name} strikes again with Time Dilation for {extra_dmg:.2f} damage!")

        if not defender.is_alive():
            log_line(log, "defeat", f"{defender.name} has been defeated!")
            return attacker.name


def full_battle(botA, botB, arena="neutral"):
    log = []
    round_num = 1
    intro_line = ARENA_FLAVOR.get(arena, f"🏟️ Battle begins in the {arena_name(arena)} Arena!")
    log_line(log, "arena", intro_line)

    while botA.is_alive() and botB.is_alive():
        log_line(log, "round", f"(Round {round_num})")
        winner = battle_round(botA, botB, log, arena=arena, round_num=round_num)
        if winner:
            log_line(log, "battleover", f"Battle Over! Winner: {winner}")
            for entry in log:
                print(f"[{entry[0]}] {entry[1]}")
            return winner, log
        round_num += 1


# Test battle
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10,
                     clk=14, luck=10, weapon_type="melee", special_effect="Time Dilation", weapon = "code cutter")
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12,
                     clk=14, luck=10, weapon_type="ranged", special_effect="Evolve Protocol")

    #Randomly pick Ironclash, Skyline, or Neutral
    chosen_arena = random.choice(["ironclash", "skyline", "neutral", "frozen"])
    winner, log = full_battle(bot1, bot2, arena=chosen_arena)
import random
from constants import ALGORITHM_XP_MULTIPLIER


class BattleBot:
    def __init__(self, name, hp, energy, proc, defense, speed=0, clk=0, luck=0,
                 weapon_atk=0, weapon_type=None, special_effect=None):
        self.name = name
        self.hp = hp
        self.energy = energy
        self.proc = proc
        self.defense = defense
        self.speed = speed
        self.clk = clk
        self.luck = luck
        self.weapon_atk = weapon_atk
        self.weapon_type = weapon_type
        self.special_effect = special_effect

        self.damage_dealt = 0
        self.critical_hits = 0
        self.dodges = 0
        self.rounds_alive = 0

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
        "whiff_melee": 0.07,
        "whiff_ranged": 0.07,
        "spd_mod": 0.90,
        "def_mod": 1.10
    }
}


def log_line(log, type, text):
    log.append((type.strip().lower(), text))


def calculate_turn_order(botA, botB, rng):
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return rng.sample([botA, botB], 2)


def arena_name(arena):
    if arena is None:
        return "Neutral"
    return str(arena).title()


def apply_arena_modifiers(bot, arena):
    effects = ARENA_EFFECTS.get(arena, ARENA_EFFECTS["neutral"])
    bot.clk = int(bot.clk * effects["spd_mod"])
    bot.defense = int(bot.defense * effects["def_mod"])


def get_effective_proc(bot):
    return bot.proc + (bot.weapon_atk if bot.weapon_atk else 0)


def calculate_bot_stat_points(bot, result):
    points = 0
    if result == "win":
        points += 5
    else:
        points += 2

    points += int(bot.damage_dealt // 50)
    points += bot.critical_hits
    points += bot.dodges
    points += bot.rounds_alive // 2

    return points


def use_ability(attacker, defender, log, round_num=1, rng=None):
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
        chosen_stats = rng.sample(stats, 2)
        for stat in chosen_stats:
            setattr(attacker, stat, int(getattr(attacker, stat) * 1.10))
        log_line(log, "special",
                 f"🔄 {attacker.name} adapts mid-battle with Evolve Protocol!")

    elif attacker.special_effect == "Time Dilation":
        attacker.extra_attacks = 1
        log_line(log, "special",
                 f"⏳ {attacker.name} bends time with Time Dilation!")

def calculate_damage(attacker, defender, log, rng, arena="neutral"):
    effects = ARENA_EFFECTS.get(arena, ARENA_EFFECTS["neutral"])


    if attacker.weapon_type == "ranged":
        whiff_chance = effects["whiff_ranged"]
    else:
        whiff_chance = effects["whiff_melee"]

    if rng.random() < whiff_chance:
        log_line(log, "whiff", f"💨 {attacker.name} misses in the {arena_name(arena)} Arena!")
        return 0.0

    # Base damage = effective proc minus defense reduction
    base_proc = get_effective_proc(attacker) - (defender.defense * 0.7)
    base_proc = max(base_proc, 0.0)

    # Arena damage bonus ONLY if attacker is favored type
    if effects["favored"] is not None and attacker.weapon_type == effects["favored"]:
        base_proc *= effects["damage_bonus"]

    # Ranged variance 
    if attacker.weapon_type == "ranged":
        base_proc *= rng.uniform(0.85, 1.15)

    # Critical hit check
    is_crit = rng.randint(1, 100) <= int(attacker.luck or 0)
    if is_crit:
        attacker.critical_hits += 1
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} lands a devastating strike!")
        base_proc *= 2.0

    # Dodge check 
    if defender.clk > attacker.clk:
        clk_gap = defender.clk - attacker.clk
        dodge_chance = (clk_gap * (defender.luck / 100.0)) / 100.0  # keep it small
        dodge_chance = max(0.0, min(dodge_chance, 0.35))            # cap at 35%
        if rng.random() < dodge_chance:
            defender.dodges += 1
            log_line(log, "dodge", f"🌀 {defender.name} dodged the attack!")
            return 0.0

    # Track damage dealt
    attacker.damage_dealt += float(base_proc)
    return float(base_proc)


def battle_round(botA, botB, log, rng, arena="neutral", round_num=1):
    # Track rounds alive
    botA.rounds_alive += 1
    botB.rounds_alive += 1

    turn_order = calculate_turn_order(botA, botB, rng)

    for attacker in turn_order:
        defender = botB if attacker == botA else botA

        if not attacker.is_alive() or not defender.is_alive():
            continue

        attacker.energy -= 10
        attacker.energy = max(attacker.energy, 0)

        if not attacker.is_alive():
            log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
            return defender.name

        use_ability(attacker, defender, log=log, round_num=round_num, rng=rng)

        damage = calculate_damage(attacker, defender, log, rng, arena=arena)
        defender.hp -= damage
        if defender.hp < 0:
            defender.hp = 0

        log_line(log, "attack", f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")
        log_line(log, "status", f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        if attacker.extra_attacks > 0 and defender.is_alive():
            attacker.extra_attacks -= 1
            extra_dmg = calculate_damage(attacker, defender, log, rng, arena=arena)
            defender.hp -= extra_dmg
            if defender.hp < 0:
                defender.hp = 0
            log_line(log, "attack", f"{attacker.name} strikes again with Time Dilation for {extra_dmg:.2f} damage!")

        if not defender.is_alive():
            log_line(log, "defeat", f"{defender.name} has been defeated!")
            return attacker.name

    return None


def full_battle(botA, botB, seed=None, arena="neutral"):
    if seed is None:
        seed = random.randint(0, 999999999)

    rng = random.Random(seed)
    log = []
    round_num = 1
    winner = None

    # Apply arena mods ONCE (not every hit)
    apply_arena_modifiers(botA, arena)
    apply_arena_modifiers(botB, arena)

    intro_line = ARENA_FLAVOR.get(
        arena,
        f"🏟️ Battle begins in the {arena_name(arena)} Arena!"
    )
    log_line(log, "arena", intro_line)

    while botA.is_alive() and botB.is_alive():
        log_line(log, "round", f"(Round {round_num})")

        winner = battle_round(
            botA,
            botB,
            log,
            rng=rng,
            arena=arena,
            round_num=round_num
        )

        if winner:
            log_line(log, "battleover", f"Battle Over! Winner: {winner}")
            break

        round_num += 1

    if winner == botA.name:
        botA_points = calculate_bot_stat_points(botA, "win")
        botB_points = calculate_bot_stat_points(botB, "lose")
    else:
        botB_points = calculate_bot_stat_points(botB, "win")
        botA_points = calculate_bot_stat_points(botA, "lose")

    return {
        "winner": winner,
        "log": log,
        "seed": seed,
        "botA_points": botA_points,
        "botB_points": botB_points
    }


# Test battle
if __name__ == "__main__":
    bot1 = BattleBot("Alpha", hp=100, energy=50, proc=30, defense=10,
                     clk=14, luck=10, weapon_type="melee", special_effect="Time Dilation")
    bot2 = BattleBot("Beta", hp=120, energy=50, proc=25, defense=12,
                     clk=14, luck=10, weapon_type="ranged", special_effect="Evolve Protocol")

    # 🎲 Randomly pick Ironclash, Skyline, Neutral, or Frozen
    chosen_arena = random.choice(["ironclash", "skyline", "neutral", "frozen"])
    result = full_battle(bot1, bot2, arena=chosen_arena)
    print("Winner:", result["winner"])
    for t, msg in result["log"]:
        print(f"[{t}] {msg}")


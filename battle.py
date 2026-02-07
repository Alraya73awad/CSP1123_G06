import random
from constants import ALGORITHM_XP_MULTIPLIER

# -----------------------------
# Character Items (hard-coded)
# -----------------------------
CHARACTER_ITEMS = [
    {
        "id": 101,
        "name": "Armor Plating",
        "desc": "+10% DEF",
        "cost": 30,
        "stat": "defense",
        "value": 10
    },
    {
        "id": 102,
        "name": "Overclock Unit",
        "desc": "+10% SPD but costs 5 Energy per turn",
        "cost": 40,
        "stat": "speed",
        "value": 10
    },
    {
        "id": 103,
        "name": "Regen Core",
        "desc": "Regain 5% HP each turn",
        "cost": 40,
        "stat": "hp",
        "value": 5
    },
    {
        "id": 104,
        "name": "Critical Subroutine",
        "desc": "+5% Crit Chance",
        "cost": 40,
        "stat": "crit",
        "value": 5
    },
    {
        "id": 105,
        "name": "Energy Recycler",
        "desc": "Gain 10 Energy each turn",
        "cost": 40,
        "stat": "energy",
        "value": 10
    },
    {
        "id": 106,
        "name": "EMP Shield",
        "desc": "Immune to Energy drain effects",
        "cost": 40,
        "stat": "energy",
        "value": 10
    }
]

# -----------------------------
# BattleBot Class
# -----------------------------
class BattleBot:
    def __init__(
        self,
        name,
        hp,
        energy,
        proc,
        defense,
        speed=0,
        clk=0,
        luck=0,
        logic=0,
        weapon_atk=0,
        weapon_type=None,
        special_effect=None,
        algorithm=None,
        upgrade_armor_plating=False,
        upgrade_overclock_unit=False,
        upgrade_regen_core=False,
        upgrade_critical_subroutine=False,
        upgrade_energy_recycler=False,
        upgrade_emp_shield=False,
    ):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.energy = energy
        self.max_energy = energy
        self.proc = proc     # Attack power
        self.defense = defense
        self.speed = speed
        self.clk = clk       # Reflex/clock stat
        self.luck = luck     # % chance for crit/dodge
        self.logic = logic   # Predict enemy moves: reduces incoming crit, reduces enemy dodge, chance to negate debuffs
        self.weapon_atk = weapon_atk   
        self.weapon_type = weapon_type    # "ranged" or "melee"
        self.special_effect = special_effect
        self.algorithm = algorithm  
        self.upgrade_armor_plating = upgrade_armor_plating
        self.upgrade_overclock_unit = upgrade_overclock_unit
        self.upgrade_regen_core = upgrade_regen_core
        self.upgrade_critical_subroutine = upgrade_critical_subroutine
        self.upgrade_energy_recycler = upgrade_energy_recycler
        self.upgrade_emp_shield = upgrade_emp_shield
        self.crit_bonus_pct = 5.0 if self.upgrade_critical_subroutine else 0.0

        # battle tracking
        self.damage_dealt = 0
        self.critical_hits = 0
        self.dodges = 0
        self.rounds_alive = 0
        self.extra_attacks = 0
        self.ability_used = False

        # item effects
        self.regen = 0
        self.energy_gain = 0
        self.energy_drain = 0
        self.emp_shield = False

        #Internal flags for alogorithm-specific behaviors
        self.adopted_logic_applied = False

    def is_alive(self):
        return self.hp > 0 and self.energy > 0

# -----------------------------
# Arena Flavor & Effects
# -----------------------------
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
        "whiff_melee": 0.07,
        "whiff_ranged": 0.07,
        "spd_mod": 0.90,
        "def_mod": 1.10
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

# -----------------------------
# Utility Functions
# -----------------------------
def log_line(log, type, text):
    log.append((type.strip().lower(), text))

def calculate_turn_order(botA, botB, rng):
    if botA.clk > botB.clk:
        return [botA, botB]
    elif botB.clk > botA.clk:
        return [botB, botA]
    else:
        return rng.sample([botA, botB], 2) # random order if equal

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


def roll_negate_debuff(defender, rng):
    """
    LOGIC gives a chance to negate debuffs applied by the attacker.
    When you add debuff effects (e.g. defense down, slow), call this first;
    if it returns True, the debuff is negated and should not be applied.
    Negate chance = defender.logic / (100 + defender.logic).
    """
    logic = float(defender.logic or 0)
    if logic <= 0:
        return False
    negate_chance = logic / (100.0 + logic)
    return rng.random() < negate_chance


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

# -----------------------------
# Item Application
# -----------------------------
def apply_items(bot, items):
    for item in items:
        if item["id"] == 101:  # Armor Plating
            bot.defense = int(bot.defense * 1.10)
        elif item["id"] == 102:  # Overclock Unit
            bot.speed = int(bot.speed * 1.10)
            bot.energy_drain += 5
        elif item["id"] == 103:  # Regen Core
            bot.regen += int(bot.hp * (item["value"]/100))  # 5% regen
        elif item["id"] == 104:  # Critical Subroutine
            bot.luck += item["value"]  # +5% crit chance
        elif item["id"] == 105:  # Energy Recycler
            bot.energy_gain += item["value"]
        elif item["id"] == 106:  # EMP Shield
            bot.emp_shield = True

# -----------------------------
# Abilities
# -----------------------------
def use_ability(attacker, defender, log, round_num=1, rng=None):
    if attacker.ability_used:
        return
    if not (attacker.hp < 40 or round_num == 6):
        return

    if rng is None:
        rng = random.Random()

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

    # Dodge check — attacker LOGIC reduces defender's effective dodge (accuracy)
    # Final Dodge = Dodge Chance × (100 / (100 + Attacker LOGIC))
    if defender.clk > attacker.clk:
        clk_gap = defender.clk - attacker.clk
        dodge_chance = (clk_gap * (defender.luck / 100.0)) / 100.0  # keep it small
        dodge_chance = max(0.0, min(dodge_chance, 0.35))             # cap at 35%
        attacker_logic = float(attacker.logic or 0)
        final_dodge = dodge_chance * (100.0 / (100.0 + attacker_logic))
        if rng.random() < final_dodge:
            defender.dodges += 1
            log_line(log, "dodge", f"🌀 {defender.name} dodged the attack!")
            log_line(log, "status", f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")
            return 0.0

    # Critical hit check — defender LOGIC reduces incoming crit chance
    # Effective Crit Chance = BaseCrit × (100 / (100 + Defender LOGIC))
    base_crit_pct = float(attacker.luck or 0) + float(getattr(attacker, "crit_bonus_pct", 0.0))
    defender_logic = float(defender.logic or 0)
    effective_crit_pct = base_crit_pct * (100.0 / (100.0 + defender_logic))
    is_crit = rng.random() < (effective_crit_pct / 100.0)
    if is_crit:
        attacker.critical_hits += 1
        log_line(log, "crit", f"💥 Critical Hit! {attacker.name} lands a devastating strike!")
        base_proc *= 2.0

    # Track damage dealt
    attacker.damage_dealt += float(base_proc)
    return float(base_proc)

def battle_round(botA, botB, log, rng, arena="neutral", round_num=1):
    botA.rounds_alive += 1
    botB.rounds_alive += 1

    # Apply per-turn item effects
    for bot in (botA, botB):
        if bot.regen > 0:
            bot.hp += bot.regen
            log_line(log, "regen", f"💚 {bot.name} regenerates {bot.regen} HP!")
        if bot.energy_gain > 0:
            bot.energy += bot.energy_gain
            log_line(log, "energy", f"⚡ {bot.name} gains {bot.energy_gain} energy!")
        if bot.energy_drain > 0 and not bot.emp_shield:
            bot.energy -= bot.energy_drain
            log_line(log, "energy", f"🔻 {bot.name} loses {bot.energy_drain} energy from Overclock!")
        bot.energy = max(bot.energy, 0)
    round_had_damage = False
    # Track rounds alive

    def apply_round_upgrades(bot):
        if bot.upgrade_overclock_unit and not bot.upgrade_emp_shield:
            bot.energy = max((bot.energy or 0) - 5, 0)

        if bot.upgrade_energy_recycler:
            bot.energy = min((bot.energy or 0) + 10, bot.max_energy)

        if bot.upgrade_regen_core:
            heal = int((bot.max_hp or 0) * 0.05)
            if heal > 0:
                bot.hp = min((bot.hp or 0) + heal, bot.max_hp)

    apply_round_upgrades(botA)
    apply_round_upgrades(botB)

    # CHAOS-RND: per-turn random buffs/debuffs
    def apply_chaos(bot):
        if getattr(bot, "algorithm", None) != "CHAOS-RND":
            return

        stats = ["hp", "energy", "proc", "defense", "clk", "luck", "logic"]
        chosen = rng.sample(stats, 2)
        changes = []

        for stat in chosen:
            direction = rng.choice(["up", "down"])
            factor = 1.10 if direction == "up" else 0.90
            old_value = getattr(bot, stat)
            new_value = int(old_value * factor)
            # Ensure stats don't drop below 1 for core attributes
            if stat in {"hp", "energy", "proc", "defense", "clk", "luck", "logic"}:
                new_value = max(new_value, 1)
            setattr(bot, stat, new_value)
            changes.append((stat, direction, old_value, new_value))

        # Log a concise summary of changes
        if changes:
            parts = []
            for stat, direction, old, new in changes:
                sign = "+" if direction == "up" else "-"
                parts.append(f"{stat.upper()} {sign}10% ({old} → {new})")
            msg = f"⚙️ CHAOS-RND surges! {bot.name}'s " + ", ".join(parts) + "."
            log_line(log, "special", msg)

    apply_chaos(botA)
    apply_chaos(botB)

    turn_order = calculate_turn_order(botA, botB, rng)

    for attacker in turn_order:
        defender = botB if attacker == botA else botA

        if not attacker.is_alive() or not defender.is_alive():
            continue

        # baseline energy cost per attack
        attacker.energy -= 10
        attacker.energy = max(attacker.energy, 0)

        if not attacker.is_alive():
            log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
            return {"winner": defender.name, "damage": round_had_damage}

        use_ability(attacker, defender, log=log, round_num=round_num, rng=rng)

        damage = calculate_damage(attacker, defender, log, rng, arena=arena)
        if damage > 0:
            round_had_damage = True
        defender.hp = max(defender.hp - damage, 0)

        log_line(log, "attack", f"{attacker.name} attacks {defender.name} for {damage:.2f} damage!")
        log_line(log, "status", f"{defender.name} HP: {defender.hp:.2f}, Energy: {defender.energy:.2f}")

        if attacker.extra_attacks > 0 and defender.is_alive():
            attacker.extra_attacks -= 1
            attacker.energy -= 10
            attacker.energy = max(attacker.energy, 0)
            if not attacker.is_alive():
                log_line(log, "energy", f"{attacker.name} has been defeated (out of energy)!")
                return {"winner": defender.name, "damage": round_had_damage}
            extra_dmg = calculate_damage(attacker, defender, log, rng, arena=arena)
            if extra_dmg > 0:
                round_had_damage = True
            defender.hp = max(defender.hp - extra_dmg, 0)
            log_line(log, "attack", f"{attacker.name} strikes again for {extra_dmg:.2f} damage!")

        if not defender.is_alive():
            log_line(log, "defeat", f"{defender.name} has been defeated!")
            return {"winner": attacker.name, "damage": True}

    return {"winner": None, "damage": round_had_damage}

def full_battle(botA, botB, seed=None, arena="neutral"):
    if seed is None:
        seed = random.randint(0, 999999999)

    rng = random.Random(seed)
    log = []
    round_num = 1
    winner = None
    MAX_ROUNDS = 10

    # DRAW rule: draw when both bots don’t land any hits for 10 turns in a row
    NO_HIT_TURN_LIMIT = 10
    no_hit_turns = 0

    def apply_prebattle_upgrades(bot):
        if bot.upgrade_armor_plating:
            bot.defense = int(bot.defense * 1.10)
        if bot.upgrade_overclock_unit:
            bot.clk = int(bot.clk * 1.10)

    apply_prebattle_upgrades(botA)
    apply_prebattle_upgrades(botB)

    # Apply arena mods ONCE
    # Apply arena mods ONCE 
    apply_arena_modifiers(botA, arena)
    apply_arena_modifiers(botB, arena)

    intro_line = ARENA_FLAVOR.get(
        arena,
        f"🏟️ Battle begins in the {arena_name(arena)} Arena!"
    )
    log_line(log, "arena", intro_line)

    while botA.is_alive() and botB.is_alive() and round_num <= MAX_ROUNDS:
        # ADAPT-X: after 2 full rounds, permanently boost LOGIC by +10%
        if round_num == 3:
            for bot in (botA, botB):
                if getattr(bot, "algorithm", None) == "ADAPT-X" and not getattr(bot, "_adapt_logic_applied", False):
                    old_logic = bot.logic
                    bot.logic = int(bot.logic * 1.10)
                    bot._adapt_logic_applied = True
                    log_line(
                        log,
                        "special",
                        f"🤖 {bot.name} has adapted! LOGIC increased from {old_logic} to {bot.logic}.",
                    )

        log_line(log, "round", f"(Round {round_num})")

        # Track HP BEFORE the round
        hpA_before = float(botA.hp or 0)
        hpB_before = float(botB.hp or 0)

        round_result = battle_round(
            botA,
            botB,
            log,
            rng=rng,
            arena=arena,
            round_num=round_num
        )

        winner = round_result["winner"]
        round_had_damage = round_result["damage"]

        if winner is not None:
            log_line(log, "battleover", f"Battle Over! Winner: {winner}")
            break

        if not round_had_damage:
            no_hit_turns += 1
            log_line(
                log,
                "system",
                f"No hits landed this round. No-hit rounds: {no_hit_turns}/{NO_HIT_TURN_LIMIT}"
            )

            if no_hit_turns >= NO_HIT_TURN_LIMIT:
                winner = "draw"
                log_line(
                    log,
                    "battleover",
                    f"DRAW! No hits landed for {NO_HIT_TURN_LIMIT} rounds in a row."
                )
                break
        else:
            no_hit_turns = 0

        round_num += 1
    
    if round_num > MAX_ROUNDS and winner is None:
        winner = "draw"
        log_line(log, "battleover", " DRAW! Maximum rounds reached.")

    if winner == "draw" or winner is None:
        botA_points = 0
        botB_points = 0
    elif winner == botA.name:
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
    bot1 = BattleBot(
        "Alpha",
        hp=100,
        energy=50,
        proc=30,
        defense=10,
        clk=14,
        luck=10,
        weapon_type="melee",
        special_effect="Time Dilation",
        algorithm="CHAOS-RND",
    )
    bot2 = BattleBot(
        "Beta",
        hp=120,
        energy=50,
        proc=25,
        defense=12,
        clk=14,
        luck=10,
        weapon_type="ranged",
        special_effect="Evolve Protocol",
        algorithm="ADAPT-X",
    )

    # 🎲 Randomly pick Ironclash, Skyline, Neutral, or Frozen
    chosen_arena = random.choice(["ironclash", "skyline", "neutral", "frozen"])
    result = full_battle(bot1, bot2, arena=chosen_arena)
    print("Winner:", result["winner"])
    for t, msg in result["log"]:
        print(f"[{t}] {msg}")

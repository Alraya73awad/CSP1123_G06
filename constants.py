CURRENCY_NAME = "Tokens"

# Rank tiers (shared UI/logic)
RANK_TIERS = [
    {"name": "Prototype", "min": 0, "max": 799, "icon": "🔧", "color": "lightblue"},
    {"name": "Circuit", "min": 800, "max": 999, "icon": "⚡", "color": "yellow"},
    {"name": "Processor", "min": 1000, "max": 1199, "icon": "🖥️", "color": "orange"},
    {"name": "Mainframe", "min": 1200, "max": 1399, "icon": "💻", "color": "cyan"},
    {"name": "Quantum", "min": 1400, "max": 1599, "icon": "🌌", "color": "magenta"},
    {"name": "Nexus", "min": 1600, "max": None, "icon": "🔮", "color": "red"},
]

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

# ALGORITHMS
algorithms = {
    "VEX-01": "Aggressive",
    "BASL-09": "Defensive",
    "EQUA-12": "Balanced",
    "ADAPT-X": "Adaptive",
    "RUSH-09": "Speed",
    "CHAOS-RND": "Random"
}

# ALGORITHM BUFFS/NERFS
algorithm_effects = {
    "VEX-01": {
        "proc": 1.15,
        "def": 0.9
    },
    "BASL-09": {
        "def": 1.2,
        "clk": 0.9
    },
    "EQUA-12": {
        # No effects
    },
    "ADAPT-X": {    
        "ent": 1.05,
        "proc": 0.9
    },
    "RUSH-09": {    
        "clk": 1.2,
        "def": 0.9
         },
    "CHAOS-RND": {  
        # No static effects
    }
}

ALGORITHM_XP_MULTIPLIER = {
    "VEX-01": 1.15,
    "BASL-09": 1.10,
    "EQUA-12": 1.00,
    "ADAPT-X": 1.20,
    "RUSH-09": 1.10,
    "CHAOS-RND": 1.30 
}

# ALGORITHM DESCRIPTIONS
algorithm_descriptions = {
    "VEX-01": "Vexor Assault Kernel: Built for aggressive attack routines. Prioritizes damage output at the cost of stability. +15% PROC, -10% DEF",
    "BASL-09": "Bastion Logic Framework: Defensive fortress AI that fortifies its shielding subroutines above all else. +20% DEF, -10% CLK",
    "EQUA-12": "Equilibrium Core Matrix: Balanced core algorithm ensuring even system resource allocation. No buffs or nerfs.",
    "ADAPT-X": "Adaptive Pattern Synthesizer: Self-learning AI that adjusts its combat model mid-battle. +10% LOGIC after 2 turns, +5% ENT, -10% PROC",
    "RUSH-09": "Rapid Unit Synchronization Hub: An advanced AI core utilizing probabilistic threading for extreme combat reflexes. Fast but fragile. +20% CLK, -10% DEF",
    "CHAOS-RND": "Chaotic Execution Driver: Unstable algorithm driven by randomized decision-making. High volatility, unpredictable results. Unstable modifiers each battle"
}
XP_TABLE = {
    1: {"to_next": 50, "total": 50},
    2: {"to_next": 200, "total": 250},
    3: {"to_next": 450, "total": 700},
    4: {"to_next": 800, "total": 1500},
    5: {"to_next": 1250, "total": 2750},
    10: {"to_next": 5000, "total": 14250},
}
UPGRADES = [
    {"id": 1, "name": "Attack Upgrade", "stat": "attack", "amount": 5, "cost": 50, "desc": None},
    {"id": 2, "name": "Defense Upgrade", "stat": "defense", "amount": 5, "cost": 50, "desc": None},
    {"id": 3, "name": "Speed Booster", "stat": "speed", "amount": 3, "cost": 40, "desc": None},
    {"id": 4, "name": "AI Logic Module", "stat": None, "amount": 0, "cost": 100, "desc": "Custom AI enhancement"},
    {"id": 5, "name": "Armor Plating", "stat": "defense", "amount": 10, "cost": 75, "desc": None},
    {"id": 6, "name": "Energy Core", "stat": None, "amount": 0, "cost": 120, "desc": "Power boost module"},
]

PASSIVE_ITEMS = [
    {"id": 1, "name": "Steady Core", "desc": "Immune to random stat drops.", "cost": 25},
    {"id": 2, "name": "Efficient Circuit", "desc": "Uses 10% less Energy for abilities.", "cost": 50},
    {"id": 3, "name": "Critical Logic", "desc": "+10% Crit damage.", "cost": 60},
    {"id": 4, "name": "Backup OS", "desc": "Survive with 1 HP once per battle.", "cost": 150},
]

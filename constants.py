CURRENCY_NAME = "Tokens"

STORE_ITEMS = [
    {
        "id": 1,
        "name": "Code cutter",
        "desc": "Standard starter dagger; lightweight and fast.",
        "cost": 20,
        "stat": None  # Not directly affecting bot stats
    },
    {
        "id": 2,
        "name": "Bit Blaster",
        "desc": "Fires compressed data packets as projectiles",
        "cost": 20,
        "stat": None
    },
    {
        "id": 3,
        "name": "Pulse Blade",
        "desc": "Emits rhythmic energy waves when swung.",
        "cost": 40,
        "stat": None
    },
    {
        "id": 4,
        "name": "Flux Rifle",
        "desc": "Uses magnetic flux to accelerate energy projectiles.",
        "cost": 40,
        "stat": None
    },
    {
        "id": 5,
        "name": "Null Gauntlets",
        "desc": "Fists that erase enemy circuits on impact.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 6,
        "name": "Firewall Blaster",
        "desc": "Fists that erase enemy circuits on impact.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 7,
        "name": "Syntax Scythe",
        "desc": "A scythe that parses enemies into fragments.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 8,
        "name": "Quantum Pistol",
        "desc": "Phases bullets through defenses like a clever exploit.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 9,
        "name": "Overclock Whip",
        "desc": "An electrified whip that strikes faster with each swing.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 10,
        "name": "Virus Launcher",
        "desc": "Infects enemies with code that slowly disables them.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 11,
        "name": "AI Katana",
        "desc": "A smart blade that predicts enemy moves before they strike.",
        "cost": 60,
        "stat": None
    },
    {
        "id": 12,
        "name": "Packet Bomb",
        "desc": "Explodes into fragments of damaging code on impact.",
        "cost": 60,
        "stat": None
    }
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
from app import app
from extensions import db
from models import Weapon, Ability

# --- Weapons ---
weapons = [
    Weapon(
        name="Code Cutter",
        type="Melee",
        atk_bonus=5,
        tier=1,
        description="Standard starter dagger; lightweight and fast."
    ),
    Weapon(
        name="Bit Blaster",
        type="Ranged",
        atk_bonus=5,
        tier=1,
        description="Fires compressed data packets as projectiles."
    ),
    Weapon(
        name="Pulse Blade",
        type="Melee",
        atk_bonus=8,
        tier=2,
        description="Emits rhythmic energy waves when swung."
    ),
    Weapon(
        name="Flux Rifle",
        type="Ranged",
        atk_bonus=8,
        tier=2,
        description="Uses magnetic flux to accelerate energy projectiles."
    ),
    Weapon(
        name="Null Gauntlets",
        type="Melee",
        atk_bonus=16,
        tier=3,
        description="Fists that erase enemy circuits on impact."
    ),
    Weapon(
        name="Firewall Cannon",
        type="Ranged",
        atk_bonus=16,
        tier=3,
        description="Shoots bursts of searing digital energy."
    ),
    Weapon(
        name="Syntax Scythe",
        type="Melee",
        atk_bonus=33,
        tier=4,
        description="A scythe that parses enemies into fragments."
    ),
    Weapon(
        name="Quantum Pistol",
        type="Ranged",
        atk_bonus=33,
        tier=4,
        description="Phases bullets through defenses like a clever exploit."
    ),
    Weapon(
        name="Overclock Whip",
        type="Melee",
        atk_bonus=55,
        tier=5,
        description="Electrified whip that strikes faster with each swing."
    ),
    Weapon(
        name="Virus Launcher",
        type="Ranged",
        atk_bonus=55,
        tier=5,
        description="Infects enemies with code that slowly disables them."
    ),
    Weapon(
        name="AI Katana",
        type="Melee",
        atk_bonus=100,
        tier=6,
        description="A smart blade that predicts enemy moves before they strike."
    ),
    Weapon(
        name="Packet Bomb",
        type="Ranged",
        atk_bonus=100,
        tier=6,
        description="Explodes into fragments of damaging code on impact."
    ),
]

# --- Abilities (your traits) ---
abilities = [
    Ability(
        name="Steady Core",
        description="Immune to random stat drops.",
        energy_cost=0,
        effect_type="passive",
        effect_value=0
    ),
    Ability(
        name="Efficient Circuit",
        description="Uses 10% less Energy for abilities.",
        energy_cost=0,
        effect_type="passive",
        effect_value=0
    ),
    Ability(
        name="Critical Logic",
        description="+10% Crit damage.",
        energy_cost=0,
        effect_type="passive",
        effect_value=10
    ),
    Ability(
        name="Backup OS",
        description="Survive with 1 HP once.",
        energy_cost=0,
        effect_type="passive",
        effect_value=0
    ),
]

# --- Seeding ---
with app.app_context():
    for w in weapons:
        db.session.add(w)
    for a in abilities:
        db.session.add(a)
    db.session.commit()

    print("Weapons and Abilities seeded successfully!")

    # Print results
    print("\n--- Weapons ---")
    for w in Weapon.query.all():
        print(f"{w.name} (Tier {w.tier}) - ATK Bonus: {w.atk_bonus}, Type: {w.type}")

    print("\n--- Abilities ---")
    for a in Ability.query.all():
        print(f"{a.name} | {a.description}")
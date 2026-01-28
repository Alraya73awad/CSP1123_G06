from extensions import db
from models import Weapon

def seed_weapons():
    if Weapon.query.first():
        print("Weapons already seeded.")
        return

    weapons = [
        Weapon(
            name="Code Cutter",
            type="Melee",
            atk_bonus=5,
            tier = 1,
            price = 20,
            description="Standard starter dagger; lightweight and fast."
        ),
        Weapon(
            name="Bit Blaster",
            type="Ranged",
            atk_bonus=5,
            tier = 1,
            price = 20,
            description="Fires compressed data packets as projectiles."
        ),
        Weapon(
            name="Pulse Blade",
            type="Melee",
            atk_bonus=8,
            tier = 2,
            price = 40,
            description="Emits rhythmic energy waves when swung."
        ),
        Weapon(
            name="Flux Rifle",
            type="Ranged",
            atk_bonus=8,
            tier = 2,
            price = 40,
            description="Uses magnetic flux to accelerate energy projectiles."
        ),
        Weapon(
            name="Null Gauntlets",
            type="Melee",
            atk_bonus=16,
            tier = 3,
            price = 60,
            description="Fists that erase enemy circuits on impact."
        ),
        Weapon(
            name="Firewall Cannon",
            type="Ranged",
            atk_bonus=16,
            tier = 3,
            price = 60,
            description="Shoots bursts of searing digital energy."
        ),
        Weapon(
            name="Syntax Scythe",
            type="Melee",
            atk_bonus=33,
            tier = 4,
            price = 80,
            description="A scythe that parses enemies into fragments."
        ),
        Weapon(
            name="Quantum Pistol",
            type="Ranged",
            atk_bonus=33,
            tier = 4,
            price = 80,
            description="Phases bullets through defenses like a clever exploit."
        ),
        Weapon(
            name="Overclock Whip",
            type="Melee",
            atk_bonus=55,
            tier = 5,
            price = 100,
            description="Electrified whip that strikes faster with each swing."
        ),
        Weapon(
            name="Virus Launcher",
            type="Ranged",
            atk_bonus=55,
            tier = 5,
            price = 100,
            description="Infects enemies with code that slowly disables them."
        ),
        Weapon(
            name="AI Katana",
            type="Melee",
            atk_bonus=100,
            tier = 6,
            price = 200,
            description="A smart blade that predicts enemy moves before they strike."
        ),
        Weapon(
            name="Packet Bomb",
            type="Ranged",
            atk_bonus=100,
            tier = 6,
            price = 200,
            description="Explodes into fragments of damaging code on impact."
        ),
    ]

    db.session.add_all(weapons)
    db.session.commit()
    print("Weapons seeded successfully!")

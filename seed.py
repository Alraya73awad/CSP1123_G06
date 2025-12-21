from app import create_app
from extensions import db
from models import Modules

app = create_app()

with app.app_context():
    db.session.query(Modules).delete()
    db.create_all()

    modules = [
        Modules(
            name="Armor Plating",
            description="Reinforced plating increases defense.",
            defense_boost=10
        ),
        Modules(
            name="Overclock Unit",
            description="Pushes CPU cycles for faster actions.",
            speed_boost=15
        ),
        Modules(
            name="Energy Recycler",
            description="Converts waste heat into usable energy.",
            power_boost=5
        ),
        Modules(
            name="Regen Core",
            description="Restores 5% HP each turn.",
            defense_boost=5
        ),
        Modules(
            name="Logic Enhancer",
            description="Improves decision-making algorithms.",
            power_boost=10
        ),
        Modules(
            name="Luck Amplifier",
            description="Random number generator tuned for better odds.",
            speed_boost=5
        ),
        Modules(
            name="Adaptive Shield",
            description="Dynamic shielding adjusts to incoming attacks.",
            defense_boost=15
        ),
        Modules(
            name="Turbo Thrusters",
            description="High-speed propulsion system.",
            speed_boost=20
        ),
    ]

    db.session.add_all(modules)
    db.session.commit()

    print("Seeded modules successfully into the Modules table.")
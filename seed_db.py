from faker import Faker
from werkzeug.security import generate_password_hash
import random

from app import app
from extensions import db
from models import User, Bot, Weapon, WeaponOwnership
from constants import algorithms, XP_TABLE
from seed_weapons import seed_weapons

fake = Faker()

UPGRADE_FLAGS = [
    "upgrade_armor_plating",
    "upgrade_overclock_unit",
    "upgrade_regen_core",
    "upgrade_critical_subroutine",
    "upgrade_energy_recycler",
    "upgrade_emp_shield",
]


def clamp(value, low, high):
    return max(low, min(value, high))


def xp_for_level(level):
    if level in XP_TABLE:
        return XP_TABLE[level]["to_next"]
    known_levels = sorted(XP_TABLE.keys())
    nearest = max((lv for lv in known_levels if lv <= level), default=1)
    base = XP_TABLE[nearest]["to_next"]
    return int(base + (level - nearest) * 50)


def make_bot_name():
    return fake.word().capitalize() + "-" + str(random.randint(10, 99))


def distribute_stat_points(base_stats, points):
    stats = base_stats.copy()
    keys = list(stats.keys())
    for _ in range(points):
        key = random.choice(keys)
        stats[key] += 1
    return stats


def create_test_players(num_players=50, min_bots=1, max_bots=3, clear_existing=False):
    """Creates fake players with bots, weapons, and upgrades for battle testing."""
    with app.app_context():
        if clear_existing:
            WeaponOwnership.query.delete()
            Bot.query.delete()
            User.query.delete()
            db.session.commit()

        if Weapon.query.count() == 0:
            seed_weapons()

        weapons = Weapon.query.all()
        if not weapons:
            raise RuntimeError("No weapons available. Check seed_weapons().")

        print(f"Creating {num_players} test players with bots...")
        test_password = generate_password_hash("test123")

        for i in range(num_players):
            username = fake.unique.user_name()
            email = fake.unique.email()

            rating = int(clamp(random.gauss(1000, 250), 600, 2000))
            total_games = random.randint(5, 200)
            win_rate = clamp(0.45 + (rating - 1000) / 2000, 0.1, 0.9)
            wins = int(round(total_games * win_rate))
            losses = max(total_games - wins, 0)

            level = int(clamp(random.gauss(12, 6), 1, 30))
            xp = random.randint(0, xp_for_level(level))
            tokens = random.randint(50, 2000)

            user = User(
                username=username,
                email=email,
                password=test_password,
                wins=wins,
                losses=losses,
                rating=rating,
                level=level,
                xp=xp,
                tokens=tokens,
            )
            db.session.add(user)
            db.session.flush()

            bot_count = random.randint(min_bots, max_bots)
            remaining_wins = wins
            remaining_losses = losses

            for b in range(bot_count):
                algo = random.choice(list(algorithms.keys()))
                bot_level = int(clamp(random.gauss(level, 4), 1, 30))
                base_stats = {
                    "hp": 100,
                    "atk": 10,
                    "defense": 10,
                    "speed": 10,
                    "logic": 10,
                    "luck": 10,
                    "energy": 100,
                }

                stat_points = bot_level * 3
                final_stats = distribute_stat_points(base_stats, stat_points)

                bot = Bot(
                    name=make_bot_name(),
                    algorithm=algo,
                    hp=final_stats["hp"],
                    atk=final_stats["atk"],
                    defense=final_stats["defense"],
                    speed=final_stats["speed"],
                    logic=final_stats["logic"],
                    luck=final_stats["luck"],
                    energy=final_stats["energy"],
                    level=bot_level,
                    xp=random.randint(0, xp_for_level(bot_level)),
                    stat_points=random.randint(0, 10),
                    user_id=user.id,
                )

                if b == bot_count - 1:
                    bot.botwins = remaining_wins
                    bot.botlosses = remaining_losses
                else:
                    bot.botwins = random.randint(0, remaining_wins)
                    bot.botlosses = random.randint(0, remaining_losses)
                    remaining_wins -= bot.botwins
                    remaining_losses -= bot.botlosses

                for flag in random.sample(UPGRADE_FLAGS, random.randint(0, 3)):
                    setattr(bot, flag, True)

                db.session.add(bot)
                db.session.flush()

                if random.random() < 0.7:
                    weapon = random.choice(weapons)
                    ownership = WeaponOwnership(
                        user_id=user.id,
                        weapon_id=weapon.id,
                        bot_id=bot.id,
                        equipped=True,
                    )
                    db.session.add(ownership)

            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{num_players} players...")

        db.session.commit()
        print(f"✅ Successfully created {num_players} test players with bots!")


if __name__ == "__main__":
    create_test_players(num_players=100, min_bots=1, max_bots=3, clear_existing=False)

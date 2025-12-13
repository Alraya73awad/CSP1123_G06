from app import db
from flask_login import current_user

def add_xp_and_rewards(user, result):
    xp_rewards = {
        "win": 50,
        "lose": 20,
        "draw": 30
    }

    token_rewards = {
        "win": 10,
        "lose": 3,
        "draw": 5
    }

    user.xp += xp_rewards[result]
    user.tokens += token_rewards[result]

    # Level up
    while user.xp >= user.level * 100:
        user.xp -= user.level * 100
        user.level += 1

    db.session.commit()

def process_battle_result(winner):
    if winner == "player":
        add_xp_and_rewards(current_user, "win")
    elif winner == "bot":
        add_xp_and_rewards(current_user, "lose")
    else:
        add_xp_and_rewards(current_user, "draw")

winner = process_battle_result
process_battle_result(winner)

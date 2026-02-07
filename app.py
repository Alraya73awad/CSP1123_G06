import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps
from sqlalchemy import or_

from extensions import db
from constants import CURRENCY_NAME,CHARACTER_ITEMS, algorithms, algorithm_effects, algorithm_descriptions, XP_TABLE, PASSIVE_ITEMS, UPGRADES, RANK_TIERS
from battle import BattleBot, full_battle, calculate_bot_stat_points, ARENA_EFFECTS
from models import User, Bot, History, Weapon, WeaponOwnership

app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "dev_secret_key"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "clash_of_code.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://","postgresql://",1)
    
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)



@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

def get_rank_tier(rating):
    for tier in RANK_TIERS:
        max_rating = tier["max"]
        if max_rating is None:
            if rating >= tier["min"]:
                return tier
        elif tier["min"] <= rating <= max_rating:
            return tier
    return RANK_TIERS[0]

@app.context_processor
def inject_rank_helpers():
    return dict(get_rank_tier=get_rank_tier, rank_tiers=RANK_TIERS)

def get_upgrade_labels(bot):
    labels = []
    if getattr(bot, "upgrade_armor_plating", False):
        labels.append("Armor Plating")
    if getattr(bot, "upgrade_overclock_unit", False):
        labels.append("Overclock Unit")
    if getattr(bot, "upgrade_regen_core", False):
        labels.append("Regen Core")
    if getattr(bot, "upgrade_critical_subroutine", False):
        labels.append("Critical Subroutine")
    if getattr(bot, "upgrade_energy_recycler", False):
        labels.append("Energy Recycler")
    if getattr(bot, "upgrade_emp_shield", False):
        labels.append("EMP Shield")
    return labels

def apply_upgrade_arena_effects(stats, upgrades, arena="neutral"):
    effective = stats.copy()

    if upgrades.get("armor"):
        effective["def"] = int((effective.get("def") or 0) * 1.10)
    if upgrades.get("overclock"):
        effective["clk"] = int((effective.get("clk") or 0) * 1.10)
    if upgrades.get("crit"):
        effective["luck"] = int((effective.get("luck") or 0) + 5)

    effects = ARENA_EFFECTS.get(arena, ARENA_EFFECTS["neutral"])
    effective["clk"] = int((effective.get("clk") or 0) * effects.get("spd_mod", 1.0))
    effective["def"] = int((effective.get("def") or 0) * effects.get("def_mod", 1.0))

    return effective

@app.context_processor
def inject_upgrade_helpers():
    return dict(get_upgrade_labels=get_upgrade_labels)

def calculate_elo_change(winner_rating, loser_rating, k_factor=32):
    """
    Calculate ELO rating changes for winner and loser.
    
    Args:
        winner_rating: Current rating of the winner
        loser_rating: Current rating of the loser
        k_factor: How much ratings change per game (default 32)
    
    Returns:
        (winner_change, loser_change) - both as integers
    """
    # Calculate expected win probability for the winner
    expected_win = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    
    # Calculate rating changes
    winner_change = int(k_factor * (1 - expected_win))
    loser_change = int(k_factor * (0 - (1 - expected_win)))
    
    return winner_change, loser_change

# Stat Min/Max Values
STAT_LIMITS = {
    "hp": (100, 999),
    "energy": (100, 999),
    "atk": (10, 999),
    "defense": (10, 999),
    "speed": (10, 999),
    "logic": (10, 999),
    "luck": (10, 999),
}
    
#routes
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html", username=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))


    if request.method == "POST":
        identifier = request.form.get("username")
        password = request.form.get("password")

        # Otherwise check normal user
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

        if user and not user.banned and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        elif user and user.banned:
            flash("Your account has been banned. Contact support.", "danger")
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

#register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("email")
        new_password = request.form.get("new_password")
        user = User.query.filter(or_(User.username == identifier, User.email == identifier)).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successfully!", "success")
        else:
            flash("Player ID not found.", "danger")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if not User.query.get(user_id):
            session.clear()
            flash("Session expired. Please log in again.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("login"))

    # HANDLE BOT CREATION (FORM SUBMIT)
    if request.method == "POST":
        name = request.form.get("name")
        algorithm = request.form.get("algorithm")

        if not name or not algorithm:
            flash("Please enter a bot name and select an algorithm.", "danger")
        else:
            new_bot = Bot(name=name, algorithm=algorithm, user_id=user.id)
            db.session.add(new_bot)
            db.session.commit()
            flash("Bot created successfully!", "success")

        return redirect(url_for("dashboard"))

    enhanced_bots = []
    for bot in user.bots:
        total_proc = getattr(bot, "total_proc", None)
        if total_proc is None:
            total_proc = int(bot.atk or 0)

        base_stats = {
            "int": int(bot.hp or 0),
            "proc": int(total_proc or 0),
            "def": int(bot.defense or 0),
            "clk": int(bot.speed or 0),
            "logic": int(bot.logic or 0),
            "luck": int(bot.luck or 0),
            "pwr": int(bot.energy or 0),
        }

        effects = algorithm_effects.get(bot.algorithm, {})
        final_stats = {stat: int(base * effects.get(stat, 1.0)) for stat, base in base_stats.items()}

        enhanced_bots.append({"bot": bot, "final_stats": final_stats})

    return render_template(
        "dashboard.html",
        user=user,
        tokens=int(user.tokens or 0),
        enhanced_bots=enhanced_bots,
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions,
        currency=CURRENCY_NAME,

        xp_table=XP_TABLE,
    )


#logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


# Create bot
@app.route("/create_bot", methods=["GET", "POST"])
@login_required
def create_bot():
    if request.method == "POST":
        name = request.form.get("name")
        algorithm = request.form.get("algorithm")

        if not name or not algorithm:
            flash("Please provide a bot name and select an algorithm.", "danger")
            return redirect(url_for("create_bot"))

        new_bot = Bot(name=name, algorithm=algorithm, user_id=session["user_id"])
        db.session.add(new_bot)
        db.session.commit()

        flash("Bot created successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template(
        "create_bot.html",
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions,
    )

def bot_xp_to_next_level(level):
    return 50 + (level - 1) * 25

# manage bot
@app.route('/manage_bot')
@login_required
def manage_bot():
    if 'user_id' not in session:
        flash("Please log in to manage your bots.", "warning")
        return redirect(url_for('login'))

    user_bots = Bot.query.filter_by(user_id=session['user_id']).all()
    user = User.query.get(session["user_id"])
    bots = user.bots

    enhanced_bots = []
    for bot in bots:
        base_stats = {
            "int": bot.hp,
            "proc": bot.total_proc,
            "def": bot.defense,   
            "clk": bot.speed,
            "logic": bot.logic,
            "luck": bot.luck,
            "pwr": bot.energy
        }

        effects = algorithm_effects.get(bot.algorithm, {})
        final_stats = {}

        for stat, base in base_stats.items():
            multiplier = effects.get(stat, 1.0)
            final_stats[stat] = int(base * multiplier)

        xp_needed = bot_xp_to_next_level(bot.level or 1)
        xp_current = int(bot.xp or 0)
        xp_percent = int((xp_current / xp_needed) * 100) if xp_needed > 0 else 0

        enhanced_bots.append({
            "bot": bot,
            "final_stats": final_stats
        })
    return render_template('manage_bot.html', enhanced_bots=enhanced_bots, bots=user_bots, algorithms=algorithms, algorithm_descriptions=algorithm_descriptions)

# Other pages
@app.route("/store")
@login_required
def store():
    user = User.query.get(session["user_id"])
    bots = Bot.query.filter_by(user_id=user.id).all()
    credits = int(user.tokens or 0)

    weapons = Weapon.query.order_by(Weapon.tier.asc(), Weapon.price.asc(), Weapon.name.asc()).all()

    owned = WeaponOwnership.query.filter_by(user_id=user.id).all()
    owned_map = {ow.weapon_id: ow for ow in owned} 

    return render_template(
        "store.html",
        passive_items=PASSIVE_ITEMS,
        bots=bots,
        credits=credits,
        weapons=weapons,
        owned_map=owned_map
    )




@app.route('/buy_passive/<int:passive_id>', methods=['POST'])
@login_required
def buy_passive(passive_id):
    user = User.query.get(session['user_id'])
    bot_id = request.form.get('bot_id')
    bot = Bot.query.get(bot_id)

    passive = next((p for p in PASSIVE_ITEMS if p["id"] == passive_id), None)
    if not passive:
        flash("Passive not found", "danger")
        return redirect(url_for("store"))

    if user.tokens < passive["cost"]:
        flash("Not enough credits!", "danger")
        return redirect(url_for("store"))

    user.tokens -= passive["cost"]

    bot.passive_effect = passive["name"]

    db.session.commit()
    flash(f"{bot.name} learned passive: {passive['name']}", "success")
    return redirect(url_for("store"))

@app.route("/character")
@login_required
def character():
    user = User.query.get(session["user_id"])
    bots = Bot.query.filter_by(user_id=user.id).all()

    selected_bot_id = request.args.get("bot_id")
    selected_bot = None

    if bots:
        if selected_bot_id:
            selected_bot = Bot.query.filter_by(id=selected_bot_id, user_id=user.id).first()
        if not selected_bot:
            selected_bot = bots[0]

    xp_to_next = XP_TABLE.get(user.level, {"to_next": 50})["to_next"]

    return render_template(
        "character.html",
        user=user,
        bots=bots,
        selected_bot=selected_bot,
        tokens=int(user.tokens or 0),
        xp_to_next=xp_to_next,
        CHARACTER_ITEMS=CHARACTER_ITEMS
    )


@app.route("/equip_weapon_from_store", methods=["POST"])
@login_required
def equip_weapon_from_store():
    user = User.query.get(session["user_id"])

    ownership_id = request.form.get("ownership_id")
    bot_id = request.form.get("bot_id")

    if not ownership_id or not bot_id:
        flash("Invalid equip request.", "danger")
        return redirect(url_for("store"))

    bot = Bot.query.filter_by(id=int(bot_id), user_id=user.id).first()
    if not bot:
        flash("Invalid bot.", "danger")
        return redirect(url_for("store"))

    ow = WeaponOwnership.query.filter_by(id=int(ownership_id), user_id=user.id).first()
    if not ow:
        flash("Weapon not found in your inventory.", "danger")
        return redirect(url_for("store"))

    # Unequip any currently equipped weapon on this bot
    WeaponOwnership.query.filter_by(bot_id=bot.id, equipped=True).update(
        {"equipped": False, "bot_id": None}
    )

    # If this weapon is equipped on a different bot, unequip it there
    WeaponOwnership.query.filter_by(id=ow.id).update(
        {"equipped": False, "bot_id": None}
    )

    # Equip it to selected bot
    ow.bot_id = bot.id
    ow.equipped = True

    db.session.commit()
    flash(f"{ow.weapon.name} equipped to {bot.name}!", "success")
    return redirect(url_for("store"))


# profile page
@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        flash("Error loading profile.", "danger")
        return redirect(url_for('login'))
    
    # Calculate win rate
    total_battles = user.wins + user.losses
    win_rate = (user.wins / total_battles * 100) if total_battles > 0 else 0
    rank = get_rank_tier(user.rating)

    return render_template(
        'profile.html',
        username=user.username,
        email=user.email,
        level=user.level,
        xp=user.xp,
        tokens=user.tokens,
        user=user,
        win_rate=win_rate,
        total_battles=total_battles,
        rank=rank
    )


from constants import CHARACTER_ITEMS

@app.route("/buy_character", methods=["POST"])
@login_required
def buy_character():
    user = User.query.get(session.get("user_id"))
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))

    # Validate bot_id
    bot_id = request.form.get("bot_id", "").strip()
    if not bot_id.isdigit():
        flash("Invalid character selection.", "danger")
        return redirect(url_for("character"))
    bot_id = int(bot_id)

    bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
    if not bot:
        flash("Character not found.", "danger")
        return redirect(url_for("character"))

    # Validate purchase_id
    purchase_id = request.form.get("purchase_id", "").strip()
    if not purchase_id.isdigit():
        flash("No upgrade selected.", "danger")
        return redirect(url_for("character", bot_id=bot.id))
    purchase_id = int(purchase_id)

    # Find upgrade
    item = next((i for i in CHARACTER_ITEMS if i["id"] == purchase_id), None)
    if not item:
        flash("Invalid upgrade selected.", "danger")
        return redirect(url_for("character", bot_id=bot.id))

    cost = int(item["cost"])
    user.tokens = int(user.tokens or 0)

    if user.tokens < cost:
        flash("Not enough tokens!", "danger")
        return redirect(url_for("character", bot_id=bot.id))

    flag = item.get("flag")
    if not flag or not hasattr(bot, flag):
        flash(f"{item['name']} is not implemented yet. No tokens were spent.", "warning")
        return redirect(url_for("character", bot_id=bot.id))

    upgrade_flags = [
        "upgrade_armor_plating",
        "upgrade_overclock_unit",
        "upgrade_regen_core",
        "upgrade_critical_subroutine",
        "upgrade_energy_recycler",
        "upgrade_emp_shield",
    ]
    active_upgrades = sum(1 for f in upgrade_flags if getattr(bot, f, False))
    if active_upgrades >= 3 and not getattr(bot, flag):
        flash("Upgrade cap reached (3). Use an upgrade in battle before buying another.", "warning")
        return redirect(url_for("character", bot_id=bot.id))

    if getattr(bot, flag):
        flash(f"{item['name']} is already installed on {bot.name}.", "warning")
        return redirect(url_for("character", bot_id=bot.id))

    user.tokens -= cost
    setattr(bot, flag, True)
    db.session.commit()
    flash(f"{item['name']} purchased for {bot.name}! (-{cost} tokens)", "success")
    return redirect(url_for("character", bot_id=bot.id))






@app.route("/update_settings", methods=["POST"])
@login_required
def update_settings():
    user = User.query.get(session["user_id"])
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if username:
        user.username = username
    if email:
        user.email = email
    if password:
        user.password = generate_password_hash(password)

    db.session.commit()
    flash("Settings updated successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    user = User.query.get(session["user_id"])

    # Delete related data
    # Delete weapon ownership
    WeaponOwnership.query.filter_by(user_id=user.id).delete()

    # Delete bots (this will cascade to weapon_ownership if bot_id)
    Bot.query.filter_by(user_id=user.id).delete()

    # Delete history logs where history involves the user
    histories = History.query.filter(or_(History.user1_id == user.id, History.user2_id == user.id)).all()
    for history in histories:
        HistoryLog.query.filter_by(history_id=history.id).delete()
        db.session.delete(history)

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    session.clear()
    flash("Account deleted successfully.", "info")
    return redirect(url_for("home"))

@app.route("/delete_bot/<int:bot_id>", methods=["POST"])
@login_required
def delete_bot(bot_id):
    bot = Bot.query.filter_by(
        id=bot_id,
        user_id=session["user_id"]
    ).first_or_404()

    # Detach bot from history before delete to avoid FK / NOT NULL issues
    History.query.filter_by(bot1_id=bot.id).update({"bot1_id": None})
    History.query.filter_by(bot2_id=bot.id).update({"bot2_id": None})

    db.session.delete(bot)
    db.session.commit()
    flash("Bot deleted successfully.", "success")
    return redirect(url_for("manage_bot"))

@app.route('/edit-bot/<int:bot_id>', methods=['GET', 'POST'])
@login_required
def edit_bot(bot_id):
    bot = Bot.query.filter_by(
        id=bot_id,
        user_id=session["user_id"]
    ).first_or_404()

    def read_stat(name):
        raw_num = (request.form.get(f"{name}_number") or "").strip()
        raw_slider = (request.form.get(name) or "").strip()

        chosen = raw_num if raw_num != "" else raw_slider
        if chosen == "":
            return getattr(bot, name)

        try:
            return int(chosen)
        except ValueError:
            return None

    if request.method == "POST":
        new_name = (request.form.get("name") or "").strip()
        new_algorithm = (request.form.get("algorithm") or "").strip()

        # Gather stats from sliders
        new_stats = {stat: read_stat(stat) for stat in STAT_LIMITS.keys()}

        if "preview" in request.form:
            errors = []

            if not new_name:
                errors.append("Bot name cannot be empty.")
            if not new_algorithm:
                errors.append("Please select an algorithm.")

            for stat, val in new_stats.items():
                if val is None:
                    errors.append(f"{stat.upper()} must be an integer.")
                    continue
                low, high = STAT_LIMITS[stat]
                if val < low or val > high:
                    errors.append(f"{stat.upper()} must be between {low} and {high}.")
                    continue
                current_val = int(getattr(bot, stat) or 0)
                if val < current_val:
                    errors.append(f"{stat.upper()} cannot be lower than the current value ({current_val}).")

            if errors:
                for e in errors:
                    flash(e, "danger")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            return render_template(
                "preview_bot.html",
                bot=bot,
                new_stats=new_stats,
                new_name=new_name,
                new_algorithm=new_algorithm
            )

        if "confirm" in request.form:
            if not new_name:
                flash("Bot name cannot be empty.", "danger")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            if not new_algorithm:
                flash("Please select an algorithm.", "danger")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            errors = []
            final_stats = {}

            # Validate stats again (never trust the client)
            for stat in STAT_LIMITS.keys():
                raw = request.form.get(stat)
                if raw is None:
                    errors.append(f"Missing {stat} in confirmation.")
                    continue
                try:
                    val = int(raw)
                except ValueError:
                    errors.append(f"{stat.upper()} must be an integer.")
                    continue

                low, high = STAT_LIMITS[stat]
                if val < low or val > high:
                    errors.append(f"{stat.upper()} must be between {low} and {high}.")
                    continue
                current_val = int(getattr(bot, stat) or 0)
                if val < current_val:
                    errors.append(f"{stat.upper()} cannot be lower than the current value ({current_val}).")
                    continue
                final_stats[stat] = val

            if errors:
                for e in errors:
                    flash(e, "danger")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            # Cost = ONLY increases
            required = 0
            for stat, new_val in final_stats.items():
                cur = int(getattr(bot, stat) or 0)
                diff = new_val - cur
                if diff > 0:
                    required += diff

            available = int(bot.stat_points or 0)
            if required > available:
                flash(f"Not enough stat points. Required {required}, you have {available}.", "danger")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            changed = (
                bot.name != new_name or
                bot.algorithm != new_algorithm or
                any(int(getattr(bot, s) or 0) != int(final_stats[s]) for s in final_stats)
            )
            if not changed:
                flash("No changes were made.", "warning")
                return redirect(url_for("edit_bot", bot_id=bot_id) + "?flash=1")

            # Apply + deduct ONCE
            bot.stat_points = available - required
            bot.name = new_name
            bot.algorithm = new_algorithm
            for stat, val in final_stats.items():
                setattr(bot, stat, val)

            db.session.commit()
            flash("Bot updated successfully.", "success")
            return redirect(url_for("manage_bot") + "?flash=1")

    return render_template(
        "edit_bot.html",
        bot=bot,
        stat_limits=STAT_LIMITS,
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions,
        show_flashes=False
    )

@app.route('/bot/<int:bot_id>')
@login_required
def bot_details(bot_id):
    bot = Bot.query.filter_by(
        id=bot_id,
        user_id=session["user_id"]
    ).first_or_404()

    base_stats = {
        "int": bot.hp,
        "proc": bot.total_proc,
        "def": bot.defense,   
        "clk": bot.speed,
        "logic": bot.logic,
        "ent": bot.luck,
        "pwr": bot.energy
    }

    effects = algorithm_effects.get(bot.algorithm, {})

    final_stats = {}
    multipliers = {}

    for stat, value in base_stats.items():
        multiplier = effects.get(stat, 1.0)
        multipliers[stat] = multiplier
        final_stats[stat] = int(value * multiplier)

    return render_template(
        "bot_details.html",
        bot=bot,
        base_stats=base_stats,
        multipliers=multipliers,
        final_stats=final_stats
    )

@app.route("/bots")
@login_required
def bot_list():
    user_id = session["user_id"]
    bots = Bot.query.filter_by(user_id=user_id).all()

    items = []
    for bot in bots:
        base_stats = {
            "int": bot.hp,
            "proc": bot.total_proc,
            "def": bot.defense,   
            "clk": bot.speed,
            "logic": bot.logic,
            "luck": bot.luck,
            "pwr": bot.energy
        }
        effects = algorithm_effects.get(bot.algorithm, {})
        final_stats = {stat: int(value * effects.get(stat, 1.0)) for stat, value in base_stats.items()}
        items.append({"bot": bot, "final_stats": final_stats})

    return render_template("dashboard.html", bots=items, algorithms=algorithms, algorithm_descriptions=algorithm_descriptions)

@app.route("/combat_log/<int:bot1_id>/<int:bot2_id>")
@login_required
def combat_log(bot1_id, bot2_id):
    # Get bots and user
    bot1 = Bot.query.get_or_404(bot1_id)
    bot2 = Bot.query.get_or_404(bot2_id)
    user = User.query.get(session["user_id"])

    # Apply algorithm stats
    stats1 = apply_algorithm(bot1)
    stats2 = apply_algorithm(bot2)
    stats1_base = stats1
    stats2_base = stats2
    weapon1_ow = WeaponOwnership.query.filter_by(bot_id=bot1.id, equipped=True).first()
    weapon2_ow = WeaponOwnership.query.filter_by(bot_id=bot2.id, equipped=True).first()

    # Get weapon ATK
    weapon1_atk = weapon1_ow.effective_atk() if weapon1_ow else 0
    weapon2_atk = weapon2_ow.effective_atk() if weapon2_ow else 0
    
    # Get algorithm effects
    effects1 = algorithm_effects.get(bot1.algorithm, {})
    effects2 = algorithm_effects.get(bot2.algorithm, {})
    
    # Calculate final proc: (base + weapon) × algorithm multiplier
    base_proc1 = bot1.atk + weapon1_atk
    final_proc1 = int(base_proc1 * effects1.get("proc", 1.0))
    
    base_proc2 = bot2.atk + weapon2_atk
    final_proc2 = int(base_proc2 * effects2.get("proc", 1.0))

    bot1_upgrades = {
        "armor": bot1.upgrade_armor_plating,
        "overclock": bot1.upgrade_overclock_unit,
        "regen": bot1.upgrade_regen_core,
        "crit": bot1.upgrade_critical_subroutine,
        "recycler": bot1.upgrade_energy_recycler,
        "emp": bot1.upgrade_emp_shield,
    }
    bot2_upgrades = {
        "armor": bot2.upgrade_armor_plating,
        "overclock": bot2.upgrade_overclock_unit,
        "regen": bot2.upgrade_regen_core,
        "crit": bot2.upgrade_critical_subroutine,
        "recycler": bot2.upgrade_energy_recycler,
        "emp": bot2.upgrade_emp_shield,
    }

    # Convert to BattleBot
    battleA = BattleBot(
        name=bot1.name,
        hp=stats1["hp"],
        energy=stats1["energy"],
        proc=final_proc1,  
        defense=stats1["def"],   # FIX
        clk=stats1["clk"],
        luck=stats1["luck"],
        logic=stats1["logic"],
        weapon_atk=0,
        weapon_type=weapon1_ow.weapon.type if weapon1_ow else None,
        algorithm=bot1.algorithm,
        upgrade_armor_plating=bot1_upgrades["armor"],
        upgrade_overclock_unit=bot1_upgrades["overclock"],
        upgrade_regen_core=bot1_upgrades["regen"],
        upgrade_critical_subroutine=bot1_upgrades["crit"],
        upgrade_energy_recycler=bot1_upgrades["recycler"],
        upgrade_emp_shield=bot1_upgrades["emp"],
    )

    battleB = BattleBot(
        name=bot2.name,
        hp=stats2["hp"],
        energy=stats2["energy"],
        proc=final_proc2,  
        defense=stats2["def"],   # FIX
        clk=stats2["clk"],
        luck=stats2["luck"],
        logic=stats2["logic"],
        weapon_atk=0,
        weapon_type=weapon2_ow.weapon.type if weapon2_ow else None,
        algorithm=bot2.algorithm,
        upgrade_armor_plating=bot2_upgrades["armor"],
        upgrade_overclock_unit=bot2_upgrades["overclock"],
        upgrade_regen_core=bot2_upgrades["regen"],
        upgrade_critical_subroutine=bot2_upgrades["crit"],
        upgrade_energy_recycler=bot2_upgrades["recycler"],
        upgrade_emp_shield=bot2_upgrades["emp"],
    )

    # Run the battle
    result = full_battle(battleA, battleB)
    winner_name = result["winner"]
    log = result["log"]
    is_draw = (winner_name == "draw" or winner_name is None)
    botA_points = result["botA_points"]
    botB_points = result["botB_points"]
    seed = result["seed"]

    # consume one-time upgrades after battle
    if any(bot1_upgrades.values()):
        bot1.upgrade_armor_plating = False
        bot1.upgrade_overclock_unit = False
        bot1.upgrade_regen_core = False
        bot1.upgrade_critical_subroutine = False
        bot1.upgrade_energy_recycler = False
        bot1.upgrade_emp_shield = False

    if any(bot2_upgrades.values()):
        bot2.upgrade_armor_plating = False
        bot2.upgrade_overclock_unit = False
        bot2.upgrade_regen_core = False
        bot2.upgrade_critical_subroutine = False
        bot2.upgrade_energy_recycler = False
        bot2.upgrade_emp_shield = False

    # save bot win or loss (skip if draw)
    if not is_draw:
        if winner_name == bot1.name:
            bot1.botwins += 1
            bot2.botlosses += 1
        else:
            bot2.botwins += 1
            bot1.botlosses += 1

    db.session.commit()

    # Determine results
    if is_draw:
        bot1_result = "draw"
        bot2_result = "draw"
    else:
        bot1_result = "win" if winner_name == bot1.name else "lose"
        bot2_result = "win" if winner_name == bot2.name else "lose"

    # BOT XP SYSTEM
    def bot_xp_to_next_level(level):
        return 50 + (level - 1) * 25

    def add_bot_xp(bot, amount):
        bot.xp = int(bot.xp or 0)
        bot.level = int(bot.level or 1)
        bot.stat_points = int(bot.stat_points or 0)

        bot.xp += int(amount)
        levels_gained = 0

        while bot.xp >= bot_xp_to_next_level(bot.level):
            bot.xp -= bot_xp_to_next_level(bot.level)
            bot.level += 1
            levels_gained += 1

            bot.stat_points += 5

        return levels_gained

    # Calculate XP per bot
    def calculate_bot_xp(battle_bot, result):
        if result == "win":
            return 20
        elif result == "lose":
            return 5
        elif result == "draw":
            return 10 
        return 0

    # Apply XP
    bot1_xp = calculate_bot_xp(battleA, bot1_result)
    bot2_xp = calculate_bot_xp(battleB, bot2_result)

    if bot1.user_id == user.id:
        add_bot_xp(bot1, bot1_xp)

    elif bot2.user_id == user.id:
        add_bot_xp(bot2, bot2_xp)

    db.session.commit()


     # USER XP
    xp_gained = 0
    levels_gained = 0

  # Determine winning bot
    winning_bot = None
    losing_bot = None

    if winner_name == bot1.name:
        winning_bot = bot1
        losing_bot = bot2
    elif winner_name == bot2.name:
        winning_bot = bot2
        losing_bot = bot1

    if winning_bot and winning_bot.user_id == user.id:
        xp_gained = 30
        levels_gained = add_xp(user, xp_gained)

        user.tokens = int(user.tokens or 0) + 5

        db.session.commit()

    elif losing_bot and losing_bot.user_id == user.id:
        xp_gained = 10
        levels_gained = add_xp(user, xp_gained)

        db.session.commit()
        flash(f"Congratulations {user.username}! You gained {xp_gained} XP and {levels_gained} levels.", "success")

    # elo rating changes
    is_ranked = (bot1.user_id != bot2.user_id)
    
    if is_ranked and not is_draw:
        if winner_name == bot1.name:
            winner_user = bot1.user
            loser_user = bot2.user
        else:
            winner_user = bot2.user
            loser_user = bot1.user
        
        rating_gain, rating_loss = calculate_elo_change(
            winner_user.rating,
            loser_user.rating
        )
        
        old_winner_rating = winner_user.rating
        old_loser_rating = loser_user.rating
        
        winner_user.rating += rating_gain
        winner_user.wins += 1
        
        loser_user.rating += rating_loss
        loser_user.losses += 1
        
        db.session.commit()
        
        flash(
            f"🏆 {winner_user.username} won! Rating: {old_winner_rating} → {winner_user.rating} (+{rating_gain})",
            "success"
        )
        flash(
            f"💔 {loser_user.username} lost. Rating: {old_loser_rating} → {loser_user.rating} ({rating_loss})",
            "info"
        )

    # Add weapon info to stats dictionaries for template
    stats1_base["weapon_atk"] = weapon1_atk
    stats1_base["weapon_name"] = weapon1_ow.weapon.name if weapon1_ow else None
    stats1_base["weapon_type"] = weapon1_ow.weapon.type if weapon1_ow else None
    stats1_base["proc"] = final_proc1 
    stats1["upgrades"] = [
        label for label, enabled in [
            ("Armor Plating", bot1_upgrades["armor"]),
            ("Overclock Unit", bot1_upgrades["overclock"]),
            ("Regen Core", bot1_upgrades["regen"]),
            ("Critical Subroutine", bot1_upgrades["crit"]),
            ("Energy Recycler", bot1_upgrades["recycler"]),
            ("EMP Shield", bot1_upgrades["emp"]),
        ] if enabled
    ]
    
    stats2_base["weapon_atk"] = weapon2_atk
    stats2_base["weapon_name"] = weapon2_ow.weapon.name if weapon2_ow else None
    stats2_base["weapon_type"] = weapon2_ow.weapon.type if weapon2_ow else None
    stats2_base["proc"] = final_proc2  
    stats2["upgrades"] = [
        label for label, enabled in [
            ("Armor Plating", bot2_upgrades["armor"]),
            ("Overclock Unit", bot2_upgrades["overclock"]),
            ("Regen Core", bot2_upgrades["regen"]),
            ("Critical Subroutine", bot2_upgrades["crit"]),
            ("Energy Recycler", bot2_upgrades["recycler"]),
            ("EMP Shield", bot2_upgrades["emp"]),
        ] if enabled
    ]

    
    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        user1_id=bot1.user_id,
        user2_id=bot2.user_id,
        bot1_name=bot1.name,
        bot2_name=bot2.name,
        winner=winner_name,
        seed=seed,

        bot1_hp=stats1_base["hp"],
        bot1_energy=stats1_base["energy"],
        bot1_proc=final_proc1,
        bot1_defense=stats1_base["def"],   
        bot1_clk=stats1_base["clk"],
        bot1_luck=stats1_base["luck"],
        bot1_logic=stats1_base["logic"],
        bot1_weapon_atk=weapon1_atk,
        bot1_weapon_name=(weapon1_ow.weapon.name if weapon1_ow else None),
        bot1_weapon_type=(weapon1_ow.weapon.type if weapon1_ow else None),
        bot1_algorithm=bot1.algorithm,
        bot1_upgrade_armor_plating=bot1_upgrades["armor"],
        bot1_upgrade_overclock_unit=bot1_upgrades["overclock"],
        bot1_upgrade_regen_core=bot1_upgrades["regen"],
        bot1_upgrade_critical_subroutine=bot1_upgrades["crit"],
        bot1_upgrade_energy_recycler=bot1_upgrades["recycler"],
        bot1_upgrade_emp_shield=bot1_upgrades["emp"],

        bot2_hp=stats2_base["hp"],
        bot2_energy=stats2_base["energy"],
        bot2_proc=final_proc2,
        bot2_defense=stats2_base["def"],   #use def 
        bot2_clk=stats2_base["clk"],
        bot2_luck=stats2_base["luck"],
        bot2_logic=stats2_base["logic"],
        bot2_weapon_atk=weapon2_atk,
        bot2_weapon_name=(weapon2_ow.weapon.name if weapon2_ow else None),
        bot2_weapon_type=(weapon2_ow.weapon.type if weapon2_ow else None),
        bot2_algorithm=bot2.algorithm,
        bot2_upgrade_armor_plating=bot2_upgrades["armor"],
        bot2_upgrade_overclock_unit=bot2_upgrades["overclock"],
        bot2_upgrade_regen_core=bot2_upgrades["regen"],
        bot2_upgrade_critical_subroutine=bot2_upgrades["crit"],
        bot2_upgrade_energy_recycler=bot2_upgrades["recycler"],
        bot2_upgrade_emp_shield=bot2_upgrades["emp"],
    )
    db.session.add(history)

    db.session.commit()


    stats1_display = apply_upgrade_arena_effects(stats1_base, bot1_upgrades)
    stats2_display = apply_upgrade_arena_effects(stats2_base, bot2_upgrades)
    stats1_display["weapon_atk"] = stats1_base["weapon_atk"]
    stats1_display["weapon_name"] = stats1_base["weapon_name"]
    stats1_display["weapon_type"] = stats1_base["weapon_type"]
    stats1_display["proc"] = stats1_base["proc"]
    stats1_display["upgrades"] = stats1["upgrades"]
    stats2_display["weapon_atk"] = stats2_base["weapon_atk"]
    stats2_display["weapon_name"] = stats2_base["weapon_name"]
    stats2_display["weapon_type"] = stats2_base["weapon_type"]
    stats2_display["proc"] = stats2_base["proc"]
    stats2_display["upgrades"] = stats2["upgrades"]

    return render_template(
    "combat_log.html",
    bot1=bot1,
    bot2=bot2,
    stats1=stats1_display,
    stats2=stats2_display,
    log=log,
    winner=winner_name,
    xp_gained=xp_gained,
    levels_gained=levels_gained,
    seed=seed,
    new_level=user.level if levels_gained else None,
    is_replay = False
)

@app.route("/battle", methods=["GET", "POST"])
@login_required
def battle_select():
    user = User.query.get(session["user_id"])
    
    if request.method == "POST":
        bot1_id = request.form.get("bot1")
        bot2_id = request.form.get("bot2")
        
        bot1 = Bot.query.get(bot1_id)
        bot2 = Bot.query.get(bot2_id)
        
        if not bot1 or not bot2:
            flash("Invalid bot selection!", "danger")
            return redirect(url_for("battle_select"))

        if bot1_id == bot2_id:
            flash("You must choose two different bots!", "warning")
            return redirect(url_for("battle_select"))
        
        if bot1.user_id != user.id:
            flash("You can only battle with your own bots!", "danger")
            return redirect(url_for("battle_select"))
        
        if bot2.user_id == user.id:
            flash("Please select an opponent's bot!", "warning")
            return redirect(url_for("battle_select"))
        
        return redirect(url_for('combat_log', bot1_id=bot1_id, bot2_id=bot2_id))
    

    my_bots = user.bots
    my_rating = user.rating
    
    # Find suitable opponents (within ±200 rating)
    min_rating = my_rating - 200
    max_rating = my_rating + 200
    
    opponent_users = User.query.filter(
        User.id != user.id,
        User.rating >= min_rating,
        User.rating <= max_rating
    ).order_by(User.rating.desc()).limit(10).all()
    
   
    matched_bots = []
    for opponent in opponent_users:
        for bot in opponent.bots:
            matched_bots.append(bot)
    
    opponent_data = []
    for bot in matched_bots:
        
        weapon_type = "None"
        if bot.weapon:
            weapon_type = bot.weapon.type  

        total_battles = bot.botwins + bot.botlosses
        win_rate = (bot.botwins / total_battles * 100) if total_battles > 0 else 0
        
        opponent_data.append({
            'id': bot.id,
            'name': bot.name,
            'level': bot.level,
            'algorithm': bot.algorithm,
            'owner': User.query.get(bot.user_id).username,
            'wins': bot.botwins,
            'losses': bot.botlosses,
            'total_battles': total_battles,
            'win_rate': round(win_rate, 1),
            'weapon_type': weapon_type
        })
    
    return render_template(
        "battle.html",
        my_bots=my_bots,
        matched_bots=matched_bots,
        my_rating=my_rating,
        opponent_data=opponent_data
    )

def apply_algorithm(bot):
    equipped = WeaponOwnership.query.filter_by(bot_id=bot.id, equipped=True).first()
    weapon_atk = equipped.effective_atk() if equipped else 0

    base_stats = {
        "hp": bot.hp,
        "energy": bot.energy,
        "proc": bot.atk,
        "def": bot.defense,
        "clk": bot.speed,
        "luck": bot.luck,
        "logic": bot.logic or 0,
    }

    algo = bot.algorithm

    effects = algorithm_effects.get(algo, {}).copy()

    # Apply multipliers
    final_stats = {
        "hp": int(base_stats["hp"] * effects.get("hp", 1.0)),
        "energy": int(base_stats["energy"] * effects.get("energy", 1.0)),
        "proc": int(base_stats["proc"] * effects.get("proc", 1.0)),
        "def": int(base_stats["def"] * effects.get("def", 1.0)),
        "clk": int(base_stats["clk"] * effects.get("clk", 1.0)),
        "luck": int(base_stats["luck"] * effects.get("luck", 1.0)),
        "logic": int(base_stats["logic"] * effects.get("logic", 1.0)),
    }

    return final_stats

@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    
    battles = History.query.filter(
        or_(
            History.user1_id == user_id,
            History.user2_id == user_id
        )
    ).order_by(History.timestamp.desc()).all()
    
    return render_template("history.html", battles=battles)

@app.route("/history/<int:history_id>")
@login_required
def view_history(history_id):
    user_id = session["user_id"]
    history = History.query.get_or_404(history_id)
    
    if history.user1_id != user_id and history.user2_id != user_id:
        flash("You don't have permission to view this battle.", "danger")
        return redirect(url_for("history"))
    
    stats1 = {
        "hp": history.bot1_hp,
        "energy": history.bot1_energy,
        "proc": history.bot1_proc,
        "def": history.bot1_defense,  
        "clk": history.bot1_clk,
        "luck": history.bot1_luck,
        "logic": history.bot1_logic or 0,
        "weapon_atk": history.bot1_weapon_atk if history.bot1_weapon_atk else 0,
        "weapon_name": history.bot1_weapon_name,
        "weapon_type": history.bot1_weapon_type,
        "upgrades": [
            label for label, enabled in [
                ("Armor Plating", history.bot1_upgrade_armor_plating),
                ("Overclock Unit", history.bot1_upgrade_overclock_unit),
                ("Regen Core", history.bot1_upgrade_regen_core),
                ("Critical Subroutine", history.bot1_upgrade_critical_subroutine),
                ("Energy Recycler", history.bot1_upgrade_energy_recycler),
                ("EMP Shield", history.bot1_upgrade_emp_shield),
            ] if enabled
        ]
    }
    
    stats2 = {
        "hp": history.bot2_hp,
        "energy": history.bot2_energy,
        "proc": history.bot2_proc,
        "def": history.bot2_defense,   
        "clk": history.bot2_clk,
        "luck": history.bot2_luck,
        "logic": history.bot2_logic or 0,
        "weapon_atk": history.bot2_weapon_atk if history.bot2_weapon_atk else 0,
        "weapon_name": history.bot2_weapon_name,
        "weapon_type": history.bot2_weapon_type,
        "upgrades": [
            label for label, enabled in [
                ("Armor Plating", history.bot2_upgrade_armor_plating),
                ("Overclock Unit", history.bot2_upgrade_overclock_unit),
                ("Regen Core", history.bot2_upgrade_regen_core),
                ("Critical Subroutine", history.bot2_upgrade_critical_subroutine),
                ("Energy Recycler", history.bot2_upgrade_energy_recycler),
                ("EMP Shield", history.bot2_upgrade_emp_shield),
            ] if enabled
        ]
    }
    
    # Recreate BattleBots with stored stats (including logic for accurate replay)
    battleA = BattleBot(
        name=history.bot1_name,
        hp=history.bot1_hp,
        energy=history.bot1_energy,
        proc=history.bot1_proc,
        defense=history.bot1_defense,
        clk=history.bot1_clk,
        luck=history.bot1_luck,
        logic=stats1["logic"],
        weapon_atk=0,
        weapon_type=history.bot1_weapon_type,
        algorithm=history.bot1_algorithm,
        upgrade_armor_plating=history.bot1_upgrade_armor_plating,
        upgrade_overclock_unit=history.bot1_upgrade_overclock_unit,
        upgrade_regen_core=history.bot1_upgrade_regen_core,
        upgrade_critical_subroutine=history.bot1_upgrade_critical_subroutine,
        upgrade_energy_recycler=history.bot1_upgrade_energy_recycler,
        upgrade_emp_shield=history.bot1_upgrade_emp_shield,
    )

    battleB = BattleBot(
        name=history.bot2_name,
        hp=history.bot2_hp,
        energy=history.bot2_energy,
        proc=history.bot2_proc,
        defense=history.bot2_defense,
        clk=history.bot2_clk,
        luck=history.bot2_luck,
        logic=stats2["logic"],
        weapon_atk=0,
        weapon_type=history.bot2_weapon_type,
        algorithm=history.bot2_algorithm,
        upgrade_armor_plating=history.bot2_upgrade_armor_plating,
        upgrade_overclock_unit=history.bot2_upgrade_overclock_unit,
        upgrade_regen_core=history.bot2_upgrade_regen_core,
        upgrade_critical_subroutine=history.bot2_upgrade_critical_subroutine,
        upgrade_energy_recycler=history.bot2_upgrade_energy_recycler,
        upgrade_emp_shield=history.bot2_upgrade_emp_shield,
    )
    
    result = full_battle(battleA, battleB, history.seed)
    winner = result["winner"]
    log = result["log"]

    upgrades1 = {
        "armor": history.bot1_upgrade_armor_plating,
        "overclock": history.bot1_upgrade_overclock_unit,
        "regen": history.bot1_upgrade_regen_core,
        "crit": history.bot1_upgrade_critical_subroutine,
        "recycler": history.bot1_upgrade_energy_recycler,
        "emp": history.bot1_upgrade_emp_shield,
    }
    upgrades2 = {
        "armor": history.bot2_upgrade_armor_plating,
        "overclock": history.bot2_upgrade_overclock_unit,
        "regen": history.bot2_upgrade_regen_core,
        "crit": history.bot2_upgrade_critical_subroutine,
        "recycler": history.bot2_upgrade_energy_recycler,
        "emp": history.bot2_upgrade_emp_shield,
    }
    stats1_display = apply_upgrade_arena_effects(stats1, upgrades1)
    stats2_display = apply_upgrade_arena_effects(stats2, upgrades2)
    stats1_display["weapon_atk"] = stats1["weapon_atk"]
    stats1_display["weapon_name"] = stats1["weapon_name"]
    stats1_display["weapon_type"] = stats1["weapon_type"]
    stats1_display["proc"] = stats1["proc"]
    stats1_display["upgrades"] = stats1["upgrades"]
    stats2_display["weapon_atk"] = stats2["weapon_atk"]
    stats2_display["weapon_name"] = stats2["weapon_name"]
    stats2_display["weapon_type"] = stats2["weapon_type"]
    stats2_display["proc"] = stats2["proc"]
    stats2_display["upgrades"] = stats2["upgrades"]

    return render_template(
        "combat_log.html",
        log=log,
        winner=winner,
        stats1=stats1_display,
        stats2=stats2_display,
        history=history,
        is_replay=True
    )

@app.route("/weapons")
def weapons_shop():
    weapons = Weapon.query.order_by(Weapon.tier.asc(), Weapon.price.asc(), Weapon.name.asc()).all()
    return render_template("weapons.html", weapons=weapons)

@app.route("/weapon/<int:weapon_id>/level_up", methods=["POST"])
@login_required
def level_up_weapon(weapon_id):
    user = User.query.get(session["user_id"])
    ownership = WeaponOwnership.query.filter_by(user_id=user.id, weapon_id=weapon_id).first()
    if not ownership or not ownership.weapon:
        flash("You do not own this weapon.", "warning")
        return redirect(url_for("store"))

    weapon = ownership.weapon

    if ownership.level < weapon.max_level:
        base_price = int(weapon.price or 0)
        current_level = int(ownership.level or 1)
        level_cost = int(round(base_price * (1 + 0.6 * (current_level - 1))))

        if user.tokens < level_cost:
            flash("Not enough credits to level up this weapon.", "warning")
            if ownership.bot_id:
                return redirect(url_for("gear", bot_id=ownership.bot_id))
            return redirect(url_for("store"))

        user.tokens -= level_cost
        ownership.level += 1
        db.session.commit()
        flash(f"{weapon.name} leveled up! (-{level_cost} tokens)", "success")
    else:
        flash("Weapon already at max level.", "info")

    if ownership.bot_id:
        return redirect(url_for("gear", bot_id=ownership.bot_id))
    return redirect(url_for("store"))

@app.route("/buy_weapon/<int:weapon_id>", methods=["POST"])
@login_required
def buy_weapon(weapon_id):
    user = User.query.get(session["user_id"])
    weapon = Weapon.query.get_or_404(weapon_id)

    existing = WeaponOwnership.query.filter_by(
        user_id=user.id,
        weapon_id=weapon.id
    ).first()
    if existing:
        flash("You already own this weapon.", "warning")
        return redirect(url_for("store"))

    if user.tokens < weapon.price:
        flash("Not enough credits.", "error")
        return redirect(url_for("store"))

    user.tokens -= weapon.price

    ownership = WeaponOwnership(
        user_id=user.id,
        weapon_id=weapon.id
    )

    db.session.add(ownership)
    db.session.commit()

    flash(f"{weapon.name} purchased and added to your inventory!", "success")
    return redirect(url_for("store"))

@app.route('/gear/<int:bot_id>', methods=['GET', 'POST'])
@login_required
def gear(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    user_id = bot.user_id 
    owned_weapons = WeaponOwnership.query.filter_by(user_id=user_id).all()
    user = User.query.get(session["user_id"])
    user_tokens = int(user.tokens or 0) if user else 0

    if request.method == "POST":
        if "equip_weapon" in request.form:
            ownership_id = request.form.get("equip_weapon")

            # Unequip any currently equipped weapon for this bot
            WeaponOwnership.query.filter_by(
                bot_id=bot.id,
                equipped=True
            ).update({"equipped": False, "bot_id": None})

            if ownership_id:
                ownership = WeaponOwnership.query.get_or_404(int(ownership_id))
                ownership.bot_id = bot.id
                ownership.equipped = True

            db.session.commit()
            flash("Weapon equipped successfully!", "success")
            return redirect(url_for("gear", bot_id=bot.id))

        if "weapon_ownership_id" in request.form:
            ow_id = int(request.form.get("weapon_ownership_id"))
            ow = WeaponOwnership.query.get_or_404(ow_id)
            if ow.user_id != user.id:
                flash("You do not own this weapon.", "warning")
                return redirect(url_for("gear", bot_id=bot.id))

            if ow.level >= ow.weapon.max_level:
                flash("Weapon already at max level.", "warning")
                return redirect(url_for("gear", bot_id=bot.id))

            base_price = int(ow.weapon.price or 0)
            current_level = int(ow.level or 1)
            level_cost = int(round(base_price * (1 + 0.6 * (current_level - 1))))

            user = User.query.get(session["user_id"])
            if not user or int(user.tokens or 0) < level_cost:
                flash("Not enough credits to level up this weapon.", "warning")
                return redirect(url_for("gear", bot_id=bot.id))

            user.tokens = int(user.tokens or 0) - level_cost
            ow.level += 1
            db.session.commit()
            flash(f"{ow.weapon.name} leveled up! (-{level_cost} tokens)", "success")

            return redirect(url_for("gear", bot_id=bot.id))


    return render_template(
        "gear.html",
        bot=bot,
        owned_weapons=owned_weapons,
        user_tokens=user_tokens
    )

@app.route("/leaderboard")
@login_required
def leaderboard():
    # Get top 50 players by rating
    top_players = User.query.filter(
        User.wins + User.losses > 0  # Only players who have battled
    ).order_by(User.rating.desc()).limit(50).all()
    
    # Get current user's rank if logged in
    current_user_rank = None
    user_has_matches = False
    nearby_players = []
    show_nearby = False
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        user_has_matches = (user.wins + user.losses) > 0
        if user_has_matches:
            higher_rated = (User.query.filter(or_(User.wins > 0, User.losses > 0),User.rating > user.rating).count())
            current_user_rank = higher_rated + 1

    # Only show nearby players if user is NOT in top 50
    if current_user_rank is not None and current_user_rank > 50:
        show_nearby = True
                
        # Get all players with matches, sorted by rating
        all_ranked_players = User.query.filter(
            User.wins + User.losses > 0
        ).order_by(User.rating.desc()).all()
                
        # Find user's position in the list
        user_index = None
        for i, player in enumerate(all_ranked_players):
            if player.id == user.id:
                user_index = i
                break
                
        if user_index is not None:
            # Get 5 players above and 5 below
            start_index = max(0, user_index - 5)
            end_index = min(len(all_ranked_players), user_index + 6)
                    
            nearby_players = all_ranked_players[start_index:end_index]
                    
            # Calculate the starting rank number for nearby players
            nearby_start_rank = start_index + 1
    
    return render_template(
        "leaderboard.html",
        top_players=top_players,
        current_user_rank=current_user_rank,
        user_has_matches = user_has_matches,
        nearby_players=nearby_players,
        show_nearby=show_nearby,
        nearby_start_rank=nearby_start_rank if show_nearby else None
    )

#xp system


def xp_to_next_level(level):
    return 100 + (level - 1) * 50  # progressive leveling

def add_xp(user, amount):
    """
    Adds XP to a user and handles leveling.
    Returns number of levels gained.
    """
    user.xp += amount
    levels_gained = 0

    while user.xp >= xp_to_next_level(user.level):
        user.xp -= xp_to_next_level(user.level)
        user.level += 1
        levels_gained += 1

        # Rewards per level
        user.tokens = int(user.tokens or 0) + 20 

    db.session.commit()
    return levels_gained 

@app.route("/database")
@login_required
def database():
    return render_template("database.html")

#Database Pages
@app.route("/database/getting-started")
def database_getting_started():
    return render_template("database_pages/getting_started.html", active_database="getting_started")

@app.route("/database/combat")
def database_combat():
    return render_template("database_pages/combat.html", active_database="combat")

@app.route("/database/algorithms")
def database_algorithms():
    return render_template("database_pages/algorithms.html", active_database="algorithms")

@app.route("/database/weapons")
def database_weapons():
    return render_template("database_pages/weapons.html", active_database="weapons")

@app.route("/database/upgrades")
def database_upgrades():
    return render_template("database_pages/upgrades.html", active_database="upgrades")

@app.route("/database/stats")
def database_stats():
    return render_template("database_pages/stats.html", active_database="stats")

@app.route("/database/leaderboard")
def database_rating_system():
    return render_template("database_pages/rating_system.html", active_database="rating_system")

@app.route("/database/arenas")
def database_arenas():
    return render_template("database_pages/arenas.html", active_database="arenas")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001, use_reloader=False)

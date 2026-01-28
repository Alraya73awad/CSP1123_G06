import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from sqlalchemy import or_
from functools import wraps
from sqlalchemy import or_

from extensions import db
from constants import CURRENCY_NAME,CHARACTER_ITEMS, algorithms, algorithm_effects, algorithm_descriptions, XP_TABLE, PASSIVE_ITEMS, UPGRADES
from battle import BattleBot, full_battle, calculate_bot_stat_points
from seed_weapons import seed_weapons


from models import User, Bot, History, HistoryLog, Weapon, WeaponOwnership

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

with app.app_context():
    db.create_all()
    seed_weapons()


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
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))  
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = User.query.get(session["user_id"])

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
            "ent": int(bot.luck or 0),
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
            "ent": bot.luck,
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

    weapons = Weapon.query.all()

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

    stat_points = int(getattr(selected_bot, "stat_points", 0) or 0) if selected_bot else 0

    xp_to_next = XP_TABLE.get(user.level, {"to_next": 50})["to_next"]

    return render_template(
        "character.html",
        user=user,
        bots=bots,
        selected_bot=selected_bot,
        stat_points=stat_points,
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
    
    # Determine rank tier
    def get_rank_tier(rating):
        if rating < 800:
            return {"name": "Prototype", "icon": "🔧", "color": "text-secondary"}
        elif rating < 1000:
            return {"name": "Circuit", "icon": "⚡", "color": "text-success"}
        elif rating < 1200:
            return {"name": "Processor", "icon": "🖥️", "color": "text-info"}
        elif rating < 1400:
            return {"name": "Mainframe", "icon": "💻", "color": "text-primary"}
        elif rating < 1600:
            return {"name": "Quantum", "icon": "🌌", "color": "text-warning"}
        else:
            return {"name": "Nexus", "icon": "🔮", "color": "text-danger"}
    
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

    # Ensure bot stat_points exists
    bot.stat_points = int(bot.stat_points or 0)

    # Check points (BOT points, not USER points)
    if bot.stat_points < int(item["cost"]):
        flash("Not enough stat points!", "danger")
        return redirect(url_for("character", bot_id=bot.id))

    # Deduct points from this bot
    bot.stat_points -= int(item["cost"])

    # Apply upgrade to the bot
    stat = item.get("stat")
    value = int(item.get("value", 0))

    if stat in ["hp", "atk", "defense", "speed", "logic", "luck", "energy"]:
        setattr(bot, stat, int(getattr(bot, stat) or 0) + value)

    db.session.commit()
    flash(f"{item['name']} purchased for {bot.name}!", "success")
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

@app.route("/delete_bot/<int:bot_id>", methods=["POST"])
@login_required
def delete_bot(bot_id):
    bot = Bot.query.filter_by(
        id=bot_id,
        user_id=session["user_id"]
    ).first_or_404()

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

    if request.method == 'POST':

        def read_stat(name):
            raw_num = request.form.get(f"{name}_number", "").strip()
            raw_slider = request.form.get(name, "").strip()

            
            chosen = raw_num if raw_num != "" else raw_slider

            # If still empty, fallback to existing bot value
            if chosen == "" or chosen is None:
                return getattr(bot, name)
            try:
                return int(chosen)
            except ValueError:
                return None 

        # Gather values
        new_stats = {}
        for stat in STAT_LIMITS.keys():
            new_stats[stat] = read_stat(stat)

        if "preview" in request.form:
            # validate types and ranges
            errors = []
            for stat, val in new_stats.items():
                if val is None:
                    errors.append(f"{stat.upper()} must be an integer.")
                    continue
                low, high = STAT_LIMITS[stat]
                if val < low or val > high:
                    errors.append(f"{stat.upper()} must be between {low} and {high}.")

            if errors:
                for e in errors:
                    flash(e, "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id) + "?flash=1")

            return render_template('preview_bot.html', bot=bot, new_stats=new_stats)

        if "confirm" in request.form:
            new_name = request.form.get("name", "").strip()
            new_algorithm = request.form.get("algorithm", "").strip()


            if not new_name:
                flash("Bot name cannot be empty.", "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id))

            if not new_algorithm:
                flash("Please select an algorithm.", "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id))


            final_stats = {}
            errors = []
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
                final_stats[stat] = val

            if errors:
                for e in errors:
                    flash(e, "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id) + "?flash=1")
            
            # Read new name + algorithm
            new_name = request.form.get("name", "").strip()
            new_algorithm = request.form.get("algorithm", "").strip()

            # Prevent empty name / algorithm
            if not new_name:
                flash("Bot name cannot be empty.", "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id) + "?flash=1")

            if not new_algorithm:
                flash("Please select an algorithm.", "danger")
                return redirect(url_for('edit_bot', bot_id=bot_id) + "?flash=1")

            changed = (
                bot.name != new_name or
                bot.algorithm != new_algorithm or
                bot.hp != final_stats['hp'] or
                bot.energy != final_stats['energy'] or
                bot.atk != final_stats['atk'] or
                bot.defense != final_stats['defense'] or
                bot.speed != final_stats['speed'] or
                bot.logic != final_stats['logic'] or
                bot.luck != final_stats['luck'] 
            )

            if not changed:
                flash("No changes were made.", "warning")
                return redirect(url_for('bot_list', bot_id=bot_id) + "?flash=1")
            
            bot.name = new_name
            bot.algorithm = new_algorithm
            
            bot.hp = final_stats['hp']
            bot.energy = final_stats['energy']
            bot.atk = final_stats['atk']
            bot.defense = final_stats['defense']
            bot.speed = final_stats['speed']
            bot.logic = final_stats['logic']
            bot.luck = final_stats['luck']


            db.session.commit()
            flash("Bot updated successfully.", "success")
            return redirect(url_for('manage_bot') + "?flash=1")

    return render_template('edit_bot.html', bot=bot, stat_limits=STAT_LIMITS, algorithms = algorithms, algorithm_descriptions=algorithm_descriptions, show_flashes = False)

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
            "ent": bot.luck,
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

    # Convert to BattleBot
    battleA = BattleBot(
        name=bot1.name,
        hp=stats1["hp"],
        energy=stats1["energy"],
        proc=final_proc1,  
        defense=stats1["def"],   # FIX
        clk=stats1["clk"],
        luck=stats1["luck"],
        weapon_atk=weapon1_atk,
        weapon_type=weapon1_ow.weapon.type if weapon1_ow else None
    )

    battleB = BattleBot(
        name=bot2.name,
        hp=stats2["hp"],
        energy=stats2["energy"],
        proc=final_proc2,  
        defense=stats2["def"],   # FIX
        clk=stats2["clk"],
        luck=stats2["luck"],
        weapon_atk=weapon2_atk,
        weapon_type=weapon2_ow.weapon.type if weapon2_ow else None
    )

    # Run the battle
    result = full_battle(battleA, battleB)
    winner_name = result["winner"]
    log = result["log"]
    botA_points = result["botA_points"]
    botB_points = result["botB_points"]
    seed = result["seed"]

    #save bot win or loss
    if winner_name == bot1.name:
        bot1.botwins += 1
        bot2.botlosses += 1
    else:
        bot2.botwins += 1
        bot1.botlosses += 1

    db.session.commit()

    # Determine results
    bot1_result = "win" if winner_name == bot1.name else "lose"
    bot2_result = "win" if winner_name == bot2.name else "lose"

    # BOT XP SYSTEM
    def bot_xp_to_next_level(level):
        return 50 + (level - 1) * 25

    def add_bot_xp(bot, amount):
        bot.xp = int(bot.xp or 0)
        bot.level = int(bot.level or 1)

        bot.xp += int(amount)
        levels_gained = 0

        while bot.xp >= bot_xp_to_next_level(bot.level):
            bot.xp -= bot_xp_to_next_level(bot.level)
            bot.level += 1
            levels_gained += 1

            bot.hp = int(bot.hp or 0) + 10
            bot.atk = int(bot.atk or 0) + 2
            bot.defense = int(bot.defense or 0) + 2

        return levels_gained

    # Calculate XP per bot
    def calculate_bot_xp(battle_bot, result):
        base = 20 if result == "win" else 10
        return base

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

     # BOT-specific stat points reward (per level gained)
        winning_bot.stat_points = int(winning_bot.stat_points or 0) + (levels_gained * 5)

        db.session.commit()

    elif losing_bot and losing_bot.user_id == user.id:
        xp_gained = 10
        levels_gained = add_xp(user, xp_gained)

    # gives loser smaller points
        losing_bot.stat_points = int(losing_bot.stat_points or 0) + (levels_gained * 2)

        db.session.commit()
        flash(f"Congratulations {user.username}! You gained {xp_gained} XP and {levels_gained} levels.", "success")

    # elo rating changes
    is_ranked = (bot1.user_id != bot2.user_id)
    
    if is_ranked:
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
    stats1["weapon_atk"] = weapon1_atk
    stats1["weapon_type"] = weapon1_ow.weapon.type if weapon1_ow else None
    stats1["proc"] = final_proc1 
    
    stats2["weapon_atk"] = weapon2_atk
    stats2["weapon_type"] = weapon2_ow.weapon.type if weapon2_ow else None
    stats2["proc"] = final_proc2  

    
    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        user1_id=bot1.user_id,
        user2_id=bot2.user_id,
        bot1_name=bot1.name,
        bot2_name=bot2.name,
        winner=winner_name,
        seed=seed,

        bot1_hp=stats1["hp"],
        bot1_energy=stats1["energy"],
        bot1_proc=final_proc1,
        bot1_defense=stats1["def"],   
        bot1_clk=stats1["clk"],
        bot1_luck=stats1["luck"],
        bot1_weapon_atk=weapon1_atk,
        bot1_weapon_type=(weapon1_ow.weapon.type if weapon1_ow else None),

        bot2_hp=stats2["hp"],
        bot2_energy=stats2["energy"],
        bot2_proc=final_proc2,
        bot2_defense=stats2["def"],   #use def 
        bot2_clk=stats2["clk"],
        bot2_luck=stats2["luck"],
        bot2_weapon_atk=weapon2_atk,
        bot2_weapon_type=(weapon2_ow.weapon.type if weapon2_ow else None),
    )
    db.session.add(history)
    db.session.flush()

    for type, text in log:
        entry = HistoryLog(history_id=history.id, type=type, text=text)
        db.session.add(entry)

    db.session.commit()


    return render_template(
    "combat_log.html",
    bot1=bot1,
    bot2=bot2,
    stats1=stats1,
    stats2=stats2,
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
    effects = algorithm_effects.get(bot.algorithm, {})
    equipped = WeaponOwnership.query.filter_by(bot_id=bot.id, equipped=True).first()
    weapon_atk = equipped.effective_atk() if equipped else 0

    # Return new effective stats
    return {
        "hp": int(bot.hp * effects.get("hp", 1.0)),
        "energy": int(bot.energy * effects.get("energy", 1.0)),
        "proc": int(bot.atk * effects.get("proc", 1.0)),
        "def": int(bot.defense * effects.get("def", 1.0)),   # FIX: key + multiplier key
        "clk": int(bot.speed * effects.get("clk", 1.0)),
        "luck": int(bot.luck * effects.get("luck", 1.0)),
    }

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
        "weapon_atk": history.bot1_weapon_atk if history.bot1_weapon_atk else 0,
        "weapon_type": history.bot1_weapon_type
    }
    
    stats2 = {
        "hp": history.bot2_hp,
        "energy": history.bot2_energy,
        "proc": history.bot2_proc,
        "def": history.bot2_defense,   
        "clk": history.bot2_clk,
        "luck": history.bot2_luck,
        "weapon_atk": history.bot2_weapon_atk if history.bot2_weapon_atk else 0,
        "weapon_type": history.bot2_weapon_type
    }
    
    # Recreate BattleBots
    battleA = BattleBot(
        name=history.bot1_name,
        hp=history.bot1_hp,
        energy=history.bot1_energy,
        proc=history.bot1_proc,
        defense=history.bot1_defense,
        clk=history.bot1_clk,
        luck=history.bot1_luck,
        weapon_atk=history.bot1_weapon_atk,
        weapon_type=history.bot1_weapon_type
    )

    battleB = BattleBot(
        name=history.bot2_name,
        hp=history.bot2_hp,
        energy=history.bot2_energy,
        proc=history.bot2_proc,
        defense=history.bot2_defense,
        clk=history.bot2_clk,
        luck=history.bot2_luck,
        weapon_atk=history.bot2_weapon_atk,
        weapon_type=history.bot2_weapon_type
    )
    
    result = full_battle(battleA, battleB, history.seed)
    winner = result["winner"]
    log = result["log"]

    return render_template(
        "combat_log.html",
        log=log,
        winner=winner,
        stats1=stats1,
        stats2=stats2,
        history=history,
        is_replay=True
    )

@app.route("/weapons")
def weapons_shop():
    weapons = Weapon.query.all()
    return render_template("weapons.html", weapons=weapons)

@app.route("/weapon/<int:weapon_id>/level_up", methods=["POST"])
def level_up_weapon(weapon_id):
    weapon = Weapon.query.get_or_404(weapon_id)

    if weapon.level < weapon.max_level:
        weapon.level += 1
        db.session.commit()

    return redirect(url_for("edit_bot", bot_id=weapon.bot_id))

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
def gear(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    user_id = bot.user_id 
    owned_weapons = WeaponOwnership.query.filter_by(user_id=user_id).all()

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

            if ow.weapon.level < ow.weapon.max_level:
                ow.weapon.level += 1
                db.session.commit()
                flash(f"{ow.weapon.name} leveled up!", "success")
            else:
                flash("Weapon already at max level.", "warning")

            return redirect(url_for("gear", bot_id=bot.id))


    return render_template(
        "gear.html",
        bot=bot,
        owned_weapons=owned_weapons
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
    if current_user_rank > 50:
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001, use_reloader=False) 



import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps
from extensions import db
from constants import CURRENCY_NAME, STORE_ITEMS, CHARACTER_ITEMS, algorithms, algorithm_effects, algorithm_descriptions, XP_TABLE
from battle import BattleBot, full_battle, calculate_bot_stat_points

from models import User, Bot, History, HistoryLog

app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clash_of_code.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

#routes
@app.route("/")
def home():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])

    return render_template("index.html", username=user.username if user else None)

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Username does not exist.", "danger")
            return redirect(url_for("login"))

        if not check_password_hash(user.password, password):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        flash("Successfully logged in!", "success")
        return redirect(url_for("dashboard"))

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


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user = User.query.get(session["user_id"])

    # HANDLE BOT CREATION
    if request.method == "POST":
        name = request.form.get("name")
        algorithm = request.form.get("algorithm")

        if not name or not algorithm:
            flash("Please enter a bot name and select an algorithm.", "danger")
        else:
            new_bot = Bot(
                name=name,
                algorithm=algorithm,
                user_id=user.id
            )
            db.session.add(new_bot)
            db.session.commit()
            flash("Bot created successfully!", "success")

        return redirect(url_for("dashboard"))

    # XP calculation from XP_TABLE
    level_info = XP_TABLE.get(user.level, {"to_next": 100, "total": 0})
    xp_to_next = level_info["to_next"]
    xp_percent = int((user.xp / xp_to_next) * 100) if xp_to_next > 0 else 0

    # Include stat points
    stat_points = user.stat_points if hasattr(user, "stat_points") else 0

    # Bots enhanced stats
    enhanced_bots = []
    for bot in user.bots:
        base_stats = {
            "int": bot.hp,
            "proc": bot.atk,
            "def": bot.defense,
            "clk": bot.speed,
            "logic": bot.logic,
            "ent": bot.luck,
            "pwr": bot.energy
        }
        effects = algorithm_effects.get(bot.algorithm, {})
        final_stats = {stat: int(base * effects.get(stat, 1.0)) for stat, base in base_stats.items()}
        enhanced_bots.append({"bot": bot, "final_stats": final_stats})

    return render_template(
        "dashboard.html",
        user=user,
        tokens=user.tokens,
        xp_percent=xp_percent,
        xp_to_next=xp_to_next,
        stat_points=stat_points,
        bots=enhanced_bots,
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions,
        currency=CURRENCY_NAME
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

        new_bot = Bot(
            name=name,
            algorithm=algorithm,
            user_id=session["user_id"]
        )

        db.session.add(new_bot)
        db.session.commit()

        flash("Bot created successfully!", "success")
        return redirect(url_for("dashboard"))

    # GET request → show form
    return render_template(
        "create_bot.html",
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions
    )

# Stat Min/Max Values
STAT_LIMITS = {
    "hp": (100, 999),
    "energy": (100, 999),
    "atk": (10, 999),
    "defense": (10, 999),
    "speed": (10, 999),
    "logic": (10, 999),
    "luck": (10, 999)
}


# manage bot
@app.route('/manage_bot')
def manage_bot():
    if 'user_id' not in session:
        flash("Please log in to manage your bots.", "warning")
        return redirect(url_for('login'))

    user_bots = Bot.query.filter_by(user_id=session['user_id']).all()
    return render_template('manage_bot.html', bots=user_bots)

# Other pages
@app.route('/store')
@login_required
def store():
    user = User.query.get(session['user_id'])
    bots = Bot.query.filter_by(user_id=user.id).all()
    credits = user.tokens
    return render_template(
        "store.html",
        store_items=STORE_ITEMS,
        bots=bots,
        credits=credits,
        currency=CURRENCY_NAME
    )

from constants import XP_TABLE

@app.route("/character")
def character():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))

    bots = Bot.query.filter_by(user_id=user.id).all() or []

    xp_to_next = XP_TABLE.get(user.level, {"to_next": 100}).get("to_next", 100)
    current_xp = user.xp or 0

    return render_template(
        "character.html",
        user=user,
        bots=bots,
        stat_points=user.stat_points or 0,
        current_xp=current_xp,
        xp_to_next=xp_to_next,
        CHARACTER_ITEMS=CHARACTER_ITEMS,
    )



def level_up(user):
    XP_TABLE = {
        1: 50,
        2: 200,
        3: 450,
        4: 800,
        5: 1250,
        6: 2000  # etc.
    }

    while user.level in XP_TABLE and user.xp >= XP_TABLE[user.level]:
        user.xp -= XP_TABLE[user.level]       # subtract XP needed for current level
        user.level += 1                        # level up
        user.stat_points += 5                  # award stat points per level
        print(f"{user.username} reached level {user.level}! +5 stat points.")

    db.session.commit()



@app.route('/play')
@login_required
def play():
    return render_template('battle.html')

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

    return render_template(
        'profile.html',
        username=user.username,
        email=user.email,
        level=user.level,
        xp=user.xp,
        tokens=user.tokens
    )



@app.route("/buy", methods=["POST"])
@login_required
def buy():
    user = User.query.get(session["user_id"])

    bot_id = request.form.get("bot_id")
    bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
    if not bot:
        flash("Invalid bot.", "danger")
        return redirect(url_for("store"))

    purchase_id = request.form.get("purchase_id")
    item = next((i for i in STORE_ITEMS if str(i["id"]) == str(purchase_id)), None)
    if not item:
        flash("Invalid item.", "danger")
        return redirect(url_for("store"))

    cost = item["cost"]
    if user.tokens < cost:
        flash("Not enough tokens.", "danger")
        return redirect(url_for("store"))

    user.tokens -= cost
    bot.weapon_type = item.get("type", None)
    bot.weapon_atk = item.get("atk", 0)

    db.session.commit()

    flash(f"{item['name']} purchased!", "success")
    return redirect(url_for("dashboard"))


from constants import CHARACTER_ITEMS

@app.route("/buy_character", methods=["POST"])
@login_required
def buy_character():
    user = User.query.get(session.get("user_id"))
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))

    # Ensure stat_points is always an integer
    stat_points = getattr(user, "stat_points", 0) or 0

    # Validate bot_id
    bot_id = request.form.get("bot_id")
    if not bot_id or not bot_id.isdigit():
        flash("Invalid character selection.", "danger")
        return redirect(url_for("character"))
    bot_id = int(bot_id)

    bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
    if not bot:
        flash("Character not found.", "danger")
        return redirect(url_for("character"))

    # Validate purchase_id
    purchase_id = request.form.get("purchase_id")
    if not purchase_id or not purchase_id.isdigit():
        flash("No upgrade selected.", "danger")
        return redirect(url_for("character"))
    purchase_id = int(purchase_id)

    # Find the upgrade item
    item = next((i for i in CHARACTER_ITEMS if i["id"] == purchase_id), None)
    if not item:
        flash("Invalid upgrade selected.", "danger")
        return redirect(url_for("character"))

    # Check if user has enough stat points
    if stat_points < item["cost"]:
        flash("Not enough stat points!", "danger")
        return redirect(url_for("character"))

    # Deduct points and commit
    user.stat_points -= item["cost"]
    db.session.commit()

    flash(f"{item['name']} purchased for {bot.name}!", "success")
    return redirect(url_for("character"))


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

            # prefer numeric input if user typed something (not empty)
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
                return redirect(url_for('manage_bot') + "?flash=1")
            
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
        "proc": bot.atk,
        "def": bot.defense,
        "clk": bot.speed,
        "logic": bot.logic,
        "ent": bot.luck,
        "pwr": bot.energy
    }

    # lookup effects; default empty dict for algorithms with no static buffs
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

    # Create BattleBot instances
    battleA = BattleBot(
        name=bot1.name,
        hp=stats1["hp"],
        energy=stats1["energy"],
        proc=stats1["proc"],
        defense=stats1["defense"],
        clk=stats1["clk"],
        luck=stats1["luck"]
    )

    battleB = BattleBot(
        name=bot2.name,
        hp=stats2["hp"],
        energy=stats2["energy"],
        proc=stats2["proc"],
        defense=stats2["defense"],
        clk=stats2["clk"],
        luck=stats2["luck"]
    )

    # Run the battle
    result = full_battle(battleA, battleB)
    winner_name = result["winner"]
    log = result["log"]
    botA_points = result["botA_points"]
    botB_points = result["botB_points"]


    # Determine results
    bot1_result = "win" if winner_name == bot1.name else "lose"
    bot2_result = "win" if winner_name == bot2.name else "lose"

    # BOT XP SYSTEM
    def bot_xp_to_next_level(level):
        return 50 + (level - 1) * 25

    def add_bot_xp(bot, amount):
        bot.xp = bot.xp or 0
        bot.level = bot.level or 1
        bot.xp += amount
        while bot.xp >= bot_xp_to_next_level(bot.level):
            bot.xp -= bot_xp_to_next_level(bot.level)
            bot.level += 1
            
            # Optional stat growth
            bot.hp = (bot.hp or 0) + 10
            bot.atk = (bot.atk or 0) + 2
            bot.defense = (bot.defense or 0) + 2
    
        db.session.commit()

    # Calculate XP per bot
    def calculate_bot_xp(battle_bot, result):
        base = 20 if result == "win" else 10
        return base

    # Apply XP
    bot1_xp = calculate_bot_xp(battleA, bot1_result)
    bot2_xp = calculate_bot_xp(battleB, bot2_result)

    add_bot_xp(bot1, bot1_xp)
    add_bot_xp(bot2, bot2_xp)


    # USER XP
    xp_gained = 0
    levels_gained = 0

    winning_bot = None

    # Determine winning bot
    if winner_name == bot1.name:
        winning_bot = bot1
    elif winner_name == bot2.name:
        winning_bot = bot2

    # if user owns the winning bot
    if winning_bot and winning_bot.user_id == user.id:
        xp_gained = 30
        levels_gained = add_xp(user, xp_gained)
        user.tokens += 5

        db.session.commit()

    #user lost

    elif not winning_bot:
        pass
    else:
        xp_gained = 10
        levels_gained = add_xp(user, xp_gained)
        db.session.commit()

        flash(f"Congratulations {user.username}! You gained {xp_gained} XP and {levels_gained} levels.", "success")

    # Save battle history
    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        bot1_name=bot1.name,
        bot2_name=bot2.name,
        winner=winner_name
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
        new_level=user.level if xp_gained else None
    )

    # Save history
    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        bot1_name=bot1.name,
        bot2_name=bot2.name,
        winner=winner_name
    )
    db.session.add(history)
    db.session.flush()

    for log_type, text in log:
        db.session.add(
            HistoryLog(history_id=history.id, type=log_type, text=text)
        )

    db.session.commit()

    return render_template(
        "combat_log.html",
        log=log,
        winner=winner_name,
        bot1=bot1,
        bot2=bot2,
        stats1=stats1,
        stats2=stats2,
        xp_gained=xp_gained,
        levels_gained=levels_gained,
        new_level=user.level if levels_gained else None
    )



@app.route("/battle", methods=["GET", "POST"])
def battle_select():
    bots = Bot.query.all()

    if request.method == "POST":
        bot1_id = request.form.get("bot1")
        bot2_id = request.form.get("bot2")

        if bot1_id == bot2_id:
            flash("You must choose two different bots!", "warning") 
        else:
            return redirect(url_for('combat_log', bot1_id=bot1_id, bot2_id=bot2_id))

    return render_template("battle.html", bots=bots)

def apply_algorithm(bot):
    effects = algorithm_effects.get(bot.algorithm, {})

    # Return new effective stats
    return {
        "hp": int(bot.hp * effects.get("hp", 1.0)),
        "energy": int(bot.energy * effects.get("energy", 1.0)),
        "proc": int(bot.atk * effects.get("proc", 1.0)),
        "defense": int(bot.defense * effects.get("def", 1.0)),
        "clk": int(bot.speed * effects.get("clk", 1.0)),
        "luck": int(bot.luck * effects.get("luck", 1.0)),
    }

@app.route("/history")
def history():
    battles = History.query.order_by(History.timestamp.desc()).all()
    return render_template("history.html", battles = battles)

@app.route("/history/<int:history_id>")
def view_history(history_id):
    history = History.query.get_or_404(history_id)
    bot1 = Bot.query.get(history.bot1_id)
    bot2 = Bot.query.get(history.bot2_id)
    stats1 = apply_algorithm(bot1)
    stats2 = apply_algorithm(bot2)
    logs = HistoryLog.query.filter_by(history_id=history.id).all()

    return render_template("combat_log.html", log=[(l.type, l.text) for l in logs], winner = history.winner, bot1 = bot1, bot2 = bot2, stats1 = stats1, stats2 = stats2)

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
        user.tokens += 20
        user.stat_points = int(user.stat_points or 0) + 5  

    db.session.commit()
    return levels_gained


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001) 

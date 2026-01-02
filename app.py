import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps
from extensions import db
from constants import UPGRADES, STORE_ITEMS, PASSIVE_ITEMS
from battle import BattleBot, full_battle

# Models
from models import User, Bot, History, HistoryLog, Weapon, WeaponOwnership

app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clash_of_code.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

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
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#dashboard
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
            new_bot = Bot(
                name=name,
                algorithm=algorithm,
                user_id=user.id
            )
            db.session.add(new_bot)
            db.session.commit()
            flash("Bot created successfully!", "success")

        return redirect(url_for("dashboard"))

    # NORMAL DASHBOARD LOAD (GET)
    bots = user.bots
    xp_percent = int((user.xp / (user.level * 100)) * 100)

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

        enhanced_bots.append({
            "bot": bot,
            "final_stats": final_stats
        })

    return render_template(
        "dashboard.html",
        bots=enhanced_bots,
        xp_percent=xp_percent,
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions
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

#ALGORITHMS
algorithms = {
    "VEX-01": "Aggressive",
    "BASL-09": "Defensive",
    "EQUA-12": "Balanced",
    "ADAPT-X": "Adaptive",
    "RUSH-09": "Speed",
    "CHAOS-RND": "Random"
    }

#ALGORITHM BUFFS/NERFS
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

    }
}

#ALGORITHM DESCRIPTIONS
algorithm_descriptions = {
    "VEX-01": "Vexor Assault Kernel: Built for aggressive attack routines. Prioritizes damage output at the cost of stability. +15% PROC, -10% DEF",
    "BASL-09": "Bastion Logic Framework: Defensive fortress AI that fortifies its shielding subroutines above all else. +20% DEF, -10% CLK",
    "EQUA-12": "Equilibrium Core Matrix: Balanced core algorithm ensuring even system resource allocation. No buffs or nerfs.",
    "ADAPT-X": "Adaptive Pattern  Synthesizer: Self-learning AI that adjusts its combat model mid-battle. +10% LOGIC after 2 turns, +5% ENT, -10% PROC",
    "RUSH-09": "Rapid Unit Synchronization Hub: An advanced AI core utilizing probabilistic threading for extreme combat reflexes. Fast but fragile. +20% CLK, -10% DEF",
    "CHAOS-RND": "Chaotic Execution Driver: Unstable algorithm driven by randomized decision-making. High volatility, unpredictable results. Unstable modifiers each battle"
}


# manage bot
@app.route('/manage_bot')
def manage_bot():
    if 'user_id' not in session:
        flash("Please log in to manage your bots.", "warning")
        return redirect(url_for('login'))

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

        enhanced_bots.append({
            "bot": bot,
            "final_stats": final_stats
        })
    return render_template('manage_bot.html', bots=enhanced_bots,   algorithms=algorithms, algorithm_descriptions=algorithm_descriptions)

# Other pages
@app.route('/store')
@login_required
def store():
    user = User.query.get(session['user_id'])
    bots = Bot.query.filter_by(user_id=user.id).all()
    credits = user.tokens
    weapons = Weapon.query.all()

    return render_template(
        "store.html",
        store_items=STORE_ITEMS,     
        passive_items=PASSIVE_ITEMS, 
        bots=bots,
        credits=credits,
        weapons = weapons
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

    # Deduct credits
    user.tokens -= passive["cost"]

    # Assign passive to bot
    bot.passive_effect = passive["name"]

    db.session.commit()
    flash(f"{bot.name} learned passive: {passive['name']}", "success")
    return redirect(url_for("store"))

@app.route('/character')
def character():
    return render_template('character.html')

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

#store display func

def store():
    for upgrade in UPGRADES:
        print(upgrade["name"], upgrade["cost"])

# Buy item and upgrade purchase function
@app.route("/buy", methods=["POST"])
@login_required
def buy():
    user = User.query.get(session['user_id'])
    bot_id = request.form.get("bot_id")
    bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
    if not bot:
        flash("Invalid bot selection.", "danger")
        return redirect(url_for("store"))

    purchase_id = request.form.get("purchase_id")
    item = next((i for i in STORE_ITEMS if str(i["id"]) == str(purchase_id)), None)
    if not item:
        flash("Invalid purchase.", "danger")
        return redirect(url_for("store"))

    # Determine cost and apply
    cost = item["cost"]
    if user.tokens < cost:
        flash("Not enough tokens!", "danger")
        return redirect(url_for("store"))

    user.tokens -= cost

    if item.get("stat"):
        # Check whether upgrade uses 'value' or 'amount'
        value = item.get("value") or item.get("amount") or 0
        setattr(bot, item["stat"], getattr(bot, item["stat"]) + value)
        flash(f"{item['name']} applied to {bot.name}!", "success")
    else:
        flash(f"{item['name']} purchased for {bot.name}! (custom effect applied)", "success")

    db.session.commit()
    return redirect(url_for("store"))

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
    bot1 = Bot.query.get_or_404(bot1_id)
    bot2 = Bot.query.get_or_404(bot2_id)

    stats1 = apply_algorithm(bot1)
    stats2 = apply_algorithm(bot2)
    weapon1_ow = WeaponOwnership.query.filter_by(bot_id=bot1.id, equipped=True).first()
    weapon2_ow = WeaponOwnership.query.filter_by(bot_id=bot2.id, equipped=True).first()

    # Convert to BattleBot
    battleA = BattleBot(
        name=bot1.name,
        hp=stats1["hp"],
        energy=stats1["energy"],
        proc=bot1.total_proc,
        defense=stats1["defense"],
        clk=stats1["clk"],
        luck=stats1["luck"],
        weapon_atk=weapon1_ow.effective_atk() if weapon1_ow else 0,
        weapon_type=weapon1_ow.weapon.type if weapon1_ow else None
    )

    battleB = BattleBot(
        name=bot2.name,
        hp=stats2["hp"],
        energy=stats2["energy"],
        proc=bot2.total_proc,
        defense=stats2["defense"],
        clk=stats2["clk"],
        luck=stats2["luck"],
        weapon_atk=weapon2_ow.effective_atk() if weapon2_ow else 0,
        weapon_type=weapon2_ow.weapon.type if weapon2_ow else None
    )

    # RUN THE BATTLE
    winner, log = full_battle(battleA, battleB)

    is_ranked = (bot1.user_id != bot2.user_id)
    
    if is_ranked:
        # Determine winner and loser
        if winner == bot1.name:
            winner_user = bot1.user
            loser_user = bot2.user
        else:
            winner_user = bot2.user
            loser_user = bot1.user
        
        # Calculate ELO changes
        rating_gain, rating_loss = calculate_elo_change(
            winner_user.rating,
            loser_user.rating
        )
        
        # Store old ratings for display
        old_winner_rating = winner_user.rating
        old_loser_rating = loser_user.rating
        
        # UPDATE RATINGS
        winner_user.rating += rating_gain
        winner_user.wins += 1
        
        loser_user.rating += rating_loss  # rating_loss is negative
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

    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        bot1_name=bot1.name,
        bot2_name=bot2.name,
        winner=winner
    )
    db.session.add(history)
    db.session.flush()

    # Save combat log lines
    for type, text in log:
        entry = HistoryLog(
            history_id=history.id,
            type=type,
            text=text
        )
        db.session.add(entry)

    db.session.commit()
    
    return render_template(
        "combat_log.html",
        log=log,
        winner=winner,
        bot1=bot1,
        bot2=bot2,
        stats1=stats1,
        stats2=stats2
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
    
    # GET request - prepare matchmaking data
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
    
    # Get all their bots
    matched_bots = []
    for opponent in opponent_users:
        for bot in opponent.bots:
            matched_bots.append(bot)
    
    return render_template(
        "battle.html",
        my_bots=my_bots,
        matched_bots=matched_bots,
        my_rating=my_rating
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


# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

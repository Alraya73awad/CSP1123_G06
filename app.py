import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps
from extensions import db
from constants import UPGRADES, STORE_ITEMS
from battle import BattleBot, full_battle

# Models
from models import User, Bot, History, HistoryLog, Weapon, Admins, Ability

app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clash_of_code.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

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

        # Check if this user's email is in the Admins table
        admin_entry = Admins.query.filter_by(email=user.email).first()
        if admin_entry:
            session["is_admin"] = True
            flash("Logged in as Admin!", "success")
            return redirect(url_for("dashboard"))
        else:
            session["is_admin"] = False
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

@app.route("/character/<int:bot_id>", methods=["GET", "POST"])
@login_required
def character_page(bot_id):
    user = User.query.get(session["user_id"])
    bot = Bot.query.get_or_404(bot_id)

    # Only allow the owner to edit
    if bot.user_id != current_user.id:
        flash("You don't own this bot!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Handle stat upgrades
        bot.hp = int(request.form.get("hp", bot.hp))
        bot.atk = int(request.form.get("atk", bot.atk))
        bot.defense = int(request.form.get("defense", bot.defense))
        bot.speed = int(request.form.get("speed", bot.speed))
        bot.luck = int(request.form.get("luck", bot.luck))
        bot.energy = int(request.form.get("energy", bot.energy))

        # Handle weapon equip
        weapon_id = request.form.get("weapon_id")
        if weapon_id:
            weapon = Weapon.query.get(int(weapon_id))
            if weapon:
                bot.weapon = weapon

        db.session.commit()
        flash("Bot updated successfully!", "success")
        return redirect(url_for("character_page", bot_id=bot.id))

    if user["is_admin"]:
        owned_weapons = Weapon.query.all()
        owned_abilities = Ability.query.all()
    else:
        owned_weapons = user.weapons.all()
        owned_abilities = user.abilities.all()

    return render_template(
        "character_page.html",
        bot=bot,
        owned_weapons=owned_weapons,
        owned_abilities=owned_abilities
    )

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
            "proc": bot.atk,
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


@app.template_filter("getattr")
def getattr_filter(obj, name):
    return getattr(obj, name)



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
        credits=credits
    )



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

    return render_template(
        'profile.html',
        username=user.username,
        email=user.email,
        level=user.level,
        xp=user.xp,
        tokens=user.tokens
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
        return redirect(url_for("armory"))

    purchase_id = request.form.get("purchase_id")
    item = next((i for i in STORE_ITEMS if str(i["id"]) == str(purchase_id)), None)
    if not item:
        flash("Invalid purchase.", "danger")
        return redirect(url_for("amrory"))

    # Determine cost and apply
    cost = item["cost"]
    if user.tokens < cost:
        flash("Not enough tokens!", "danger")
        return redirect(url_for("armory"))

    user.tokens -= cost

    if item.get("stat"):
        # Check whether upgrade uses 'value' or 'amount'
        value = item.get("value") or item.get("amount") or 0
        setattr(bot, item["stat"], getattr(bot, item["stat"]) + value)
        flash(f"{item['name']} applied to {bot.name}!", "success")
    else:
        flash(f"{item['name']} purchased for {bot.name}! (custom effect applied)", "success")

    db.session.commit()
    return redirect(url_for("armroy"))

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
    user_id = session["user_id"]
    bot = Bot.query.filter_by(id=bot_id, user_id=user_id).first_or_404()
    user = User.query.get(user_id)
    is_admin = session.get("is_admin", False)

    if request.method == 'POST':
        xp_cost_per_point = 5

        # --- Single-point upgrade (+/- buttons) ---
        adjust = request.form.get("adjust")
        if adjust:
            stat, change = adjust.split(":")
            change = int(change)
            current_val = getattr(bot, stat)
            min_val, max_val = STAT_LIMITS[stat]

            if not is_admin and change > 0:
                if user.xp < xp_cost_per_point:
                    flash("Not enough XP to upgrade.", "danger")
                    return redirect(url_for("edit_bot", bot_id=bot.id))
                user.xp -= xp_cost_per_point

            new_val = current_val + change
            if min_val <= new_val <= max_val:
                setattr(bot, stat, new_val)
                db.session.commit()
                flash(f"{stat.upper()} updated to {new_val}", "success")
            else:
                flash(f"{stat.upper()} out of range.", "danger")

            return redirect(url_for("edit_bot", bot_id=bot.id))

        # --- Multi-level upgrade ---
        stat = request.form.get("stat")
        levels = request.form.get("levels")
        if stat and levels:
            try:
                levels = int(levels)
            except ValueError:
                flash("Invalid level input.", "danger")
                return redirect(url_for("edit_bot", bot_id=bot.id))

            current_val = getattr(bot, stat)
            min_val, max_val = STAT_LIMITS[stat]

            total_cost = xp_cost_per_point * (levels * (levels + 1) // 2)

            if not is_admin:
                if user.xp < total_cost:
                    flash(f"Not enough XP. Required: {total_cost}, Available: {user.xp}", "danger")
                    return redirect(url_for("edit_bot", bot_id=bot.id))
                user.xp -= total_cost

            new_val = current_val + levels
            if new_val > max_val:
                new_val = max_val

            setattr(bot, stat, new_val)
            db.session.commit()
            flash(f"{stat.upper()} upgraded by {levels} levels (Cost: {total_cost} XP).", "success")
            return redirect(url_for("edit_bot", bot_id=bot.id))

        # --- Weapon equip ---
        weapon_id = request.form.get("weapon_id")
        if weapon_id:
            try:
                wid = int(weapon_id)
                if is_admin or any(w.id == wid for w in user.weapons):
                    bot.weapon_id = wid
            except ValueError:
                flash("Invalid weapon selection.", "danger")

        # --- Ability equip ---
        ability_id = request.form.get("ability_id")
        if ability_id:
            try:
                aid = int(ability_id)
                if is_admin or user.abilities.filter_by(id=aid).first():
                    bot.ability_id = aid

            except ValueError:
                flash("Invalid ability selection.", "danger")

        db.session.commit()
        flash("Bot updated successfully.", "success")
        return redirect(url_for('bot_list'))

    # For GET requests, show all weapons/abilities if admin, else only owned
    owned_weapons = Weapon.query.all() if is_admin else user.weapons.all()
    owned_abilities = Ability.query.all() if is_admin else user.abilities.all()

    return render_template(
        "edit_bot.html",
        bot=bot,
        stat_limits=STAT_LIMITS,
        algorithms=algorithms,
        algorithm_descriptions=algorithm_descriptions,
        owned_weapons=owned_weapons,
        owned_abilities=owned_abilities,
        xp_balance=user.xp,
        is_admin=is_admin
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

@app.route("/bots")
def bot_list():
    user_id = session["user_id"]
    bots = Bot.query.filter_by(user_id=user_id).all()

    items = []
    for bot in bots:
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
        final_stats = {stat: int(value * effects.get(stat, 1.0)) for stat, value in base_stats.items()}
        items.append({"bot": bot, "final_stats": final_stats})

    return render_template("dashboard.html", bots=items, algorithms=algorithms, algorithm_descriptions=algorithm_descriptions)

@app.route("/combat_log/<int:bot1_id>/<int:bot2_id>")
def combat_log(bot1_id, bot2_id):
    bot1 = Bot.query.get_or_404(bot1_id)
    bot2 = Bot.query.get_or_404(bot2_id)

    stats1 = apply_algorithm(bot1)
    stats2 = apply_algorithm(bot2)
    weapon1 = bot1.weapon
    weapon2 = bot2.weapon

    # convert database Bot → BattleBot for combat (with effective stats)
    battleA = BattleBot(
        name=bot1.name,
        hp=stats1["hp"],
        energy=stats1["energy"],
        proc=stats1["proc"],
        defense=stats1["defense"],
        clk=stats1["clk"],
        luck=stats1["luck"],
        weapon_atk=weapon1.effective_atk() if weapon1 else 0,
        weapon_type=weapon1.type if weapon1 else None,
        special_effect=bot1.special_effect.name if bot1.special_effect else None,
        equipped_ability=bot1.ability.name if bot1.ability else None
    )

    battleB = BattleBot(
        name=bot2.name,
        hp=stats2["hp"],
        energy=stats2["energy"],
        proc=stats2["proc"],
        defense=stats2["defense"],
        clk=stats2["clk"],
        luck=stats2["luck"],
        weapon_atk=weapon2.effective_atk() if weapon2 else 0,
        weapon_type=weapon2.type if weapon2 else None,
        special_effect=bot2.special_effect.name if bot2.special_effect else None,
        equipped_ability=bot2.ability.name if bot2.ability else None
    )

    winner, log = full_battle(battleA, battleB)

    # create history entry
    history = History(
        bot1_id=bot1.id,
        bot2_id=bot2.id,
        bot1_name = bot1.name,
        bot2_name = bot2.name,
        winner=winner
    )
    db.session.add(history)
    db.session.flush()  # assigns history.id

    # save combat log lines
    for type, text in log:
        entry = HistoryLog(
            history_id=history.id,
            type=type,
            text=text
        )
        db.session.add(entry)

    db.session.commit()
    return render_template("combat_log.html", log=log, winner=winner, bot1=bot1, bot2=bot2, stats1 = stats1, stats2 = stats2)

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
    weapon = Weapon.query.get(bot.weapon_id) if bot.weapon_id else None
    weapon_bonus = weapon.atk_bonus if weapon else 0

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

@app.route('/gear/<int:bot_id>', methods=['GET', 'POST'])
def gear(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    weapons = Weapon.query.all()

    if request.method == "POST":
        # Equip weapon
        if "equip_weapon" in request.form:
            weapon_id = request.form.get("equip_weapon")
            bot.weapon_id = int(weapon_id) if weapon_id else None
            if bot.weapon_id:
                weapon = Weapon.query.get(bot.weapon_id)
                bot.atk = 10 + weapon.effective_atk()  
            else:
                bot.atk = 10  
            db.session.commit()
            flash("Weapon equipped successfully!", "success")
            return redirect(url_for("gear", bot_id=bot.id))

        # Level up weapon
        if "weapon_id" in request.form:
            weapon_id = int(request.form.get("weapon_id"))
            weapon = Weapon.query.get_or_404(weapon_id)
            if weapon.level < weapon.max_level:
                weapon.level += 1
                db.session.commit()
                flash(f"{weapon.name} leveled up to Lv {weapon.level}!", "success")
            else:
                flash(f"{weapon.name} is already at max level.", "warning")
            return redirect(url_for('gear', bot_id=bot.id))


    return render_template('gear.html', bot=bot, weapons=weapons)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")
@admin_required
def admin_dashboard():
    user = User.query.get(session["user_id"])
    all_users = User.query.all()
    all_bots = Bot.query.all()
    return render_template("admin_dashboard.html", current_user=user, users=all_users, bots=all_bots)


# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

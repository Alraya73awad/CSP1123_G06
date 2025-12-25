import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from functools import wraps
from extensions import db
from constants import UPGRADES, STORE_ITEMS
from battle import BattleBot, full_battle


app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clash_of_code.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

# Create tables
with app.app_context():
    db.create_all()


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


#dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    bots = user.bots if user else []

    return render_template("dashboard.html", user=user, bots=bots)


#logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    bots = Bot.query.filter_by(user_id=user.id).all()

    # XP progress 
    xp_percent = int((user.xp / (user.level * 100)) * 100)

    return render_template(
        'dashboard.html',
        username=user.username,
        level=user.level,
        xp=user.xp,
        tokens=user.tokens,
        xp_percent=xp_percent,
        bots=bots
    )



# Create bot
@app.route('/create_bot', methods=['GET', 'POST'])
def create_bot():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))


    bot_name = request.form['name']
    attack = int(request.form['attack'])
    defense = int(request.form['defense'])
    speed = int(request.form['speed'])

    new_bot = Bot(
        name=bot_name,
        attack=attack,
        defense=defense,
        speed=speed,
        user_id=session['user_id']
    )

    if request.method == 'POST':
        name = request.form.get('name')
        algorithm = request.form["algorithm"]

        new_bot = Bot(name=name, algorithm=algorithm)

        db.session.add(new_bot)
        db.session.commit()

        return redirect(url_for('bot_list'))
    
    

    return render_template('create_bot.html', algorithms = algorithms, algorithm_descriptions=algorithm_descriptions)

# Models
from models import User, Bot, History, HistoryLog

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

    user_bots = Bot.query.filter_by(user_id=session['user_id']).all()
    return render_template('manage_bot.html', bots=user_bots)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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




@app.route("/combat_log/<int:bot1_id>/<int:bot2_id>")
def combat_log(bot1_id, bot2_id):
    bot1 = Bot.query.get_or_404(bot1_id)
    bot2 = Bot.query.get_or_404(bot2_id)

    stats1 = apply_algorithm(bot1)
    stats2 = apply_algorithm(bot2)

    # convert database Bot → BattleBot for combat (with effective stats)
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

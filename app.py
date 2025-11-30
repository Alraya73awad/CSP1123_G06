from flask import Flask, render_template, request, redirect, url_for, flash
<<<<<<< HEAD
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import Bot, User
from flask import session


app = Flask(__name__, instance_relative_config=True)
=======
from flask_sqlalchemy import SQLAlchemy

# Initialize app
app = Flask(__name__)
>>>>>>> main
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'

<<<<<<< HEAD
db.init_app(app)

# HOMEPAGE
=======
# Initialize database
db = SQLAlchemy(app)

# Models
from models import Bot 

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


# Routes
>>>>>>> main
@app.route('/')
def home():
    return render_template('index.html')

<<<<<<< HEAD

# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return redirect(url_for('dashboard', user_id=user.id))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')


# REGISTER PAGE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_bots = Bot.query.filter_by(user_id=session['user_id']).all()

    return render_template('dashboard.html', bots=user_bots)



# OTHER PAGES
@app.route('/manage_bot')
def manage_bot():
    return render_template('manage_bot.html')

@app.route('/game_lobby')
def game_lobby():
    return render_template('game_lobby.html')

@app.route('/store')
def store():
    return render_template('store.html')

@app.route('/character')
def character():
    return render_template('character.html')

@app.route('/play')
def play():
    return render_template('play.html')

@app.route('/battle')
def battle():
    return render_template('battle.html')

#Bot creation
@app.route('/create_bot', methods=['POST'])
def create_bot():
    # make sure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    bot_name = request.form['name']
    attack = request.form['attack']
    defense = request.form['defense']
    speed = request.form['speed']

    new_bot = Bot(
        name=bot_name,
        attack=attack,
        defense=defense,
        speed=speed,
        user_id=session['user_id']       # IMPORTANT
    )

    db.session.add(new_bot)
    db.session.commit()

    return redirect(url_for('dashboard'))



# RUN APP
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5001)


=======
@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/create_bot', methods=['GET', 'POST'])
def create_bot():
    if request.method == 'POST':
        name = request.form.get('name')
        algorithm = request.form["algorithm"]

        new_bot = Bot(name=name, algorithm=algorithm)

        db.session.add(new_bot)
        db.session.commit()

        return redirect(url_for('bot_list'))
    
    

    return render_template('create_bot.html', algorithms = algorithms, algorithm_descriptions=algorithm_descriptions)

@app.route('/bot_list')
def bot_list():
    bots = Bot.query.all()

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

    return render_template('bot_list.html', bots=enhanced_bots)

@app.route('/delete_bot/<int:bot_id>')
def delete_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    db.session.delete(bot)
    db.session.commit()
    return redirect(url_for('bot_list'))

@app.route('/edit-bot/<int:bot_id>', methods=['GET', 'POST'])
def edit_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)

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
            return redirect(url_for('bot_list') + "?flash=1")

    return render_template('edit_bot.html', bot=bot, stat_limits=STAT_LIMITS, algorithms = algorithms, algorithm_descriptions=algorithm_descriptions, show_flashes = False)

@app.route('/bot/<int:bot_id>')
def bot_details(bot_id):
    bot = Bot.query.get_or_404(bot_id)

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


        

# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
>>>>>>> main

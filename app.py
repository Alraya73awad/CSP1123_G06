from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from test import db
from test import app
from battle import BattleBot, full_battle

# Models
from test import Bot 

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
@app.route('/')
def index():
    return render_template('index.html')

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
    app = Flask(__name__)
    app.config['DEBUG'] = True

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
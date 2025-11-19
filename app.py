from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'  # change later for production

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
    
    algorithms = {
    "VEX-01": "Aggressive",
    "BASL-09": "Defensive",
    "EQUA-12": "Balanced",
    "ADAPT-X": "Adaptive",
    "RUSH-09": "Speed",
    "CHAOS-RND": "Random"
    }

    return render_template('create_bot.html', algorithms = algorithms)

@app.route('/bot_list')
def bot_list():
    bots = Bot.query.all()
    return render_template('bot_list.html', bots=bots)

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
                return redirect(url_for('edit_bot', bot_id=bot_id))

            return render_template('preview_bot.html', bot=bot, new_stats=new_stats)

        if "confirm" in request.form:
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
                return redirect(url_for('edit_bot', bot_id=bot_id))

            bot.hp = final_stats['hp']
            bot.energy = final_stats['energy']
            bot.atk = final_stats['atk']
            bot.defense = final_stats['defense']
            bot.speed = final_stats['speed']
            bot.logic = final_stats['logic']
            bot.luck = final_stats['luck']

            db.session.commit()
            flash("Bot updated successfully.", "success")
            return redirect(url_for('bot_list'))

    return render_template('edit_bot.html', bot=bot, stat_limits=STAT_LIMITS)

        

# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Bot
import os
from flask_migrate import Migrate
from constants import UPGRADES
from constants import STORE_ITEMS

from models import User
from flask import session

app = Flask(__name__, instance_relative_config=True)

@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Create tables 
with app.app_context():
    db.create_all()



# homepage
@app.route("/")
def home():
    user_id = session.get("user_id")
    username = None

    if user_id:
        user = User.query.get(user_id)
        if user:
            username = user.username

    return render_template("index.html", username=username)



# login

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


# register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')



# DASHBOARD (User Bots Only)
@app.route('/dashboard')
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
@app.route('/create_bot', methods=['POST'])
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

    db.session.add(new_bot)
    db.session.commit()

    flash("Bot created successfully!", "success")
    return redirect(url_for('dashboard'))


# MANAGE BOT
@app.route('/manage_bot')
def manage_bot():
    if 'user_id' not in session:
        flash("Please log in to manage your bots.", "warning")
        return redirect(url_for('login'))

    user_bots = Bot.query.filter_by(user_id=session['user_id']).all()
    return render_template('manage_bot.html', bots=user_bots)


from functools import wraps

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
    return render_template('play.html')

@app.route('/battle')
def battle():
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

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#BUT ITEM AND UPGRADE PURCHASE FUNC
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





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

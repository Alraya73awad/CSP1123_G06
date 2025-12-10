from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, Bot
import os
from flask_migrate import Migrate

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# TEMP: Create tables 
with app.app_context():
    db.create_all()



# HOME PAGE
@app.route("/")
def home():
    user_id = session.get("user_id")
    username = None

    if user_id:
        user = User.query.get(user_id)
        if user:
            username = user.username

    return render_template("index.html", username=username)



# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        # if User does not exist
        if not user:
            flash("Username does not exist.", "danger")
            return redirect(url_for("login"))

        # if Incorrect password
        if not check_password_hash(user.password, password):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))

        # Success
        session["user_id"] = user.id
        flash("Successfully logged in!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # if Username already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        # if Email already used
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        # Create user
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

    # XP progress (example: level * 100)
    xp_percent = (user.xp % 100)  # or your own formula

    return render_template(
        'dashboard.html',
        username=user.username,
        level=user.level,
        xp=user.xp,
        tokens=user.tokens,
        xp_percent=xp_percent,
        bots=bots
    )



# CREATE BOT
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


# OTHER PAGES
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



# PROFILE PAGE
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

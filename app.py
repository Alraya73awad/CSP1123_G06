from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import Bot, User
from flask import session


app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'

db.init_app(app)

# HOMEPAGE
@app.route('/')
def home():
    return render_template('index.html')


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



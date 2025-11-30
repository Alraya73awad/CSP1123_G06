from flask import Flask, render_template, request, redirect, url_for, flash, session

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'  # change later for production
# Development helpers
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Import models and initialize DB (models.py defines `db`)
from models import db, User
db.init_app(app)


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required.', 'warning')
            return redirect(url_for('register'))

        # check if username already exists
        with app.app_context():
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('Username already taken.', 'danger')
                return redirect(url_for('register'))

            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

        flash('Registered successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required.', 'warning')
            return redirect(url_for('login'))

        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                flash('Logged in successfully.', 'success')
                return redirect(url_for('index'))

        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


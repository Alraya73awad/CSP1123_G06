from flask import Flask, render_template, request, redirect, url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'  # change later for production

# Initialize database
db = SQLAlchemy(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play')
def play():
    return render_template('play.html')


@app.route('/game')
def game():
    return render_template('game.html')

# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

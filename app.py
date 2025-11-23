from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'  # change later 

# Initialize database
db = SQLAlchemy(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/play')
def play():
    return render_template('play.html')

# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

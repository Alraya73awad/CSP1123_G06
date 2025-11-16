from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Initialize app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_of_code.db'
app.config['SECRET_KEY'] = 'dev_secret_key'  # change later for production

# Initialize database
db = SQLAlchemy(app)

# Models
from models import Bot 

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

    return render_template('create_bot.html')

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

        

# Run server
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

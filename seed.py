from app import app
from models import Admins
from extensions import db

with app.app_context():
    admin = Admins(email="alrayahawad8@gmail.com")
    db.session.add(admin)
    db.session.commit()
    print("Admin email added:", admin.email)

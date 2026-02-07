from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    test_user = User(username="testuser", email="test@example.com", password=generate_password_hash("oldpass"))
    db.session.add(test_user)
    db.session.commit()
    print("Test user created: testuser, test@example.com, oldpass")

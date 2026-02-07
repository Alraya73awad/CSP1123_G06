import requests
from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

# Create test user
with app.app_context():
    db.create_all()
    existing = User.query.filter_by(email='test@example.com').first()
    if not existing:
        test_user = User(username="testuser", email="test@example.com", password=generate_password_hash("oldpass"))
        db.session.add(test_user)
        db.session.commit()
        print("Test user created.")
    else:
        print("Test user already exists.")

# Test the forgot password endpoint
url = 'http://127.0.0.1:5001/forgot_password'
data = {'email': 'test@example.com', 'new_password': 'newpass'}

response = requests.post(url, data=data)
print(f"Response status: {response.status_code}")
print(f"Response text: {response.text}")

# Check if password was updated
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    if user:
        old_check = check_password_hash(user.password, 'oldpass')
        new_check = check_password_hash(user.password, 'newpass')
        print(f"Old password valid: {old_check}")
        print(f"New password valid: {new_check}")
        if new_check:
            print("Password successfully updated in database!")
        else:
            print("Password not updated.")
    else:
        print("User not found.")

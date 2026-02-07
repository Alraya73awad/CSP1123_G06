from werkzeug.security import generate_password_hash
from extensions import db
from models import Admin
from app import app

# Create a new admin
new_admin = Admin(
    username="superadmin",
    email="admin@example.com",
    password=generate_password_hash("YourSecurePassword123"),
    role="superadmin"
)
with app.app_context():
    db.session.add(new_admin)
    db.session.commit()
    print("Admin account created!")
from app import app, db
from models import User

with app.app_context():
    for u in User.query.all():
        if u.stat_points is None:
            u.stat_points = 0
    db.session.commit()
    print("All existing users stat_points fixed!")

from app import app
from extensions import db
from seed_weapons import seed_weapons


def main():
    with app.app_context():
        db.create_all()
        seed_weapons()


if __name__ == "__main__":
    main()

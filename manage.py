from app import app
from flask_migrate import MigrateCommand
from flask.cli import FlaskGroup
from extensions import db

cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
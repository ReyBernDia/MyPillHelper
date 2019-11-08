"""Models and database functions for MyPill project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()



##############################################################################
# Model definitions


class Meds(db.Model):
    """All medications."""

    __tablename__ = "meds"

    med_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    shape = db.Column(db.String(20), nullable=True)
    score = db.Column(db.String(5), nullable=True)
    imprint = db.Column(db.String(25), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    strength = db.Column(db.String(200), nullable=True)
    rxcui = db.Column(db.String(15), nullable=True)
    ndc9 = db.Column(db.String(20), nullable=False)
    medicine_name = db.Column(db.String(64), nullable=True)
    image_label = db.Column(db.String(64), nullable=True)
    has_image = db.Column(db.Boolean, nullable=True)
    img_path = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Medication: {self.medicine_name} RXCUI: {self.rxcui}>"

##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///meds'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print("Connected to DB.")
"""Models and database functions for MyPill project."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, update
from werkzeug.security import generate_password_hash, check_password_hash

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()



##############################################################################
# Model definitions


class Meds(db.Model):
    """All medications from NIH dataset."""

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

    # @classmethod
    # def retreive_medications(self, input_one, input_two ): 
    #     """Perform search queries based on input from find-meds form."""
    #     search = Meds.query.filter((Meds.imprint.like('%'+search_by_+'%'))).all()
    #     return search

class Users(db.Model):
    """Registered users."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    f_name = db.Column(db.String(25), nullable=False)
    l_name = db.Column(db.String(25), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    cell_number = db.Column(db.String(10), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Name: {self.f_name} {self.l_name} Cell: {self.cell_number}>"

class User_meds(db.Model):
    """User medications."""

    __tablename__ = "u_meds"

    user_med_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    med_id = db.Column(db.Integer, db.ForeignKey('meds.med_id'), nullable=False)
    qty_per_dose = db.Column(db.Integer, nullable=False)
    times_per_day = db.Column(db.Integer, nullable=False)
    rx_duration = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    refills = db.Column(db.Integer, nullable=False)
    rx_start_date = db.Column(db.DateTime, nullable=False)
    start_dose = db.Column(db.Integer, nullable=True)
    end_dose = db.Column(db.Integer, nullable=True)
    alternation = db.Column(db.Integer, nullable=True)
    brand_name = db.Column(db.String(64), nullable=True)
    indications = db.Column(db.String(2000), nullable=True)
    dose_admin = db.Column(db.String(2000), nullable=True)
    more_info = db.Column(db.String(2000), nullable=True)
    contraindications = db.Column(db.String(2000), nullable=True)

    #Define relationship to meds.
    med = db.relationship("Meds", 
                          backref=db.backref("u_meds"))

    #Define relationship to users. 
    user = db.relationship("Users", 
                           backref=db.backref("u_meds"))

    def __repr__(self):
        return f"<Med ID: {self.user_med_id} Med Name: {self.brand_name}>"



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
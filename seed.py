"""Utility file to seed image database from MovieLens data in seed_data/"""

from sqlalchemy import func
# from model import User
# from model import Rating
# from model import Movie

from model import connect_to_db, db
from server import app
from datetime import datetime

#EXAMPLE DATA PULL FROM SEED DATA.
# def load_users():
#     """Load users from u.user into database."""

#     print("Users")

#     # Delete all rows in table, so if we need to run this a second time,
#     # we won't be trying to add duplicate users
#     User.query.delete()

#     # Read u.user file and insert data
#     for row in open("seed_data/u.user"):
#         row = row.rstrip()
#         user_id, age, gender, occupation, zipcode = row.split("|")

#         user = User(user_id=user_id,
#                     age=age,
#                     zipcode=zipcode)

#         # We need to add to the session or it won't ever be stored
#         db.session.add(user)

#     # Once we're done, we should commit our work
#     db.session.commit()



if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    #ALL FUNCTIONS ABOVE GO BELOW LIKE SO:
    # load_users()
    # load_movies()
    # load_ratings()
    # set_val_user_id()
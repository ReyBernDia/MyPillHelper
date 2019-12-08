"""Utility file to seed image database from MovieLens data in seed_data/"""

from sqlalchemy import func

from test_model import Meds, Users, User_meds

from test_model import connect_to_db, db
from server import app
from datetime import datetime
import csv


def load_pill_data():
    """Seed database with pillbox data. """

    Meds.query.delete()

    with open('pill_testing_book.csv') as csvfile:
        csv_reader = csv.reader(csvfile)
        line_count = 0

        for row in csv_reader:
            if line_count == 0: 
                line_count += 1 
            else: 
                shape = (row[9]).upper()
                score = (row[11]).upper()
                imprint = (row[13]).upper()
                color = (row[16]).upper()
                strength = (row[18]).upper()
                rxcui = row[24]
                ndc9 = row[29]
                medicine_name = (row[32]).capitalize()
                image_label = row[45]
                has_image = row[46]
                if has_image == 'TRUE':
                    has_image = True 
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573171910/Test_pill_files/"
                                + image_label + ".jpg")
                else: 
                    has_image = False
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573708367/production_images/No_Image_Available.jpg")

                medication = Meds(shape=shape,
                                  score=score,
                                  imprint=imprint,
                                  color=color,
                                  strength=strength,
                                  rxcui=rxcui,
                                  ndc9=ndc9,
                                  medicine_name=medicine_name,
                                  image_label=image_label,
                                  has_image=has_image, 
                                  img_path=img_path)
                
                db.session.add(medication)

                line_count += 1
        db.session.commit()

if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_pill_data()
    
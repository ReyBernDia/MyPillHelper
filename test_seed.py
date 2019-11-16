"""Utility file to seed image database from MovieLens data in seed_data/"""

from sqlalchemy import func

from test_model import Meds, Users, User_meds

from test_model import connect_to_db, db
from server import app
from datetime import datetime
import csv


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


def load_pill_data():
    """Seed database with pillbox data. """

    Meds.query.delete()

    # '/home/vagrant/src/hb_pillproject/pill_testing_book.csv'

    with open('pill_testing_book.csv') as csvfile:
        csv_reader = csv.reader(csvfile)
        line_count = 0
    # print(csv_reader)
        for row in csv_reader:
            # print(row)
            if line_count == 0: 

                print(f'This is the first row.')
                print('#############')
                line_count += 1 
            else: 
                print('THIS IS NOT THE FIRST ROW')
                print('#############')
                shape = (row[9]).upper()
                print(f'{shape} = shape',type(shape))

                score = (row[11]).upper()
                print(f'{score} = score', type(score))

                imprint = (row[13]).upper()
                print(f'{imprint} = imprint', type(imprint))

                color = (row[16]).upper()
                print(f'{color} = color', type(color))

                strength = (row[18]).upper()
                print(f'{strength} = strength', type(strength))
                print(len(strength))

                rxcui = row[24]
                print(f'{rxcui} = rxcui', type(rxcui))

                ndc9 = row[29]
                print(f'{ndc9} = ndc9', type(ndc9))

                medicine_name = (row[32]).capitalize()
                print(f'{medicine_name} = medicine_name',type(medicine_name))
                print(len(medicine_name))

                image_label = row[45]
                print(f'{image_label} = image_label', type(image_label))

                has_image = row[46]
                if has_image == 'TRUE':
                    has_image = True 
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573171910/Test_pill_files/"
                                + image_label + ".jpg")

                else: 
                    has_image = False
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573708367/production_images/No_Image_Available.jpg")

                print(f'{has_image} = does this have an image',type(has_image))
                print(f'{img_path} ##IMAGE PAGE IS THIS##', type(img_path))

                #shape= row['splshape']


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
                print(medication)

                db.session.add(medication)

                # print(f'\t{row[32]} has been created with an rxcui of {row[24]}.')
                
                line_count += 1
        # print(f'Processed {line_count} lines.')
        db.session.commit()



if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_pill_data()
    
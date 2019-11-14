"""Utility file to seed image database from MovieLens data in seed_data/"""

from sqlalchemy import func

from model import Meds

from model import connect_to_db, db
from server import app
from datetime import datetime
import csv



def load_pill_data():
    """Seed database with pillbox data. """

    Meds.query.delete()

    # '/home/vagrant/src/hb_pillproject/pill_testing_book.csv'

    with open('Pillbox_production.csv') as csvfile:
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
                shape = row[9]
                print(f'{shape} = shape',type(shape))

                score = row[11]
                print(f'{score} = score', type(score))

                imprint = row[13]
                print(f'{imprint} = imprint', type(imprint))

                color = row[16]
                print(f'{color} = color', type(color))

                strength = row[18]
                print(f'{strength} = strength', type(strength))
                print(len(strength))

                rxcui = row[24]
                print(f'{rxcui} = rxcui', type(rxcui))

                ndc9 = row[29]
                print(f'{ndc9} = ndc9', type(ndc9))

                medicine_name = row[32]
                print(f'{medicine_name} = medicine_name',type(medicine_name))
                print(len(medicine_name))

                image_label = row[45]
                print(f'{image_label} = image_label', type(image_label))

                has_image = row[46]
                if has_image == 'TRUE':
                    has_image = True 
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573537498/production_images/"
                                + image_label + ".jpg")

                else: 
                    has_image = False
                    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573593090/production_images/No_Image_Available.jpg")

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
    
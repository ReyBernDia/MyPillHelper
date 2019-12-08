from model import connect_to_db, db, Meds, Users, User_meds
import api

def query_with_find_meds_values(form_imprint, score, shape, color, name):
        """Get each value from the form in find_medications.html and query the DB."""

        imprint = (form_imprint.split(" "))[0] #incase user populates scentence. 
        #set conditionals for various search query options based on input. 
        #imprint and color contain ; separated values in db. 
        query = Meds.query
        if (imprint != ""):
            query = (query.filter((Meds.imprint.like('%'+imprint+'%')))
            .order_by(Meds.has_image.desc()))
        if (score.upper() != "UNKNOWN"):
            query = (query.filter((Meds.score == score))
            .order_by(Meds.has_image.desc()))
        if (shape.upper() != "UNKNOWN"):
            query = (query.filter((Meds.shape == shape))
            .order_by(Meds.has_image.desc()))
        if (color.upper() != "UNKNOWN"):
            query = (query.filter((Meds.color.like('%'+color+'%')))
            .order_by(Meds.has_image.desc()))
        if (name != ""):
            query = (query.filter((Meds.medicine_name.like('%'+name+'%')))
            .order_by(Meds.has_image.desc()))
        query.all()

        return query

def make_dictionary_from_query(query_results):
        """Make a dictionary from query search result.

        This function should take in any amount of input from the form on 
        find_medications.html and return search results from the database. 
        The goal is to avoid displaying multiple options for the same medication 
        strengths and duplicate images to the user. There are multiple duplicates of 
        both in the database. 
        For example::

            >>> query_results = [<Med: Ramipril, Strength: 1.25mg >,
                               <Med: Ramipril, Strength: 1.25mg >, 
                               <Med: Ramipril, Strenght: 2.5mg >]

        The search results are to be passed to jinja in a dictionary to display 
        unique results of medication name, strength, and possible image. 

            >>> med_options = {'Ramipril 1.25mg': ['https...img1.jpg', 'https...img2.jpg'],
                               'Ramipril 2.5mg': ['https...img3.jpg']}

        Will need to pass on the name of the medication along with the dictionary. 
        """

        query_dictionary = {}  #dictionary to pass to jinja
        for med in query_results:
            name = med.medicine_name  #pass on common medication name to jinja
            key = med.strength  
            img_path = med.img_path  
            if key not in query_dictionary:
                query_dictionary[key] = [name, [img_path]] 
            else: 
                #get the list from values 
                #then append
                #create a value for the inner list. 
                query_dictionary[key].append(img_path)
        return query_dictionary

def make_dictionary_for_user_meds(query_results):
    """Make a dictionary for user medications."""

    query_dictionary = {}
    for med in query_results:

        key = med.med.medicine_name  
        strength = med.med.strength
        img_path = med.med.img_path 
        indications = med.indications
        dose_admin = med.dose_admin
        pharm_class = med.pharm_class
        contraindications = med.contraindications
        more_info = med.more_info
        med_id = med.med_id

        if key not in query_dictionary:
                query_dictionary[key] = {"strength":[strength],
                                         "img_path": [img_path],
                                         "indications":indications,
                                         "dose_admin": dose_admin,
                                         "pharm_class": pharm_class,
                                         "contraindications": contraindications,
                                         "more_info": more_info,
                                         "med_id": med_id} 
        else:  
            query_dictionary[key]["img_path"].append(img_path)
            query_dictionary[key]["strength"].append(strength)

    return query_dictionary


def add_user_med_to_database(api_results, med_id, user_id, qty_per_dose, 
                             times_per_day, rx_start_date):
    """Given user/med info process adding a new user medication to the database."""


    #pull all info needed to instantiate a new med from api_results.
    brand_name = api_results["brand_name"]
    indications = api_results["indications"]
    dosing_info = api_results["dosing_info"]
    info_for_patients = api_results["info_for_patients"]
    contraindications = api_results["contraindications"]
    pharm_class = api_results["pharm_class"]
   
    #truncate length to place in database. 
    if (len(indications) != 0) and (len(indications)>2000):
        indications = (indications[0:1997]+"...")
    
    if (len(dosing_info) != 0) and (len(dosing_info)>2000):
        dosing_info = (dosing_info[0:1997]+"...")

    if (len(info_for_patients) != 0) and (len(info_for_patients)>2000):
        info_for_patients = (info_for_patients[0:1997]+"...")

    if (len(contraindications) != 0) and (len(contraindications)>2000):
        contraindications = (contraindications[0:1997]+"...")

    if (len(brand_name) != 0) and (len(brand_name)>64):
        brand_name = (brand_name[0:62]+"...")

    if (len(pharm_class) != 0) and (len(pharm_class)>64):
        pharm_class = (pharm_class[0:62]+"...")

    new_user_med = User_meds(user_id=user_id,
                        med_id=med_id,
                        text_remind=False,
                        qty_per_dose=qty_per_dose,
                        times_per_day=times_per_day,
                        rx_start_date=rx_start_date,
                        brand_name=brand_name,
                        indications=indications,
                        dose_admin=dosing_info,
                        more_info=info_for_patients,
                        contraindications=contraindications,
                        pharm_class=pharm_class)
    db.session.add(new_user_med)
    db.session.commit()

def instantiate_new_medication(strength, med_name):
    """Instantiate new medication into the Meds table."""

    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1574898450/production_images/No_Image_Available.jpg")    

    new_med = Meds(strength=strength,
                   medicine_name=(med_name.capitalize()),
                   has_image=False, 
                   img_path=img_path)
    db.session.add(new_med)
    db.session.commit()

def add_unverified_med(user_id, med_id, qty_per_dose, times_per_day, rx_start_date):
    """Add user medication that does not exist in DB Meds or in FDA API."""

    new_user_med = User_meds(user_id=user_id,
                        med_id=med_id,
                        text_remind=False,
                        qty_per_dose=qty_per_dose,
                        times_per_day=times_per_day,
                        rx_start_date=rx_start_date)
    db.session.add(new_user_med)
    db.session.commit()


def make_object_dictionary(med_obj):
    """Make dictionary from medication object."""

    med_obj_dict = {}

    med_obj_dict['name'] = med_obj.brand_name
    med_obj_dict['indications'] = med_obj.indications
    med_obj_dict['dose_admin'] = med_obj.dose_admin
    med_obj_dict['more_info'] = med_obj.more_info
    med_obj_dict['contraindications'] = med_obj.contraindications
    med_obj_dict['pharm_class'] = med_obj.pharm_class

    return med_obj_dict



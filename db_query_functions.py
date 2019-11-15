from model import connect_to_db, db, Meds, Users, User_meds

def query_with_find_meds_values(form_imprint, score, shape, color):
        """Get each value from the form in find_medications.html and query the DB."""

        imprint = (form_imprint.split(" "))[0] #incase user populates scentence. 
      
        # print('IMPRINT:' ,imprint, type(imprint), len(imprint))
        # print('SCORE:' ,score, score.upper())
        # print('SHAPE:' ,shape, shape.upper())
        # print('COLOR:' ,color, color.upper())

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
        print("###############")
        print(query_dictionary)
        return query_dictionary









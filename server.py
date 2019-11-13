from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Meds

from sqlalchemy import asc, update

import os
from sys import argv
from pprint import pprint
import json
import requests


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined

@app.route("/")
def display_homepage():
    """Render homepage."""

    return render_template("homepage.html")

@app.route("/find_meds")
def display_medication_search_bar():
    """Display the medication search form."""

    return render_template("find_medications.html")
   

@app.route("/results")
def display_medication_search_results():
    """Display the options for medication search results.
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
    
    def query_with_form_values():
        """Get each value from the form in find_medications.html and query the DB."""

        form_imprint = (request.args.get('pill_imprint')).upper()
        imprint = (form_imprint.split(" "))[0] #incase user populates scentence. 
        score = request.args.get('pill_score')
        shape = (request.args.get('pill_shape')).upper() #in DB as all caps.
        color = (request.args.get('pill_color')).upper() #in DB as all caps.

        print('IMPRINT:' ,imprint, type(imprint), len(imprint))
        print('SCORE:' ,score, score.upper())
        print('SHAPE:' ,shape, shape.upper())
        print('COLOR:' ,color, color.upper())

        #set variables for various user input possibilities. 
        no_input = ((imprint == "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        only_imprint = ((imprint != "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        imprint_and_score = ((imprint != "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        imprint_score_shape = ((imprint != "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        imprint_score_shape_color = ((imprint != "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        imprint_and_shape = ((imprint != "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        only_shape = ((imprint == "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        shape_and_color = ((imprint == "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        only_score = ((imprint == "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))
        
        score_and_shape = ((imprint == "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() == "UNKNOWN"))

        score_shape_color = ((imprint == "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() != "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        only_color = ((imprint == "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        color_and_score = ((imprint == "") and 
                        (score.upper() != "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        color_and_imprint = ((imprint != "") and 
                        (score.upper() == "UNKNOWN") and 
                        (shape.upper() == "UNKNOWN") and 
                        (color.upper() != "UNKNOWN"))

        #set conditionals for various search query options based on input. 
            #imprint and color contain ; separated values in db. 
        if only_imprint:
            query_results = (Meds.query.filter((Meds.imprint.like('%'+imprint+'%')))
                            .order_by(Meds.has_image.desc())
                            .all())

        elif imprint_and_score:
            query_results = (Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                             & (Meds.score == score))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif imprint_score_shape: 
            query_results = (Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                             & (Meds.shape == shape) 
                             & (Meds.score == score))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif imprint_score_shape_color: 
            query_results = (Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                             & (Meds.shape == shape) 
                             & (Meds.score == score) 
                             & (Meds.color.like('%'+color+'%')))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif imprint_and_shape:
            query_results = (Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                             & (Meds.shape == shape))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif only_shape:
            query_results = (Meds.query.filter((Meds.shape == shape))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif shape_and_color:
            query_results = (Meds.query.filter((Meds.shape == shape) 
                             & (Meds.color.like('%'+color+'%')))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif only_score:
            query_results = (Meds.query.filter((Meds.score == score))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif score_and_shape:
            query_results = (Meds.query.filter((Meds.shape == shape) 
                             & (Meds.score == score))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif score_shape_color: 
            query_results = (Meds.query.filter((Meds.shape == shape) 
                             & (Meds.score == score) 
                             & (Meds.color.like('%'+color+'%')))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif only_color:
            query_results = (Meds.query.filter((Meds.color.like('%'+color+'%')))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif color_and_score:
            query_results = (Meds.query.filter((Meds.color.like('%'+color+'%')) 
                             & (Meds.score == score))
                             .order_by(Meds.has_image.desc())
                             .all())

        elif color_and_imprint:
            query_results = (Meds.query.filter((Meds.color.like('%'+color+'%')) 
                             & (Meds.imprint.like('%'+imprint+'%')))
                             .order_by(Meds.has_image.desc())
                             .all())

        else: 
            query_results = []

        return query_results

    def make_dictionary_from_query():
        """Make a dictionary from query search results."""

        query_result_list = query_with_form_values() #get 

        query_dictionary = {}  #dictionary to pass to jinja
        for med in query_result_list:
            name = med.medicine_name  #pass on common medication name to jinja
            key = med.strength  
            img_path = med.img_path  
            if key not in query_dictionary:
                query_dictionary[key] = [name, [img_path]] 
            else: 
                query_dictionary[key].append(img_path)
        # print("###############")
        # print(query_dictionary)
        return query_dictionary

    search_dictionary = make_dictionary_from_query()

    if len(search_dictionary) == 0:  #check if search_dictionary is empty. 
        return render_template("no_search.html")
    else:
        med_options = search_dictionary
        return render_template("results.html", 
                            med_options=med_options) 
                         

@app.route("/more_info/<value>")
def display_more_info(value):
    """Given selected value, query FDA API to display more information on med."""

    # print(value, type(value))
    API_KEY = os.environ['API_KEY']
    # print(API_KEY)

    url = ("https://api.fda.gov/drug/label.json?api_key="
           + API_KEY
           +"&search=openfda.generic_name:" 
           + value)
    # print(url)
    r = requests.get(url)
    med_info = r.json()

    if 'results' in med_info:
        info_dict = (med_info['results'][0])
        openfda_dict = (med_info['results'][0]['openfda'])

        if 'indications_and_usage' in info_dict:
            indications = (med_info['results'][0]['indications_and_usage'])
        else: 
            indications = ""
        if 'dosage_and_administration' in info_dict:
            dosing_info = (med_info['results'][0]['dosage_and_administration'])
        else: 
            dosing_info = ""
        if 'information_for_patients' in info_dict:
            info_for_patients = (med_info['results'][0]['information_for_patients'])
        else: 
            info_for_patients = ""
        if 'contraindications' in info_dict:
            contraindications = (med_info['results'][0]['contraindications'])
        else: 
            contraindications = ""
        if 'brand_name' in openfda_dict:
            brand_name = (med_info['results'][0]['openfda']['brand_name'])
        else: 
            brand_name = value
        if 'pharm_class_moa' in openfda_dict:
            pharm_class = (med_info['results'][0]['openfda']['pharm_class_moa'])
        else: 
            pharm_class = ""
    
    else:
        brand_name = value
        indications = "" 
        dosing_info = ""
        info_for_patients = ""
        contraindications = ""
        pharm_class = ""


    return render_template("more_info.html", indications=indications,
                           dosing_info=dosing_info,
                           info_for_patients=info_for_patients,
                           contraindications=contraindications, 
                           brand_name=brand_name,
                           pharm_class=pharm_class)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
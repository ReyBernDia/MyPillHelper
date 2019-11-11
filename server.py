from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from test_model import connect_to_db, db, Meds

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

        >>> search_results = [<Med: Ramipril, Strength: 1.25mg >,
                           <Med: Ramipril, Strength: 1.25mg >, 
                           <Med: Ramipril, Strenght: 2.5mg >]

    The search results are to be passed to jinja in a dictionary to display 
    unique results of medication name, strength, and possible image. 

        >>> med_options = {'Ramipril 1.25mg': ['https...img1.jpg', 'https...img2.jpg'],
                           'Ramipril 2.5mg': ['https...img3.jpg']}

    Will need to pass on the name of the medication along with the dictionary. 
    """
    
    #get each value from the form in find_medications.html
    imprint = request.args.get('pill_imprint')
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
        search_results = Meds.query.filter((Meds.imprint.like('%'+imprint+'%'))).all()

    elif imprint_and_score:
        search_results = Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                         & (Meds.score == score)).all()

    elif imprint_score_shape: 
        search_results = Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                         & (Meds.shape == shape) 
                         & (Meds.score == score)).all()

    elif imprint_score_shape_color: 
        search_results = Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                         & (Meds.shape == shape) 
                         & (Meds.score == score) 
                         & (Meds.color.like('%'+color+'%'))).all()

    elif imprint_and_shape:
        search_results = Meds.query.filter((Meds.imprint.like('%'+imprint+'%')) 
                         & (Meds.shape == shape)).all()

    elif only_shape:
        search_results = Meds.query.filter((Meds.shape == shape)).all()

    elif shape_and_color:
        search_results = Meds.query.filter((Meds.shape == shape) 
                         & (Meds.color.like('%'+color+'%'))).all()

    elif only_score:
        search_results = Meds.query.filter((Meds.score == score)).all()

    elif score_and_shape:
        search_results = Meds.query.filter((Meds.shape == shape) 
                         & (Meds.score == score)).all()

    elif score_shape_color: 
        search_results = Meds.query.filter((Meds.shape == shape) 
                         & (Meds.score == score) 
                         & (Meds.color.like('%'+color+'%'))).all()

    elif only_color:
        search_results = Meds.query.filter((Meds.color.like('%'+color+'%'))).all()

    elif color_and_score:
        search_results = Meds.query.filter((Meds.color.like('%'+color+'%')) 
                         & (Meds.score == score)).all()

    elif color_and_imprint:
        search_results = Meds.query.filter((Meds.color.like('%'+color+'%')) 
                         & (Meds.imprint.like('%'+imprint+'%'))).all()

    else: 
        search_results = Meds.query.all()

        flash("You need to enter at least one search item.")
        redirect("/find_meds")


    print('#####################')
    print(search_results)
    print('#####################')

    med_options = {}  #dictionary to pass to jinja
    for med in search_results:
        name = med.medicine_name  #pass on common medication name to jinja
        key = med.strength  
        value = med.img_path  
        if key not in med_options:
            med_options[key] = (name, [value]) 
        else: 
            med_options[key].append(value)
        # print("##################")
        # print(value)
        # print("##################")

    print(med_options)
   
    return render_template("results.html", 
                            name = name,
                            med_options=med_options) 
                            
@app.route("/more_info/<value>")
def display_more_info(value):

    print(value, type(value))
    payload = {'openfda.generic_name': value}
    url = ("https://api.fda.gov/drug/label.json?api_key=jjq96yHwsqaeKyCe0Vfvue1wijNdmZJlJkcgYwFy&search=openfda.generic_name:" + value)

    print(url)
    r = requests.get(url)

    med_info = r.json()

    indications = (med_info['results'][0]['indications_and_usage'])
    dosing_info = (med_info['results'][0]['dosage_and_administration'])
    # info_for_patients = (med_info['results'][0]['information_for_patients'])
    # contraindications = (med_info['results'][0]['contraindications'])
    # brand_name = (med_info['results'][0]['openfda']['brand_name'])
    # pharm_class = (med_info['results'][0]['openfda']['pharm_class_moa'])


    return render_template("more_info.html", indications=indications,
                           dosing_info=dosing_info)
                           # info_for_patients=info_for_patients,
                           # contraindications=contraindications, 
                           # brand_name=brand_name,
                           # pharm_class=pharm_class)


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

    
from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from test_model import connect_to_db, db, Meds

from sqlalchemy import asc, update

import os


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
    """Display the options for medication search results."""
    
    #get each value from the form in find_medications.html
    imprint = request.args.get('pill_imprint')
    score = request.args.get('pill_score')
    shape = (request.args.get('pill_shape')).upper()
    color = (request.args.get('pill_color')).upper()

    print('IMPRINT:' ,imprint, type(imprint))
    print('SCORE:' ,score, score.upper())
    print('SHAPE:' ,shape, shape.upper())
    print('COLOR:' ,color, color.upper())

    no_input = ((imprint == "") and 
                    (score.upper() == "UNKNOWN") and 
                    (shape.upper() == "UNKNOWN") and 
                    (color.upper() == "UNKNOWN"))
    only_imprint = ((imprint != "") and 
                    (score.upper() == "UNKNOWN") and 
                    (shape.upper() == "UNKNOWN") and 
                    (color.upper() == "UNKNOWN"))
    imprint_and_score = ((imprint != "") and 
                    (score != "UNKNOWN") and 
                    (shape.upper() == "UNKNOWN") and 
                    (color.upper() == "UNKNOWN"))
    imprint_score_shape = ((imprint != "") and 
                    (score != "UNKNOWN") and 
                    (shape.upper() != "UNKNOWN") and 
                    (color.upper() == "UNKNOWN"))
    imprint_score_shape_color = ((imprint != "") and 
                    (score != "UNKNOWN") and 
                    (shape.upper() != "UNKNOWN") and 
                    (color.upper() != "UNKNOWN"))

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

    print(search_results)

    #############################

    #goal: display med options from search with(med strength & med image) & avoid
    #making multiple options for same strength 
        #make a dictionary of med options to pass to jinja. 
            #in dictionary, key = med strength, value = med image
            #in jinja: check if key has a value, if so, then render image. 
    med_options = {}
    for med in search_results:
        name = med.medicine_name
        key = med.strength
        # print(key)
        value = med.img_path
        if key not in med_options:
            med_options[key] = [value] 
        else: 
            med_options[key].append(value)
        # print("##################")
        # print(value)
        # print("##################")

    # print(med_options)
   

    return render_template("results.html", 
                            name = name,
                            med_options=med_options) 
                            



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

    
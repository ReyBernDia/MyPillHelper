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
    shape = request.args.get('pill_shape')
    color = request.args.get('pill_color')

    print(imprint, score, shape, color)

    #query for searched medication
    searched_med = Meds.query.filter((Meds.imprint.like('%APO%'))).first()
    print(searched_med)

    return render_template("results.html")



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

    
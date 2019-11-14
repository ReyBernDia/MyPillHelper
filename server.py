from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Meds, Users, User_meds

from sqlalchemy import asc, update

from datetime import datetime

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

    API_KEY = os.environ['API_KEY']
    url = ("https://api.fda.gov/drug/label.json?api_key="
           + API_KEY
           +"&search=openfda.generic_name:" 
           + value)
    # print(url)
    r = requests.get(url)
    med_info = r.json()

    results = med_info.get('results', "")

    info_dict = (med_info['results'][0])
    openfda_dict = (med_info['results'][0]['openfda'])

    indications = info_dict.get('indications_and_usage', "")
    dosing_info = info_dict.get('dosage_and_administration', "")
    info_for_patients = info_dict.get('information_for_patients', "")
    contraindications = info_dict.get('contraindications', "")
    brand_name = openfda_dict.get('brand_name', value)
    pharm_class = openfda_dict.get('pharm_class_moa', "")

    return render_template("more_info.html", indications=indications,
                           dosing_info=dosing_info,
                           info_for_patients=info_for_patients,
                           contraindications=contraindications, 
                           brand_name=brand_name,
                           pharm_class=pharm_class)

@app.route('/register', methods=['GET'])
def register_new_user():
    """Display user registration form."""

    return render_template("registration.html")


@app.route('/register', methods=['POST'])
def process_registration():
    """Register new user if email not already in db."""

    f_name = request.form.get('first_name')
    l_name = request.form.get('last_name')
    email = request.form.get('email')
    cell_number = request.form.get('cell')
    password_hash = request.form.get('password')

    # if user cell already exists, ignore
    if Users.query.filter(Users.cell_number == cell_number).first():
        pass
    # if user cell does not exist, add to db
    else: 
        user = Users(f_name=f_name, 
                     l_name=l_name, 
                     email=email, 
                     cell_number=cell_number)
        user.set_password(password_hash)
        db.session.add(user)
        db.session.commit()

    return redirect('/')

@app.route('/login', methods=['GET'])
def display_login_page():

    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login_user():
    """Login user and add them to the session."""

    #query DB using login information. 
    f_name = request.form.get('first_name')
    cell_number= request.form.get('cell')
    password_hash = request.form.get('password')
    user = Users.query.filter((Users.f_name == f_name),
                              (Users.cell_number == cell_number)).first()

    #if we have a search query and the password is correct- add to session. 
    if user and user.check_password(password_hash):
        session['user_name'] = user.f_name
        session['user_id'] = user.user_id
        flash("Successfully logged in!")  # flash- logged in.
        return redirect('/user-page')  #redirect to users page.
    else: 
        flash("That is not a valid email & password.")
        return redirect('/login')   


@app.route('/logout')
def logout_user():
    """Remove user from session."""

    del session['user_name']
    del session['user_id']
    flash("Successfully logged out!")

    return redirect('/')

@app.route('/user-page', methods=['GET'])
def display_user_page():
    """Display specific information about user."""

    user = Users.query.filter(Users.user_id == session['user_id']).first()

    medications = user.u_meds #get medications for user in session. 
    

    return render_template('user_page.html', 
                            user=user, 
                            medications=medications) 
                            
@app.route('/user-page', methods=['POST'])
def process_adding_medications():
    """Add user medications to DB from input on user profile page."""

    #get user to keep them in the session. 
    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name

    med_name = request.form.get('med_name')
    qty_per_dose = int(request.form.get('qty_per_dose'))
    dose_schedule = request.form.get('dosing')

    #convert dosing to time of day to store in DB times_per_day.
    #QAM - 8:00 AM 
    #QPM - 8:00 PM 
    #BID - 8:00 AM/8:00PM 
    #TID - 8:00/12:00/8:00

    rx_duration = int(request.form.get('duration'))
    qty = int(request.form.get('qty'))
    refills = int(request.form.get('refills'))
    start_date = request.form.get('start_date')

    rx_start_date = datetime.strptime(start_date,'%Y-%m-%d')

    print(med_name, type(med_name))
    print(qty_per_dose, type(qty_per_dose))
    print(dose_schedule, type(dose_schedule))
    print(rx_duration, type(rx_duration))
    print(qty, type(qty))
    print(refills, type(refills))
    print(rx_start_date, type(rx_start_date))

    API_KEY = os.environ['API_KEY']
    url = ("https://api.fda.gov/drug/label.json?api_key="
           + API_KEY
           +"&search=openfda.generic_name:" 
           + med_name)
    # print(url)
    r = requests.get(url)
    med_info = r.json()

    results = med_info.get('results', "")

    info_dict = (med_info['results'][0])
    openfda_dict = (med_info['results'][0]['openfda'])

    indications = info_dict.get('indications_and_usage', "")
    dosing_info = info_dict.get('dosage_and_administration', "")
    info_for_patients = info_dict.get('information_for_patients', "")
    contraindications = info_dict.get('contraindications', "")
    brand_name = openfda_dict.get('brand_name', value)
    pharm_class = openfda_dict.get('pharm_class_moa', "")


    flash("Medication Added!")
    return render_template('user_page.html', user=user)


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
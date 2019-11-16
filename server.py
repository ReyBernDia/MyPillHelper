from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Meds, Users, User_meds

from sqlalchemy import asc, update

from datetime import datetime, timedelta

import db_query_functions as db_query
import api

import os
from sys import argv
from pprint import pprint
import json
import requests


app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=31)
# Required to use Flask sessions and the debug toolbar
app.secret_key = "QWEASDZXC"

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

    form_imprint = (request.args.get('pill_imprint')).upper()
    score = request.args.get('pill_score')
    shape = (request.args.get('pill_shape')).upper() #in DB as all caps.
    color = (request.args.get('pill_color')).upper() #in DB as all caps.

    query_results = db_query.query_with_find_meds_values(form_imprint, score, shape, color)

    med_dictionary = db_query.make_dictionary_from_query(query_results)

    if len(med_dictionary) == 0:  #check if med_dictionary is empty. 
        return render_template("no_search.html")
    else:
        return render_template("results.html", 
                            med_options=med_dictionary) 
                         
@app.route("/more_info/<value>")
def display_more_info(value):
    """Given selected value, query FDA API to display more information on med."""

    api_results = api.query_fda_api(value)

    return render_template("more_info.html", 
                           indications=api_results[0],
                           dosing_info=api_results[1],
                           info_for_patients=api_results[2],
                           contraindications=api_results[3], 
                           brand_name=api_results[4],
                           pharm_class=api_results[5])

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
    f_name = request.form.get('first_name') #either lower case or upcase for user input discrepancy. 
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
                            
# @app.route('/user-settings', methods=['POST'])
# def process_user_settings():

#     user = Users.query.filter(Users.user_id == session['user_id']).first()

#     medications = user.u_meds #get medications for user in session. 

#     def access_users():
#         am = request.form.get('AM_time')
#         mid = request.form.get('Mid_time')
#         pm = request.form.get('PM_time')
        
#         am_time = datetime.strptime(am, '%H:%M')
#         mid = datetime.strptime(mid, '%H:%M')
#         pm_time = datetime.strptime(pm, '%H:%M')
        
#         print(am_time, type(am_time))
#         print(mid, type(mid))
#         print(pm_time, type(pm_time))
#         return 

#     flash("Your reminder time has been updated!")
#     return render_template('user_page.html', 
#                             user=user, 
#                             medications=medications) 


@app.route('/user-page', methods=['POST'])
def process_adding_medications():
    """Add user medications to DB from input on user profile page."""

    #get user to keep them in the session. 
    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name
    user_id = session['user_id']

    med_name = (request.form.get('med_name')).upper()
    qty_per_dose = int(request.form.get('qty_per_dose'))
    times_per_day = int(request.form.get('dosing'))
    start_date = request.form.get('start_date')

    rx_start_date = datetime.strptime(start_date,'%Y-%m-%d')

    # print(med_name, type(med_name))
    # print(qty_per_dose, type(qty_per_dose))
    # print(times_per_day, type(times_per_day))
    # print(rx_start_date, type(rx_start_date))

    database_med = (Meds.query.filter(Meds.strength.like('%'+med_name+'%'))
                    .order_by(Meds.has_image.desc())
                    .all())

     #if DB query returns empty then do an API call with name. 
        #render the brand name and generic name, also indications and usage. 
        #user will need to select the medication. 
        #once user selects medication, then add it to DB under meds. 
        #once you add to DB meds- fetch the med_id and instantiate a new user_med instance.

    print("THIS IS THE DB", database_med, len(database_med))

    if len(database_med) == 0: 
        api_results = api.query_fda_api(med_name)
        print("THIS IS THE API", api_results, len(api_results))
        #display this result to the user. 
            #Ask is this your medication? Event listener on click
                #if this is then need to pass this info to DB
            #or No, this is not my medication -> enter in more info. 
                #user fills out form and then store in DB. 
        return render_template('confirm_med_api.html', api_results=api_results)
    else: 
        #display this result to the user. 
            #Ask is this your medication? Event listener on click
                #if this is then need to pass this info to DB
            #or No, this is not my medication -> enter in more info. 
                #user fills out form and then store in DB. 
        return render_template('confirm_med_db.html', database_med=database_med)

    #Ways to pass information to the user and then retrieve all back in a diff route:
        #put all form info into the session, carry it through to the next route
        #delete the info from the session once the medication has been added. 
        #all need to be post requests so the user can't go back


    # new_med = User_meds(user_id=user_id,
    #                     qty_per_dose=qty_per_dose, 
    #                     times_per_day=times_per_day,
    #                     start_date=start_date)

    # flash("Medication Added!")
    # return render_template('user_page.html', user=user)
@app.route("/add_api_med", methods=['POST'])
def add_med_to_databse():

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name

    api_info = request.form.get('api_results')
    print('###########THIS IS BACK IN /ADD_MED##################')
    print(api_info)

    database_med = request.form.get('database_med')
    print('###########THIS IS BACK IN /ADD_MED##################')
    print(database_med)

    ##CONSTRUCT ADD MEDICATION TO DATABASE##

    flash("Medication Added!")
    return render_template('user_page.html', user=user)

@app.route("/add_med_unverified")
def display_add_medication_form():

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name

    ##CONSTRUCT ADD MEDICATION TO DATABASE##

    flash("We added your medication, however, there is no further information regarding your medication at this time.")
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
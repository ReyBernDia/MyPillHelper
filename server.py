from jinja2 import StrictUndefined
from sqlalchemy import asc, update
from flask import Flask, render_template, redirect, request, flash, session, g, make_response, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Meds, Users, User_meds
import db_query_functions as db_helper
import api
from reminders_twilio import * 

from datetime import datetime, timedelta
import os
from sys import argv
from pprint import pprint
import json
import requests
import schedule
import time


app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=1)
# Required to use Flask sessions and the debug toolbar
app.secret_key = "QWEASDZXC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an error.
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
    name = (request.args.get('name_of_med')).capitalize()  

    query_results = db_helper.query_with_find_meds_values(form_imprint, score, shape, color, name)
    med_dictionary = db_helper.make_dictionary_from_query(query_results)

    if len(med_dictionary) == 0:  #check if med_dictionary is empty. 
        return render_template("no_search.html")
    else:
        return render_template("results.html", 
                            med_options=med_dictionary) 
                         
@app.route("/more_info/<value>")
def display_more_info(value):
    """Given selected value, query FDA API to display more information on med."""

    api_results = api.query_fda_api(value)
    return render_template("more_info.html", api_results=api_results)

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
    cell = request.form.get('cell')
    password_hash = request.form.get('password')
    cell_number = cell_verify(cell)  #verify cell number using Twilio API.
    #if cell verify returns error- then number is invalid. 
    if cell_number == False:  #exception made for error to return false. 
            flash("That is not a valid phone number, please try again!")
            return redirect('/register')
    # if user cell already exists, ask user to login. 
    if Users.query.filter(Users.cell_number == cell_number).first():
        flash("That cell number already exists, please login.")
        return redirect('/login')
    else:  # if user cell does not exist, add to db
        user = Users(f_name=f_name,
                     l_name=l_name,
                     email=email,
                     cell_number=cell_number)
        user.set_password(password_hash)
        db.session.add(user)
        db.session.commit()
    #place user in session.
    session['user_name'] = user.f_name
    session['user_id'] = user.user_id
    # flash("Successfully logged in!"). #need to fix formating for flash messages
    return redirect('/user-page')

@app.route('/login', methods=['GET'])
def display_login_page():

    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_user():
    """Login user and add them to the session."""

    #query DB using login information. 
    f_name = request.form.get('first_name')  #either lower case or upcase for user input discrepancy. 
    cell= request.form.get('cell')
    cell_number = cell_verify(cell)  #get correctly formated cell number
    password_hash = request.form.get('password')
    user = Users.query.filter((Users.f_name == f_name),
                              (Users.cell_number == cell_number)).first()

    #if we have a search query and the password is correct- add to session. 
    if user and user.check_password(password_hash):
        session['user_name'] = user.f_name
        session['user_id'] = user.user_id
        # flash("Successfully logged in!")
        return redirect('/user-page')  #redirect to users page.
    else: 
        flash("That is not a valid email & password.")
        return redirect('/login')   

@app.route('/logout')
def logout_user():
    """Remove user from session."""

    del session['user_name']
    del session['user_id']
    # flash("Successfully logged out!") #need to fix formating for flash messages

    return redirect('/')

@app.route('/user-page', methods=['GET'])
def display_user_page():
    """Display specific information about user."""

    if session.get('user_name',None):
        user = Users.query.filter(Users.user_id == session['user_id']).first()
        medications = user.u_meds #get medications for user in session. 
        med_dictionary = db_helper.make_dictionary_for_user_meds(medications)
        return render_template('user_page.html', 
                            user=user,
                            med_options=med_dictionary)
    else:
        return redirect('/login')
                            
@app.route('/user_data', methods=['POST'])
def send_user_data():
    """Display specific information about user."""

    req = request.get_json()  #get JSON from front-end
    med_id = req['med_id']  #pull med_id from JSON
    user = Users.query.filter(Users.user_id == session['user_id']).first()
    medications = user.u_meds #get medications for user in session. 
    med_info = User_meds.query.filter(User_meds.med_id == med_id).first()
    med_dictionary = db_helper.make_object_dictionary(med_info)
    #make response to pass back to front-end
    res = make_response(jsonify(med_dictionary), 200)
    return res

@app.route('/user-page', methods=['POST'])
def process_adding_user_medications():
    """Add user medications to DB from input on user profile page."""

    for_med_name = (request.form.get('med_name')).capitalize() #changed seed.py to have medicine name as caplitalize for display
    for_med_strength = (request.form.get('med_name')).upper() #strength in DB is upcase. 
    strength = (request.form.get('med_strength')).upper() #we want this in upcase if we store in db. 
    qty_per_dose = int(request.form.get('qty_per_dose'))
    dosing_schedule = int(request.form.get('dosing'))
    start_date = request.form.get('start_date')
    rx_start_date = datetime.strptime(start_date,'%Y-%m-%d')
    #place info in session
    session['for_med_name'] = for_med_name
    session['strength'] = strength
    session['qty_per_dose'] = qty_per_dose
    session['dosing_schedule'] = dosing_schedule
    session['rx_start_date'] = rx_start_date

    search_db = (Meds.query.filter((Meds.strength.like('%'+for_med_strength+'%'))| 
                            (Meds.medicine_name.like('%'+for_med_name+'%')))
                    .order_by(Meds.has_image.desc())
                    .all())

    database_med = db_helper.make_dictionary_from_query(search_db)

    if len(database_med) == 0: 
        #then med is not in db and need to query the API. 
        search_api = api.query_fda_api(for_med_name) 
        return render_template('confirm_med_api.html', api_results=search_api)
    else: 
        return render_template('confirm_med_db.html', database_med=database_med)

@app.route("/add_med", methods=['POST'])
def add_med_to_databse():
    """Add user medication to database and notify user."""

    #grab user from session. 
    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name
    user_id = session['user_id']
    #pulling info from confirm_med_api.html
    api_info = request.form.get('api_results')  #api_info returns as a string.
    #pulling info from confirm_med_db.html
    db_med_image = request.form.get('med_image')
    db_med_strength = request.form.get('med_strength')
    #pull info needed from session to call db_helper function. 
    med_name = session['for_med_name']
    session_strength = session['strength']
    qty_per_dose = session['qty_per_dose']
    times_per_day = session['dosing_schedule']
    rx_start_date = session['rx_start_date']
    api_results = api.query_fda_api(med_name)
    brand_name = api_results["brand_name"]
    
    if api_info == None:  #if med existed in the DB.
        #pull info needed to call db_helper function. 
        name_from_strength = db_med_strength[0]  #ignore space and other chars. 
        med = Meds.query.filter((Meds.strength.like('%'+name_from_strength+'%')) &
                            (Meds.img_path == db_med_image)).first()
        med_id = med.med_id
        db_helper.add_user_med_to_database(api_results, 
                                           med_id, 
                                           user_id, 
                                           qty_per_dose, 
                                           times_per_day, 
                                           rx_start_date) 
    else:
        #need to format strength to fit format in DB prior to instantiating.
        strength = ((med_name.upper())+ " " + (session_strength.upper()))
        #create new med instance prior to instantiating user med. 
        db_helper.instantiate_new_medication(strength, brand_name) 
        #query for newly instantiated medication to get med_id. 
        new = Meds.query.filter((Meds.strength == strength) & 
                                (Meds.medicine_name == (brand_name.capitalize()))).first()
        med_id = new.med_id 
        db_helper.add_user_med_to_database(api_results, 
                                           med_id, 
                                           user_id, 
                                           qty_per_dose, 
                                           times_per_day, 
                                           rx_start_date) 
    #delete items placed in session when user starts to add a new medication.
    del session['for_med_name']
    del session['strength']
    del session['qty_per_dose']
    del session['dosing_schedule']
    del session['rx_start_date']

    # flash("Medication Added!") #need to fix flash message format on page
    return redirect('/user-page')

@app.route("/add_med_unverified")
def display_add_medication_form():
    """Add med to DB if not in DB and not in API call- rare case."""

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    user_id = session['user_id']
    med_name = session['for_med_name']
    session_strength = session['strength']
    #need to format strength to fit format in DB prior to instantiating.
    strength = ((med_name.upper())+ " " + (session_strength.upper()))
    qty_per_dose = session['qty_per_dose']
    times_per_day = session['dosing_schedule']
    rx_start_date = session['rx_start_date']

    db_helper.instantiate_new_medication(strength, med_name)
    new = Meds.query.filter((Meds.strength == strength) & 
                                (Meds.medicine_name == (med_name.capitalize()))).first()
    med_id = new.med_id
    db_helper.add_unverified_med(user_id, 
                                 med_id, 
                                 qty_per_dose, 
                                 times_per_day, 
                                 rx_start_date)
    del session['for_med_name']
    del session['strength']
    del session['qty_per_dose']
    del session['dosing_schedule']
    del session['rx_start_date']

    flash("""We added your medication, however, there is no further information 
             regarding your medication at this time.""")
    return redirect('/user-page')


@app.route("/show_schedule_form", methods=['POST'])
def display_schedule_medication_form():
    """Display form to fill in order to schedule patients medication."""
    
    med_strength = request.form.get('med_strength')
    med_id = request.form.get('med_id')   
    return render_template('schedule_meds_form.html', 
                            med_strength=med_strength, 
                            med_id=med_id)

@app.route("/schedule_med", methods=['POST'])
def schedule_medication():
    """Update u_med in DB and schedule text notifications for medication."""

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    medications = user.u_meds #get medications for user in session. 
    med_dictionary = db_helper.make_dictionary_for_user_meds(medications)
    req = request.get_json()
    #pull info from session
    am = req['am_time']
    mid = req['mid_time']
    pm = req['pm_time']
    rx_duration = req['duration']
    qty = req['qty']
    refills = req['refills']
    med_strength = req['med_strength']
    med_id = req['med_id']
    
    if am != "":
        am_time = datetime.strptime(am,'%H:%M')
    else: 
        am_time = None
    if mid != "":
        mid_day_time = datetime.strptime(mid,'%H:%M')
    else: 
        mid_day_time = None 
    if pm != "":
        pm_time = datetime.strptime(pm, '%H:%M')
    else: 
        pm_time = None 

    user_med = User_meds.query.filter((User_meds.med_id == med_id)).first()

    user_med.am_time = am_time
    user_med.mid_day_time = mid_day_time
    user_med.pm_time = pm_time
    user_med.rx_duration = rx_duration
    user_med.qty = qty
    user_med.current_qty = qty
    user_med.refills = refills
    user_med.text_remind = True 

    db.session.add(user_med)  #update user medication in DB
    db.session.commit()
                                              
    res = make_response(jsonify(req), 200)  #make response to pass to front-end
    #get user info to send confirmation text
    med_name = user_med.brand_name
    cell = user_med.user.cell_number
    name = user_med.user.f_name
    message = (f"Hello {name}! Thank you for signing up and scheduling your meds! You will now recieve text reminders when it is time to take your {med_name}.")

    send_text_reminders(message, cell)
    return res 

@app.route("/delete_med", methods=['POST'])
def delete_medication():
    """Delete user medications from their list."""

    med_strength = request.form.get('med_strength')
    med_id = request.form.get('med_id')  
    med = User_meds.query.filter((User_meds.user_id == session['user_id']) & 
                                  (User_meds.med_id == med_id)).delete()
    db.session.commit()

    flash("Medication deleted!")
    return redirect('/user-page')


if __name__ == "__main__":
    
    schedule.every().day.at("22:00").do(send_for_active_users)
    print("I am checking for active users.")

    app.debug = False
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)
    # point that we invoke the DebugToolbarExtension
    # Use the DebugToolbar
    DebugToolbarExtension(app)

    schedule.run_continuously(1)
    
    app.run(port=5000, host='0.0.0.0')



    


from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension

from test_model import connect_to_db, db, Meds, Users, User_meds

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

    print("########API RESULTS#########")
    print(value)
    print(api_results)
    print("####################")

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

    session['user_name'] = user.f_name
    session['user_id'] = user.user_id
    flash("Successfully logged in!")
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
    print(medications)

    med_dictionary = db_query.make_dictionary_for_user_meds(medications)
    print(med_dictionary)
    

    return render_template('user_page.html', 
                            user=user,
                            med_options=med_dictionary) 
                            
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
    # user = Users.query.filter(Users.user_id == session['user_id']).first()
    # session['user_name'] = user.f_name
    # user_id = session['user_id']

    med_for_name = (request.form.get('med_name')).capitalize() #changed seed.py to have medicine name as caplitalize for display
    med_for_strength = (request.form.get('med_name')).upper() #strength in DB is upcase. 
    strength = (request.form.get('med_strength')).upper() #we want this in upcase if we store in db. 
    qty_per_dose = int(request.form.get('qty_per_dose'))
    dosing_schedule = int(request.form.get('dosing'))
    start_date = request.form.get('start_date')
    rx_start_date = datetime.strptime(start_date,'%Y-%m-%d')

    session['med_for_name'] = med_for_name
    session['strength'] = strength
    session['qty_per_dose'] = qty_per_dose
    session['dosing_schedule'] = dosing_schedule
    session['rx_start_date'] = rx_start_date

    # print(med_name, type(med_name))
    # print(strength, type(strength))
    # print(qty_per_dose, type(qty_per_dose))
    # print(dosing_schedule, type(dosing_schedule))
    # print(rx_start_date, type(rx_start_date))

    db = (Meds.query.filter((Meds.strength.like('%'+med_for_strength+'%'))| 
                            (Meds.medicine_name.like('%'+med_for_name+'%')))
                    .order_by(Meds.has_image.desc())
                    .all())

    database_med = db_query.make_dictionary_from_query(db)

    print("THIS IS THE DB", database_med, len(database_med))

    if len(database_med) == 0: 
        api_results = api.query_fda_api(med_for_name)
        print("THIS IS THE API", api_results, len(api_results))
       
        return render_template('confirm_med_api.html', api_results=api_results)
    else: 
        
        return render_template('confirm_med_db.html', database_med=database_med)


@app.route("/add_med", methods=['POST'])
def add_med_to_databse():

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name
    user_id = session['user_id']



    api_info = request.form.get('api_results')
    indications = request.form.get('indications')
    dosing_info = request.form.get('dosing_info')
    info_for_patients = request.form.get('info_for_patients')
    contraindications = request.form.get('contraindications')
    brand_name = request.form.get('brand_name')
    pharm_class = request.form.get('pharm_class')
    print('###########THIS IS API INFO BACK IN /ADD_MED##################')
    print(api_info)

    db_med_image = request.form.get('med_image')
    db_med_strength = request.form.get('med_strength')
    
    print('###########THIS IS DB INFO BACK IN /ADD_MED##################')
    print(db_med_image)
    
    if api_info == None:
        s = db_med_strength.split()
        strength = s[0]
        # print(strength)
        med = Meds.query.filter((Meds.strength.like('%'+strength+'%')) &
                                (Meds.img_path == db_med_image)).first()
        print('####THIS IS MED#####')
        print(med)
        med_id = med.med_id
        qty_per_dose = session['qty_per_dose']
        times_per_day = session['dosing_schedule']
        rx_start_date = session['rx_start_date']

        new_user_med = User_meds(user_id=user_id,
                            med_id=med_id,
                            qty_per_dose=qty_per_dose,
                            times_per_day=times_per_day,
                            rx_start_date=rx_start_date)
        db.session.add(new_user_med)
        db.session.commit()

        del session['med_for_name']
        del session['strength']
        del session['qty_per_dose']
        del session['dosing_schedule']
        del session['rx_start_date']
    else:
        
        med_name = session['med_for_name']

        session_strength = session['strength']
        strength = ((med_name.upper())+ " " + session_strength)

        qty_per_dose = session['qty_per_dose']
        times_per_day = session['dosing_schedule']
        rx_start_date = session['rx_start_date']

        if (len(indications)!=0) and (len(indications)<2000):
            indications = indications[2:-2]

        elif (len(indications) != 0) and (len(indications)>2000):
            indications = (indications[2:1998]+"...")
        
        if (len(dosing_info)!=0) and (len(dosing_info)<2000):
            dosing_info = dosing_info[2:-2]
        elif (len(dosing_info) != 0) and (len(dosing_info)>2000):
            dosing_info = (dosing_info[2:1998]+"...")

        if (len(info_for_patients)!=0) and (len(info_for_patients)<2000):
            info_for_patients = info_for_patients[2:-2]
        elif (len(info_for_patients) != 0) and (len(info_for_patients)>2000):
            info_for_patients = (info_for_patients[2:1998]+"...")

        if (len(contraindications)!=0) and (len(contraindications)<2000):
            contraindications = contraindications[2:-2]
        elif (len(contraindications) != 0) and (len(contraindications)>2000):
            contraindications = (contraindications[2:1998]+"...")

        if (len(brand_name)!=0) and (len(brand_name)<64):
            brand_name = brand_name[2:-2]
        elif (len(brand_name) != 0) and (len(brand_name)>64):
            brand_name = (brand_name[2:62]+"...")
        elif len(brand_name) == 0:
            brand_name = med_name

        if (len(pharm_class)!=0) and (len(pharm_class)<64):
            pharm_class = pharm_class[2:-2]
        elif (len(pharm_class) != 0) and (len(pharm_class)>64):
            pharm_class = (pharm_class[2:62]+"...")

        img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573708367/production_images/No_Image_Available.jpg")    

        new_med = Meds(strength=strength,
                       medicine_name=(brand_name.capitalize()),
                       has_image=False, 
                       img_path=img_path)
        db.session.add(new_med)
        db.session.commit()

        new = Meds.query.filter((Meds.strength == strength) & 
                                (Meds.medicine_name == (brand_name.capitalize()))).first()
        med_id = new.med_id

        new_user_med = User_meds(user_id=user_id,
                            med_id=med_id,
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

        del session['med_for_name']
        del session['strength']
        del session['qty_per_dose']
        del session['dosing_schedule']
        del session['rx_start_date']

    medications = user.u_meds #get medications for user in session. 

    med_dictionary = db_query.make_dictionary_for_user_meds(medications)

    flash("Medication Added!")
    return render_template('user_page.html', user=user, med_options=med_dictionary)

@app.route("/add_med_unverified")
def display_add_medication_form():

    user = Users.query.filter(Users.user_id == session['user_id']).first()
    session['user_name'] = user.f_name
    user_id = session['user_id']

    med_name = session['med_for_name']

    session_strength = session['strength']
    strength = ((med_name.upper())+ " " + session_strength)

    qty_per_dose = session['qty_per_dose']
    times_per_day = session['dosing_schedule']
    rx_start_date = session['rx_start_date']

    img_path = ("https://res.cloudinary.com/ddvw70vpg/image/upload/v1573708367/production_images/No_Image_Available.jpg")    

    new_med = Meds(strength=strength,
                   medicine_name=(med_name.capitalize()),
                   has_image=False, 
                   img_path=img_path)
    db.session.add(new_med)
    db.session.commit()

    new = Meds.query.filter((Meds.strength == strength) & 
                                (Meds.medicine_name == (med_name.capitalize()))).first()
    med_id = new.med_id

    new_user_med = User_meds(user_id=user_id,
                        med_id=med_id,
                        qty_per_dose=qty_per_dose,
                        times_per_day=times_per_day,
                        rx_start_date=rx_start_date)
    db.session.add(new_user_med)
    db.session.commit()

    del session['med_for_name']
    del session['strength']
    del session['qty_per_dose']
    del session['dosing_schedule']
    del session['rx_start_date']

    medications = user.u_meds #get medications for user in session. 

    med_dictionary = db_query.make_dictionary_for_user_meds(medications)

    flash("""We added your medication, however, there is no further information 
             regarding your medication at this time.""")
    return render_template('user_page.html', user=user, med_options=med_dictionary)


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
from twilio.rest import Client
import os
from test_model import connect_to_db, db, Meds, Users, User_meds

def send_text_reminders():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                         body="Join Earth's mightiest heroes. Like Kevin Bacon.",
                         from_=os.environ['TWILIO_NUMBER'],
                         to='+18056033859'
                     )

    print(message.sid)


ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']


def cell_verify(cell):
    """Uses Twilio API to look up cell number, returns number as string"""
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    phone_number = client.lookups \
                         .phone_numbers(cell) \
                         .fetch(type=['carrier'])

    return phone_number.phone_number

def find_active_users(): 
    """Find users that have scheduled their medications."""

    active = User_meds.query.filter(User_meds.text_remind == True).all()

    print(active)
    for user in active: 
        # print(user)
        am = user.am_time
        mid_day = user.mid_day_time
        pm = user.pm_time
        duration = user.rx_duration
        print(duration, type(duration))
        qty = user.qty  
        print(qty, type(qty))
        current = user.current_qty
        print("CURRENT", current, type(current))
        refills = user.refills
        print(refills, type(refills))
        qty_per_dose = user.qty_per_dose
        print(qty_per_dose, type(qty_per_dose))
        times_per_day = user.times_per_day
        print(times_per_day, type(times_per_day))

        daily_qty = qty_per_dose * times_per_day
        print(daily_qty, type(daily_qty))

        if current < qty_per_dose and refills > 0:  #current amount less than qty per dose. 
            
            #reset current qty to start qty & deduct dose amount 
            new_current_qty = (qty - qty_per_dose - 1) 
            user.current_qty = qty  

            new_refills = refills - 1  #deduct refills
            user.refills = new_refills

            db.session.add(user)
            db.session.commit()

            message = f"""{user.user.f_name}, assuming you refilled your medication. 
            It is time to take {user.qty_per_dose} tablets/capsules of {user.brand_name}. 
            You have {user.refills} left."""

            return message

        elif (current < (3 * daily_qty)) and (current > qty_per_dose) and refills > 0:  #current amount less than 3 times the daily qty. 

            update = current - qty_per_dose - 1 #update current qty from one dose. 
            user.current_qty = update

            db.session.add(user)
            db.session.commit()


            message = f"""{user.user.f_name}, it is time to take 
            {user.qty_per_dose} tablets/capsules of {user.brand_name}. You have 
            less than 3 days worth of medication, so remember to refill! 
            You have {user.refills} left."""

            return message

        elif current > (3 * daily_qty) and refills > 0:
            update = current - qty_per_dose - 1 #update current qty from one dose. 
            user.current_qty = update

            db.session.add(user)
            db.session.commit()


            message = f"""{user.user.f_name}, it is time to take 
            {user.qty_per_dose} tablets/capsules of {user.brand_name}."""

            return message

        elif (current < (5 * daily_qty)) and (current > qty_per_dose) and refills == 0:

            update = current - qty_per_dose - 1 #update current qty from one dose. 
            user.current_qty = update

            db.session.add(user)
            db.session.commit()


            message = f"""{user.user.f_name}, it is time to take 
            {user.qty_per_dose} tablets/capsules of {user.brand_name}. You have 
            less than 5 days worth of medication. You do not have any refills left. 
            Remember to ask your doctor for refills if you need to!"""

            return message

        elif current < qty_per_dose and refills == 0:

            user.current_qty = 0
            user.text_remind = False 

            db.session.add(user)
            db.session.commit()

            message = f"""{user.user.f_name}, it is time to finish up the rest of your
            {user.brand_name}. You dont have any more refills and you will be 
            out of medication after this dose. Your text reminders for this 
            medication will turn off now."""

            return message


    #send at if QD then send at AM or PM or default to 9:00 AM
        #if bid then send at AM & PM or default to 9 & 9 
        #if TID then send at AM, MId, and PM or default to 8,12, and 8 




# def send_text():
#     """Sends text alerts to user subscribers for current moon phase"""
#     client = Client(ACCOUNT_SID, AUTH_TOKEN)

#     tonights_moon_phase = find_tonights_moon()
#     alerts = check_alerts(tonights_moon_phase)

#     if alerts != None: 

#         for alert in alerts:

#             if alert.is_active == True:  
#                 text = write_text(#custom message here. )
#                 phone = alert.user.phone
#                 message = client.messages.create(body=text, from_=TWILIO_NUMBER, to=phone)
           
#             else:
#                 pass

#     else:
#         return None


# schedule.every().day.at("#find a wway to put varabile time here: 18:00").do(send_text)
#EVERY DAY WANT TO CHECK USERS AND RUN PILL DEDUCTIONS FOR THE DAY?
#OR WANT TO CHECK FOR USERS AND RUN NEXT DEDUCTIONS. 


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)


# if __name__ == "__main__":
    
#     connect_to_db(app)
#     app.debug=True
#     while True: 
#         schedule.run_pending() 
#         time.sleep(1) 





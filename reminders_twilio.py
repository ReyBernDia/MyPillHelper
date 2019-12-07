from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from model import connect_to_db, db, Meds, Users, User_meds
import schedule
import time
from datetime import datetime
import server
from flask import Flask, render_template, redirect, request, flash, session, g

ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']


def cell_verify(cell):
    """Uses Twilio API to look up cell number, returns number as string"""
  
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    try:
        phone_number = client.lookups \
                             .phone_numbers(cell) \
                             .fetch(type=['carrier'])
        return phone_number.phone_number
    except TwilioRestException as e:
        if e.code == 20404:
            return False
        else:
            raise e

def send_text_reminders(message, phone):
    """Given message and phone number, send users a text using Twilio API."""

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    message = client.messages \
                    .create(
                         body=message,
                         from_=os.environ['TWILIO_NUMBER'],
                         to=phone
                     )
    print(message.sid)

def send_for_active_users(): 
    """Find users that have scheduled their medications & run schedule."""
    
    active = User_meds.query.filter(User_meds.text_remind == True).all()
    print(active)
    if len(active) != 0:
        for user in active:
            print(user)
            am = user.am_time
            mid_day = user.mid_day_time
            pm = user.pm_time
            times_per_day = user.times_per_day
            duration = user.rx_duration
            qty = user.qty  
            current = user.current_qty
            refills = user.refills
            qty_per_dose = user.qty_per_dose
            daily_qty = qty_per_dose * times_per_day

            if current > (3 * daily_qty) and refills > 0:
                update = current - (qty_per_dose * times_per_day) #update current qty from one dose. 
                user.current_qty = update

                db.session.add(user)
                db.session.commit()

                message = (f"{user.user.f_name}, it is time to take {user.qty_per_dose} tablets/capsules of {user.brand_name}.")

                phone = user.user.cell_number
                run_scheduled_for_texts(am,mid_day,pm,message,phone)

            elif (current < (3 * daily_qty)) and (current > qty_per_dose) and refills > 0:  #current amount less than 3 times the daily qty. 
                update = current - (qty_per_dose * times_per_day) #update current qty from one dose. 
                user.current_qty = update

                db.session.add(user)
                db.session.commit()

                message = (f"{user.user.f_name}, it is time to take {user.qty_per_dose} tablets/capsules of {user.brand_name}. You have less than 3 days worth of medication, so remember to refill! You have {user.refills} refills left.")

                phone = user.user.cell_number
                run_scheduled_for_texts(am,mid_day,pm,message,phone)

            elif current < qty_per_dose and refills > 0:  #current amount less than qty per dose. 
                #reset current qty to start qty & deduct dose amount 
                new_current_qty = qty - (qty_per_dose * times_per_day)
                user.current_qty = qty  
                new_refills = refills - 1  #deduct refills
                user.refills = new_refills

                db.session.add(user)
                db.session.commit()

                message = (f"{user.user.f_name}, assuming you refilled your medication. It is time to take {user.qty_per_dose} tablets/capsules of {user.brand_name}. You have {user.refills} refills left.")

                phone = user.user.cell_number
                run_scheduled_for_texts(am,mid_day,pm,message,phone)

            elif (current < (5 * daily_qty)) and (current > qty_per_dose) and refills == 0:
                update = current - (qty_per_dose * times_per_day) #update current qty from one dose. 
                user.current_qty = update

                db.session.add(user)
                db.session.commit()

                message = (f"{user.user.f_name}, it is time to take {user.qty_per_dose} tablets/capsules of {user.brand_name}. You have less than 5 days worth of medication. You do not have any refills left. Remember to ask your doctor for refills if you need to!")

                phone = user.user.cell_number
                run_scheduled_for_texts(am,mid_day,pm,message,phone)

            elif current < qty_per_dose and refills == 0:
                user.current_qty = 0
                user.text_remind = False 

                db.session.add(user)
                db.session.commit()

                message = (f"{user.user.f_name}, it is time to finish up the rest of your {user.brand_name}. You don't have any more refills, and you will be out of medication after this dose. Your text reminders for this medication will turn off now. Thank you!")

                phone = user.user.cell_number
                run_scheduled_for_texts(am,mid_day,pm,message,phone)
    else: 
        return None 

def run_scheduled_for_texts(am,mid,pm,message,phone):
    """Determine schedule for sending out texts."""
    
    if am and mid and pm == None: 
        schedule.every().day.at("09:00").do(send_text_reminders, message=message, phone=phone)
    
    elif (am != None) and ((mid and pm) == None):
        am_time = am[11:-3]
        schedule.every().day.at(am_time).do(send_text_reminders, message=message, phone=phone)

    elif (pm != None) and ((am and mid) == None):
        pm_time = pm[11:-3]
        schedule.every().day.at(pm_time).do(send_text_reminders, message=message, phone=phone)

    elif (mid != None) and ((am and pm) == None):
        mid_time = mid[11:-3]
        schedule.every().day.at(mid_time).do(send_text_reminders, message=message, phone=phone)

    elif ((am and mid) != None) and (pm == None):
        am_time = am[11:-3]
        mid_time = mid[11:-3]
        schedule.every().day.at(am_time).do(send_text_reminders, message=message, phone=phone)
        schedule.every().day.at(mid_time).do(send_text_reminders, message=message, phone=phone)

    elif ((am and mid and pm) != None):
        am_time = am[11:-3]
        mid_time = mid[11:-3]
        pm_time = pm[11:-3]

        schedule.every().day.at(f"{am_time}").do(send_text_reminders, message=message, phone=phone)
        schedule.every().day.at(f"{mid_time}").do(send_text_reminders, message=message, phone=phone)
        schedule.every().day.at(f"{pm_time}").do(send_text_reminders, message=message, phone=phone)

    elif ((am and pm) != None) and (mid == None):
        am_time = am[11:-3]
        pm_time = mid[11:-3]
        schedule.every().day.at(am_time).do(send_text_reminders, message=message, phone=phone)
        schedule.every().day.at(pm_time).do(send_text_reminders, message=message, phone=phone)

    elif ((pm and mid) != None) and (am == None):
        mid_time = am[11:-3]
        pm_time = mid[11:-3]
        schedule.every().day.at(mid_time).do(send_text_reminders, message=message, phone=phone)
        schedule.every().day.at(pm_time).do(send_text_reminders, message=message, phone=phone)

    print(schedule.jobs)


if __name__ == "__main__":

    from server import app
    connect_to_db(app)
    schedule.run_continuously(1)



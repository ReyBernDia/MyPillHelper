from twilio.rest import Client
import os


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
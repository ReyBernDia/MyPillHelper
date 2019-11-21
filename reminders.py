from twilio.rest import Client
import os


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
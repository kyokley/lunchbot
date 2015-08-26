import requests
from settings import API_TOKEN

ROOM_ID = '1807405'
HIPCHAT_URL = 'https://api.hipchat.com/v2/room/%s/notification?auth_token=%s' % (ROOM_ID, API_TOKEN)

def send_test():
    message = 'this is a test'
    send_notification(message)

def send_notification(message):
    payload = build_message_payload(message)
    requests.post(HIPCHAT_URL, json=payload)

def build_message_payload(message,
                     color='black',
                     message_format='text',
                     notify=False):
    payload = {'message': message,
               'message_format': message_format,
               'color': color,
               'notify': notify,
               }
    return payload

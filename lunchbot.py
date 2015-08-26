import requests
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from settings import API_TOKEN
from collections import namedtuple

StreamItem = namedtuple('StreamItem', ['source', 'time', 'text', 'link'])

ROOM_ID = '1807405'
HIPCHAT_URL = 'https://api.hipchat.com/v2/room/%s/notification?auth_token=%s' % (ROOM_ID, API_TOKEN)
CFTF_TWITTER_URL = 'https://twitter.com/chiftf_aon'

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

class StreamParser(object):
    @staticmethod
    def _html_to_text(html):
        # Hack to prevent Beautiful Soup from collapsing space-keeping tags
        # until no whitespace remains at all
        html = re.sub('<(br|p|li)', ' \\g<0>', html, flags=re.IGNORECASE)
        text = BeautifulSoup(html, 'html.parser').get_text()
        # Idea from http://stackoverflow.com/a/1546251
        return ' '.join(text.strip().split())

    @classmethod
    def get_tweets(cls, html):
        document = BeautifulSoup(html, 'html.parser')

        for tweet in document.find_all('p', class_='tweet-text'):
            header = tweet.find_previous('div', class_='stream-item-header')

            name = header.find('strong', class_='fullname').string
            username = header.find('span', class_='username').b.string

            time_string = header.find('span', class_='_timestamp')['data-time']
            timestamp = datetime.fromtimestamp(int(time_string))

            # For Python 2 and 3 compatibility
            to_unicode = unicode if sys.version_info[0] < 3 else str
            # Remove ellipsis characters added by Twitter
            text = cls._html_to_text(to_unicode(tweet).replace(u'\u2026', ''))

            link = 'https://twitter.com%s' % header.find('a', class_='tweet-timestamp')['href']

            yield StreamItem('%s (@%s)' % (name, username), timestamp, text, link)

class LunchBot(object):
    def __init__(self):
        self.tweets = set()

    def update(self):
        for item in StreamParser.get_tweets(CFTF_TWITTER_URL):
            if item.link in self.tweets:
                continue

            print item


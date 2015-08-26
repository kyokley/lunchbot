import requests
import re
import sys
import time
from datetime import datetime
from bs4 import BeautifulSoup
from settings import API_TOKEN, ROOM_ID
from collections import namedtuple

StreamItem = namedtuple('StreamItem', ['source', 'time', 'text', 'link', 'ref_links'])

HIPCHAT_URL = 'https://textura.hipchat.com/v2/room/%s/notification?auth_token=%s' % (ROOM_ID, API_TOKEN)
CFTF_HANDLE = 'chiftf_aon'
CFTF_TWITTER_URL = 'https://twitter.com/%s' % CFTF_HANDLE
SLEEP_INTERVAL = .5

DEBUG = True

def send_test():
    message = 'this is a test'
    resp = send_notification(message)
    return resp

def send_notification(message):
    payload = build_message_payload(message)
    if DEBUG:
        print message
    else:
        return requests.post(HIPCHAT_URL, json=payload)

def build_message_payload(message,
                          color='green',
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
    def get_tweets(cls, url):
        html = requests.get(url).content
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

            refs = tweet.findAll('a', class_='twitter-atreply')
            ref_links = ['https://twitter.com%s' % ref['href'] for ref in refs]

            link = 'https://twitter.com%s' % header.find('a', class_='tweet-timestamp')['href']

            if username != CFTF_HANDLE:
                continue
            yield StreamItem('%s (@%s)' % (name, username), timestamp, text, link, ref_links)

class LunchBot(object):
    def __init__(self):
        self.tweets = set()

    def update(self):
        for item in StreamParser.get_tweets(CFTF_TWITTER_URL):
            if item.link in self.tweets:
                continue

            send_notification("Today's food trucks are...")
            for ref_link in item.ref_links:
                if ref_link:
                    send_notification(ref_link)
            self.tweets.add(item.link)
            time.sleep(SLEEP_INTERVAL)


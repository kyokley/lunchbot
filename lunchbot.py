import requests
import time
from bs4 import BeautifulSoup
from settings import API_TOKEN, ROOM_ID, COMPANY, DEBUG
from collections import namedtuple
from datetime import datetime

StreamItem = namedtuple('StreamItem', ['username', 'link', 'ref_links', 'text', 'timestamp'])

HIPCHAT_URL = 'https://%s.hipchat.com/v2/room/%s/notification?auth_token=%s' % (COMPANY, ROOM_ID, API_TOKEN)
CFTF_HANDLES = {'chiftf_aon': 'Aon',
                'chiftf_30elake': 'State & Lake'}
CFTF_TWITTER_URL_TEMPLATE = 'https://twitter.com/%s'
EXCLUDES = ['fidotogo', # Be sure to define these in all lowercase!!!!
        ]
SLEEP_INTERVAL = 60 * 10
NOTIFICATION_INTERVAL = .5

def send_test():
    message = 'this is a test'
    resp = send_notification(message)
    return resp

def send_notification(message, dry_run=False):
    payload = build_message_payload(message)
    if DEBUG or dry_run:
        print message
    else:
        time.sleep(NOTIFICATION_INTERVAL)
        return requests.post(HIPCHAT_URL, json=payload, verify=False)

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

def get_tweets(url):
    html = requests.get(url, verify=False).content
    document = BeautifulSoup(html, 'html.parser')

    for tweet in document.find_all('p', class_='tweet-text'):
        header = tweet.find_previous('div', class_='stream-item-header')
        username = header.find('span', class_='username').b.string

        if username.lower() in EXCLUDES:
            continue

        ref_links = []
        if username not in CFTF_HANDLES:
            ref_links.append('https://twitter.com/%s' % username)

        refs = tweet.findAll('a', class_='twitter-atreply')
        ref_links.extend(['https://twitter.com%s' % ref['href'] for ref in refs])

        link = 'https://twitter.com%s' % header.find('a', class_='tweet-timestamp')['href']
        text = tweet and tweet.text.encode('ascii', errors='ignore')
        data_time = tweet.find_previous().get('data-time')
        timestamp = (data_time and
                     datetime.fromtimestamp(int(data_time)) or
                     None)


        yield StreamItem(username, link, ref_links, text, timestamp)

class LunchBot(object):
    def __init__(self):
        self.tweets = set()

    def update(self, dry_run=False):
        try:
            for handle in CFTF_HANDLES:
                url = CFTF_TWITTER_URL_TEMPLATE % handle

                for item in get_tweets(url):
                    if item.link in self.tweets:
                        continue

                    print
                    if item.username == handle:
                        send_notification("Today's food trucks at %s are..." % CFTF_HANDLES[handle], dry_run=dry_run)

                        for ref_link in item.ref_links:
                            if ref_link:
                                send_notification(ref_link, dry_run=dry_run)
                    else:
                        send_notification('@%s says:\n%s' % 
                                (item.username,
                                 item.text,
                                 ), 
                                dry_run=dry_run)
                        ref_link = item.ref_links and item.ref_links[0] or ''
                        if ref_link:
                            send_notification(ref_link, dry_run=dry_run)

                    self.tweets.add(item.link)
        except Exception, e:
            print e

def main():
    print 'Running...'
    bot = LunchBot()
    
    if not DEBUG:
        # Consume any old tweets to prepare for the new ones!
        bot.update(dry_run=True)

    try:
        while True:
            print 'Starting update at %s' % datetime.now()
            bot.update()
            print 'Finished update at %s' % datetime.now()
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        print 'Shutting down'

if __name__ == '__main__':
    main()

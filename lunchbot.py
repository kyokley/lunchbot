import requests
import time
from bs4 import BeautifulSoup
from settings import API_TOKEN, ROOM_ID, COMPANY, DEBUG
from collections import namedtuple
from datetime import datetime

StreamItem = namedtuple('StreamItem', ['username', 'link', 'ref_links', 'text', 'timestamp'])

HIPCHAT_URL = 'https://%s.hipchat.com/v2/room/%s/notification?auth_token=%s' % (COMPANY, ROOM_ID, API_TOKEN)
CFTF_HANDLE = 'chiftf_aon'
CFTF_TWITTER_URL = 'https://twitter.com/%s' % CFTF_HANDLE
SLEEP_INTERVAL = 60 * 10
NOTIFICATION_INTERVAL = .5

def send_test():
    message = 'this is a test'
    resp = send_notification(message)
    return resp

def send_notification(message):
    payload = build_message_payload(message)
    if DEBUG:
        print message
    else:
        time.sleep(NOTIFICATION_INTERVAL)
        return requests.post(HIPCHAT_URL, json=payload, verify=True)

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
    html = requests.get(url, verify=True).content
    document = BeautifulSoup(html, 'html.parser')

    for tweet in document.find_all('p', class_='tweet-text'):
        header = tweet.find_previous('div', class_='stream-item-header')
        username = header.find('span', class_='username').b.string

        refs = tweet.findAll('a', class_='twitter-atreply')
        ref_links = ['https://twitter.com%s' % ref['href'] for ref in refs]

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

    def update(self, send_notifications=True):
        try:
            for item in get_tweets(CFTF_TWITTER_URL):
                if item.link in self.tweets:
                    continue

                print
                if item.username == CFTF_HANDLE:
                    if send_notifications:
                        send_notification("Today's food trucks are... (%s)" % datetime.now().strftime('%b-%d'))
                    else:
                        print 'The following notifications are not being sent...'

                    for ref_link in item.ref_links:
                        if ref_link:
                            if send_notifications:
                                send_notification(ref_link)
                            else:
                                print ref_link
                else:
                    if item.timestamp:
                        send_notification('@%s says: (%s)' % 
                                (item.username, item.timestamp.strftime('%b-%d %I:%M%p')))
                    else:
                        send_notification('@%s says:' % (item.username))
                    send_notification(item.text)

                self.tweets.add(item.link)
        except Exception, e:
            print e

def main():
    print 'Running...'
    bot = LunchBot()
    
    if not DEBUG:
        # Consume any old tweets to prepare for the new ones!
        bot.update(send_notifications=False)

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

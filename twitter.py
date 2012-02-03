import json
import time
from datetime import datetime, timedelta
import re
import pytz

class User():

	def __init__(self, timezone):
		self.timezone = timezone
		self.tweets = []
	
	@property
	def tweet_offsets(self):
		offset = self.tweets[0].timestamp
		return [(t.timestamp-offset) for t in self.tweets]

	@property
	def tweets_by_month(self):
		tbm = {}
		for tweet in self.tweets:
			d = (tweet.time.year,tweet.time.month)
			tbm[d] = tbm.get(d, 0) + 1
		return [(key[0], key[1], tbm[key]) for key in sorted(tbm.keys())]

class Tweet():

	def __init__(self, content, time, is_reply):
		self.content = content
		self.time = time
		self.is_reply = is_reply

	@property
	def timestamp(self):
		return time.mktime(self.time.timetuple())


def get_timezone(name):
	'''Twitter doesn't return the Olson names for the timezones,
	so we have to make an educated guess as to the user's location.
	If we don't get a match, we give up and return UTC.'''
	from pytz import common_timezones
	name = re.sub(r'\s[^\s]+', '', name)
	for timezone in common_timezones:
		m = re.search(name, timezone)
		if m != None:
			return timezone
	return 'UTC'

def process_tweets(tweets):
	user = User(pytz.timezone(get_timezone(tweets[0]['user']['time_zone'])))
	
	for tweet in tweets:
		utc_timestamp = datetime.strptime(re.sub('\+\d{4}\s','',tweet['created_at']),
				'%a %b %d %H:%M:%S %Y')
		local_timestamp = utc_timestamp.replace(tzinfo=pytz.utc).astimezone(user.timezone)

		# Twitter returns tweets in reverse chronological order; we reverse the order here
		# so that tweets are sorted first to last
		user.tweets.insert(0, Tweet(tweet['text'], local_timestamp, bool(re.search('^@', tweet['text']))))
	return user

if __name__=='__main__':
	user = process_tweets(json.loads(open('tweets', 'r').readline()))
	print user.tweets_by_month

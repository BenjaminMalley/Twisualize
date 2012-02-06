import oauth2 as oauth
import config
import urlparse
from flask import Flask, redirect, url_for, session, render_template, request, flash, make_response
from urllib import urlencode
import time
import json
import twitter
import redis

app = Flask(__name__)
app.secret_key = config.CKEY
app.consumer = oauth.Consumer(key=config.CKEY, secret=config.CSEC)
app.cache = redis.StrictRedis(host='localhost', port=6379, db=0)

def verify_response(resp):
	if resp['status'] != '200':
		session.pop('request_token', None)
		flash('Bad response from Twitter: {0}'.format(resp))
		return redirect(url_for('index'))
	else:
		return None

def get_tweets(client):
	'''Queries Twitter API for user tweets until it gets 0 back.
	Concatenates and returns tweets.'''
	tweets = []
	page = 1
	while True: # repeat until tweet supply is exhausted 
		url = config.API+'1/statuses/user_timeline.json?count=200&page={0}'.format(page)
		resp, content = client.request(url, 'GET', body=urlencode({
			'screen_name': session['access_token']['screen_name'],
			'include_entities': 'false',
		}))
		verify_response(resp)
	
		if content == '[]':
			return tweets
		page += 1 # get the next page of tweets
		tweets.extend(json.loads(content))


@app.route('/')
def index():
	# for debugging -- this is an annoying bug
	# TO DO: make sure an incomplete request doesn't leave request_token
	# in the session
	#session.pop('request_token', None)

	# is this an oauth callback?
	if 'request_token' in session:
		auth_token = oauth.Token(session['request_token']['oauth_token'],
			session['request_token']['oauth_token_secret'])

		# response is verified; remove the request token 
		# user will have to re-authenticate on next load
		session.pop('request_token', None)

		client = oauth.Client(app.consumer, auth_token)
		resp, content = client.request(config.AUTH_URL+'access_token', 'GET')
		
		verify_response(resp)
		
		session['access_token'] = dict(urlparse.parse_qsl(content))

		if app.cache.get(session['access_token']['screen_name']) == None:
			
			token = oauth.Token(key=session['access_token']['oauth_token'],
				secret=session['access_token']['oauth_token_secret'])
		
			client = oauth.Client(app.consumer, token)
			
			tweets = []
			page = 1
			while True: # repeat until tweet supply is exhausted 
				url = config.API+'1/statuses/user_timeline.json?count=200&page={0}'.format(page)
				resp, content = client.request(url, 'GET', body=urlencode({
					'screen_name': session['access_token']['screen_name'],
					'include_entities': 'false',
				}))

				if resp['status'] != '200':
					session.pop('request_token', None)
					flash('Bad response from Twitter: {0}'.format(resp))
					return redirect(url_for('index'))

				if content == '[]':
					break
				page += 1 # get the next page of tweets
				tweets.extend(json.loads(content))
			

			# use a pipeline so we don't accidentally leave keys in Redis
			# that won't get cleaned up.
			with app.cache.pipeline() as pipe:
				pipe.set(session['access_token']['screen_name'], json.dumps(tweets))
				# 86400 = 24 hours
				pipe.expire(session['access_token']['screen_name'], 86400)
				pipe.execute()

		# what we should be doing here is rendering a page, processing tweets in the
		# background and using AJAX to fill in the viz
		# but this will do for now
		resp = make_response(render_template('visualize.html'))
		resp.set_cookie('user', session['access_token']['screen_name'])
		return resp
	else: # just render the standard index page
		return render_template('index.html')

@app.route('/authorize/')
def authorize():
	'''Redirects user to Twitter OAuth authorization page.
	Redirects back to /success/'''

	client = oauth.Client(app.consumer)

	resp, content = client.request(config.AUTH_URL+'request_token', 'POST',
							body=urlencode({'oauth_callback': config.SITE_URL+url_for('index')}))
	verify_response(resp)

	session['request_token'] = dict(urlparse.parse_qsl(content))

	return redirect('{0}?oauth_token={1}'.format(config.AUTH_URL+'authorize',
							session['request_token']['oauth_token']))


@app.route('/data/<user>/<aggregation>/')
def get_data(user,aggregation):
	if session['access_token'] != None:
		data = app.cache.get(session['access_token']['screen_name'])
		user = twitter.process_tweets(json.loads(data))
		try:
			return str(getattr(user, aggregation)).replace("'", '"')
		except AttributeError:
			# bad data aggregation request
			return make_response('Nothing here!', 404)
	else:
		return make_response('You must have an valid session to complete this request.', 401)

@app.route('/test/')
def test():
	return make_response('You must be cool!', 401)

if __name__=='__main__':
	app.debug = config.DEBUG
	app.run()

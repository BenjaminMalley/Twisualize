import oauth2 as oauth
import config
import urlparse
from flask import Flask, redirect, url_for, session, render_template, request
from urllib import urlencode
import time
import json

app = Flask(__name__)
app.secret_key = config.CKEY
app.consumer = oauth.Consumer(key=config.CKEY, secret=config.CSEC)


def verify_response(resp):
	if resp['status'] != '200':
		raise Exception('uh oh')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/authorize/')
def authorize():
	'''Redirects user to Twitter OAuth authorization page.
	Redirects back to /success/'''

	client = oauth.Client(app.consumer)

	resp, content = client.request(config.AUTH_URL+'request_token', 'POST',
							body=urlencode({'oauth_callback': config.SITE_URL+url_for('visualize')}))
	verify_response(resp)

	session['request_token'] = dict(urlparse.parse_qsl(content))

	return redirect('{0}?oauth_token={1}'.format(config.AUTH_URL+'authorize',
							session['request_token']['oauth_token']))

@app.route('/visualize/')
def visualize():
	'''Retrieves user info from Twitter and visualizes it.
	If request_token is not in session, redirects to index.'''

	if 'request_token' in session:
		auth_token = oauth.Token(session['request_token']['oauth_token'],
			session['request_token']['oauth_token_secret'])

		client = oauth.Client(app.consumer, auth_token)
		resp, content = client.request(config.AUTH_URL+'access_token', 'GET')
		verify_response(resp)
		
		# response is verified; remove the request token 
		# prevents a bug where the user navigates to /success/ 
		session.pop('request_token', None)

		session['access_token'] = dict(urlparse.parse_qsl(content))

		request_url = 'https://api.twitter.com/1/statuses/user_timeline.json?screen_name={0}&include_entities=false'.format(
			session['access_token']['screen_name'])
		token = oauth.Token(key=session['access_token']['oauth_token'],
			secret=session['access_token']['oauth_token_secret'])
		
		client = oauth.Client(app.consumer, token)
		
		resp, content = client.request(request_url, 'GET')
		verify_response(resp)

		content = json.loads(content)
		tweets = [i[u'text'] for i in content]

		return render_template('visualize.html', tweets=tweets)
	else:
		return redirect(url_for('index'))

if __name__=='__main__':
	app.debug = config.DEBUG
	app.run()

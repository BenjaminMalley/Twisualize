import oauth2 as oauth
import config
import urlparse
from flask import Flask, redirect, url_for, session, render_template, request
from urllib import urlencode
import time

app = Flask(__name__)
app.secret_key = config.CKEY
app.consumer = oauth.Consumer(key=config.CKEY, secret=config.CSEC)

@app.route('/')
def get_auth():

	client = oauth.Client(app.consumer)

	resp, content = client.request(config.AUTH_URL+'request_token', 'POST',
							body=urlencode({'oauth_callback': config.SITE_URL+'/success/'}))
	if resp['status'] != '200': raise Exception('uh oh')

	session['request_token'] = dict(urlparse.parse_qsl(content))

	return redirect('{0}?oauth_token={1}'.format(config.AUTH_URL+'authorize',
							session['request_token']['oauth_token']))

@app.route('/success/')
def get_token():

	if 'request_token' in session.keys():
		auth_token = oauth.Token(session['request_token']['oauth_token'],
			session['request_token']['oauth_token_secret'])

		client = oauth.Client(app.consumer, auth_token)
		resp, content = client.request(config.AUTH_URL+'access_token', 'GET')
		if resp['status'] != '200': raise Exception('oh my!')

		session['access_token'] = dict(urlparse.parse_qsl(content))

		request_url = 'https://api.twitter.com/1/statuses/user_timeline.json?screen_name={0}&include_entities=false'.format(
			session['access_token']['screen_name'])
		token = oauth.Token(key=session['access_token']['oauth_token'],
			secret=session['access_token']['oauth_token_secret'])
		
		client = oauth.Client(app.consumer, token)
		
		resp, content = client.request(request_url, 'GET')
		print content
		print resp
		if resp['status'] != '200': raise Exception('uh oh')
		
		return 'hello world'

if __name__=='__main__':
	app.debug = config.DEBUG
	app.run()

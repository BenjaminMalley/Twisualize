import oauth2 as oauth
import config
import urlparse
from flask import Flask, redirect, url_for, session
from urllib import urlencode

app = Flask(__name__)

@app.route('/')
def get_auth():

	consumer = oauth.Consumer(key=config.CKEY, secret=config.CSEC)
	client = oauth.Client(consumer)

	resp, content = client.request(config.AUTH_URL+'request_token', 'POST',
							body=urlencode({'oauth_callback': config.SITE_URL+'/success/'}))
	if resp['status'] != '200': raise Exception('uh oh')

	session['token_request'] = dict(urlparse.parse_qsl(content))

	return redirect('{0}?oauth_token={1}'.format(auth_url+'authorize',
							session['token_request']['oauth_token']))

@app.route('/success/')
def get_token():
	if 'token_request' in session.keys:
		session['token'] = oauth.Token(session['token_request']['oauth_token'],
			session['token_request']['oauth_token_secret'])
		
		client = oauth.Client(consumer, token)
		
		resp, content = client.request(config.AUTH_URL+'access_token', 'GET')
		if resp['status'] != '200': raise Exception('uh oh')

		session['token'] = dict(urlparse.parse_qsl(content))

if __name__=='__main__':
	app.debug = config.DEBUG
	app.run()

from flask import Flask, render_template, request, redirect, url_for,flash, jsonify
app = Flask(__name__)
from flask import session as login_session
import random,string
from sqlalchemy import create_engine,desc,func
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Going

import httplib2,urllib
import json
from flask import make_response
import requests

##CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']

engine = create_engine('sqlite:///goingOut.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_DATA = json.loads(open('client_data.json','r').read())['web']

@app.route('/')
def main():
    	if 'username' not in login_session:
        	login = False
	else:
     		login = True
     	login_session["query"] = None
	return render_template("resCordinator.html",REST=[], CITY = None, LOGIN = login)


@app.route('/search/<string:City_name>')
def result(City_name):
	h = httplib2.Http()
	zomatoKey="5f643333da9b400bbf543e50e0d83758"
	headers = {"Accept": "application/json","user-key": zomatoKey}
	location = City_name
	login_session["query"] = City_name
	url = "https://developers.zomato.com/api/v2.1/locations?query="+urllib.quote_plus(location)
	result = json.loads((h.request(url,headers=headers))[1])
 	print result
        try:
 		city_id = result["location_suggestions"][0]["entity_id"]
 	except:
      		return "<html>Location Not found<br><a href='"+url_for('main')+"'>return to home page</a>"
	url = "https://developers.zomato.com/api/v2.1/search?entity_id="+str(city_id)+"&entity_type=city&count=10&sort=rating"
 	result = json.loads((h.request(url,headers=headers))[1])
 	rest = result["restaurants"]
  	for i in rest:
       		count = session.query(Going).filter_by(rest_id = i['restaurant']['id']).count()
       		i["restaurant"].update({"count":count})
       		print (i["restaurant"]["name"]).encode('utf-8')

	return render_template("resCordinator.html",REST=rest,CITY=City_name)

@app.route('/post/',methods=["POST"])
def going():
    if 'username' not in login_session:
        	return jsonify({'result':False})
    else:
     		user = session.query(User).filter_by(name = login_session["username"]).one()
       		print user.id

    result = json.loads(request.data)
    print result["id"]
    newGoing = Going(name = result["name"], rest_id = result["id"], user_id = user.id,user = user)
    session.add(newGoing)
    session.commit()
    count = session.query(Going).filter_by(rest_id = result['id']).count()
    return jsonify({'result':'Going','count':count})

@app.route('/oauth/login/')
def login():
	state = ''.join(random.choice(string.ascii_uppercase+string.digits) for x in xrange(32))
	login_session['state'] = state
	parm = {'client_id':CLIENT_DATA['client_id'],'redirect_uri':'http://localhost:5000/oauth/gitLogin','scope':'user','state':state}
	url = 'https://github.com/login/oauth/authorize?'
	return redirect(url+urllib.urlencode(parm))

@app.route('/oauth/disconnect/')
def disconnect():
	del login_session['access_token']
  	del login_session['provider']
  	del login_session['username']
  	del login_session['picture']
	del login_session['email']
	return redirect(url_for('main'))

@app.route('/oauth/gitLogin/')
def gitLogin():
	if request.args['state'] != login_session['state']:
     		return "<html><title>Error</title><h1>Error State does not match</h1>.</html>"
    	print request.args['code']
    	parm = {'client_id':CLIENT_DATA["client_id"],'client_secret':CLIENT_DATA['client_secret'],'code':request.args['code'],'state':login_session['state']}
	url = 'https://github.com/login/oauth/access_token?'+ urllib.urlencode(parm)
 	h = httplib2.Http()
  	result = h.request(url,'POST')[1]
  	print (result)
  	url = 'https://api.github.com/user?'+result
  	data = h.request(url,'GET')[1]
  	data = json.loads(data)
   	print data
  	login_session['access_token'] = result
  	login_session['provider'] = 'github'
  	login_session['username'] = data["login"]
  	login_session['picture'] = data['avatar_url']
	login_session['email'] = data['url']
	if (getUserId(login_session['email']) != None):
    		print("Oho")
    		login_session['user_id'] = getUserId(login_session['email'])
    	else:
    		login_session['user_id'] = createUser(login_session)
    	if login_session["query"]==None:
    		return redirect(url_for('main'))
	else:
           	return redirect(url_for('result',City_name=login_session["query"]))


def createUser(login_session):
	newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserId(user_email):
	try:
		user =  session.query(User).filter_by(email=user_email).one()
		return user.id
	except:
		return None

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Team, Player, User
from flask import session as login_session
import random
import string
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
import httplib2
from flask import make_response
import requests
import json
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "team"


# DB Connection
engine = create_engine('sqlite:///teamplayerswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)



@app.route('/gconnect', methods=['POST'])
def gconnect():
    #check Token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        #except if an error
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid for url
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response


    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    login_session['provider'] = 'google'

    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

#dealing with user

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None



@app.route('/gdisconnect')
def gdisconnect():
    #used to disconnect the user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#JSON end point
@app.route('/team/<int:team_id>/player/JSON')
def teamPlayerJSON(team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    players = session.query(Player).filter_by(
       team_id=team_id).all()
    return jsonify(player=[i.serialize for i in players])

@app.route('/team/<int:team_id>/player/<int:player_id>/JSON')
def playerJSON(team_id, player_id):
    player = session.query(Player).filter_by(id=player_id).one()
    return jsonify(player=player.serialize)


@app.route('/team/JSON')
def teamsJSON():
    teams = session.query(Team).all()
    return jsonify(team=[r.serialize for r in teams])

@app.route('/')
@app.route('/teams/')
def showTeams():
    teams = session.query(Team).order_by(asc(Team.name))
    if 'username' not in login_session:
        return render_template('publicteams.html', teams=teams)
    else:
        return render_template('teams.html', teams=teams)

#Add new team
@app.route('/team/new/', methods=['GET', 'POST'])
def newTeam():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newTeam = Team(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newTeam)
        flash('New Team %s Successfully Created' % newTeam.name)
        session.commit()
        return redirect(url_for('showTeams'))
    else:
        return render_template('newteams.html')

#Edit team if you are Authorized

@app.route('/team/<int:team_id>/edit/', methods=['GET', 'POST'])
def editTeam(team_id):
    editedteam = session.query(
        Team).filter_by(id=team_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedteam.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this player. Please create your own team in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedteam.name = request.form['name']
            flash('team Successfully Edited %s' % editedteam.name)
            return redirect(url_for('showTeams'))
    else:
        return render_template('editTeam.html', team=editedteam)

#delete team if you are authorized
@app.route('/team/<int:team_id>/delete/', methods=['GET', 'POST'])
def deleteTeam(team_id):
    teamToDelete = session.query(
        Team).filter_by(id=team_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if teamToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this team. Please create your own team in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(teamToDelete)
        flash('%s Successfully Deleted' % teamToDelete.name)
        session.commit()
        return redirect(url_for('showTeams', team_id=teamToDelete))
    else:
        return render_template('deleteteam.html', team=teamToDelete)

#show player
@app.route('/team/<int:team_id>/')
@app.route('/team/<int:team_id>/player/')
def showPlayer(team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    creator = getUserInfo(team.user_id)
    players = session.query(Player).filter_by(team_id=team_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicplayers.html', players=players, team=team, creator=creator)
    else:
        return render_template('publicplayers.html', players=players, team=team, creator=creator)


#ADD New player
@app.route('/player/<int:team_id>/player/new/', methods=['GET', 'POST'])
def newPlayer(team_id):
    if 'username' not in login_session:
        return redirect('/login')
    team = session.query(Team).filter_by(id=team_id).one()
    if login_session['user_id'] != team.user_id:
        return "<script>function enzar() {alert('You are not authorized to add players to this team. Please create your own team in order to add items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        player = Player(name=request.form['name'], description=request.form['description'], price=request.form[
                               'price'], position=request.form['position'], team_id=team_id, user_id=team.user_id)
        session.add(player)
        session.commit()
        flash('New Player %s  Successfully Created' % (player.name))
        return redirect(url_for('showPlayer', team_id=team_id))
    else:
        return render_template('newplayer.html', team_id=team_id)


#Edit player if you are authorized
@app.route('/team/<int:team_id>/player/<int:player_id>/edit', methods=['GET', 'POST'])
def editPlayer(team_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedplayer = session.query(Player).filter_by(id=player_id).one()
    team = session.query(Team).filter_by(id=team_id).one()
    if login_session['user_id'] != team.user_id:
        return "<script>function enzar() {alert('You are not authorized to edit player to this team. Please create your own team in order to edit items.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedplayer.name = request.form['name']
        if request.form['description']:
            editedplayer.description = request.form['description']
        if request.form['price']:
            editedplayer.price = request.form['price']
        if request.form['position']:
            editedplayer.course = request.form['position']
        session.add(editedplayer)
        session.commit()
        flash('Player Successfully Edited')
        return redirect(url_for('showPlayer', team_id=team_id))
    else:
        return render_template('editplayer.html', team_id=team_id, player_id=player_id, player=editedplayer)

#delete player if you are authorized
@app.route('/team/<int:team_id>/player/<int:player_id>/delete', methods=['GET', 'POST'])
def deletePlayer(team_id, player_id):
    if 'username' not in login_session:
        return redirect('/login')
    team = session.query(Team).filter_by(id=team_id).one()
    playerTodelete = session.query(Player).filter_by(id=player_id).one()
    if login_session['user_id'] != team.user_id:
         return "<script>function myFunction() {alert('You are not authorized to delete  playerss to this team. Please create your own team in order to delete palayers.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(playerTodelete)
        session.commit()
        flash(' player Successfully Deleted')
        return redirect(url_for('showPlayer', team_id=team_id))
    else:
        return render_template('deleteplayer.html', player=playerTodelete)
# using gdisconnect
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showTeams'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showTeams'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8081)


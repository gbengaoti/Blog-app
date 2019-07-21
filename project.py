from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
from requests_oauthlib import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import User, Base, Article, Comments
from flask_oauth import OAuth
import json
import httplib2
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)

engine = create_engine('sqlite:///blogarticles.db')
Base.metadata.bind = engine

session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

#validate token

@app.before_request
def before_request():
    session()

@app.after_request
def close_session(response):
    session.remove()
    return(response)

#################### GOOGLE SIGN IN ########################################
GOOGLE_CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

GOOGLE_CLIENT_SECRET = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_secret']
APPLICATION_NAME = "Blog Application"

REDIRECT_URI = '/oauth2callback'  # one of the Redirect URIs from Google APIs console

oauth = OAuth()

google = oauth.remote_app('google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={'scope':  "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/plus.login https://www.googleapis.com/auth/plus.me",
    'response_type': 'code'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET)


@app.route('/')
def index():
    access_token = login_session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError

    headers = {'Authorization': 'OAuth '+access_token}
    
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
    None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            login_session.pop('access_token', None)
            return redirect(url_for('login'))
        #return res.read()
        return redirect(url_for('signin'))
    resp = res.read()
    text = json.loads(resp)
    login_session['provider'] = 'google'
    login_session['username'] = text["name"]
    login_session['email'] = text["email"]
    # see if user exists, if not create user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    print(user_id)
    flash("you are now logged in as %s" % login_session['username'])
    return redirect(url_for('users'))

@app.route('/login')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)


@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    login_session['access_token'] = access_token, ''
    return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
    return login_session.get('access_token')

@app.route('/index')
def signin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    if is_signed_in():
        username = login_session['username'] 
    else:
        username = "Bloggers world"
    return render_template('signin.html', STATE=state, signed_in=is_signed_in(), user_name=username)



#################### FACEBOOK SIGN IN ########################################

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    # <a href="https://www.facebook.com/dialog/oauth/?client_id=YOUR_APP_ID&redirect_uri=YOUR_REDIRECT_URL&state=YOUR_STATE_VALUE&scope=COMMA_SEPARATED_LIST_OF_PERMISSION_NAMES">LOGIN!</a>


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v3.3/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v3.3/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    # error checking for if user has no email address
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # see if user exists, if not create user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    return output
#################### FACEBOOK SIGN OUT########################################


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]


####################  SIGN OUT ###############################################

@app.route('/clear')
def signoutBlog():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('signin'))
    else:
        flash("You were not logged in")
        return redirect(url_for('signin'))  

def is_signed_in():
  if 'access_token' in login_session:
    return True
  else:
    return False

#################### JSON CRUD OPERATIONS ###################################

@app.route('/user/<int:user_id>/article/<int:article_id>/comments/JSON')
def commentsJSON(user_id, article_id):
    allComments = session.query(Comments).filter_by(article_id = article_id, writer_id = user_id).all()
    return jsonify(Comments=[c.serialize for c in allComments])

@app.route('/user/<int:user_id>/articles/JSON')
def articlesJSON(user_id):
    articles = session.query(Article).filter_by(user_id = user_id).all()
    return jsonify(Articles= [article.serialize for article in articles])    

@app.route('/user/<int:user_id>/article/<int:article_id>/JSON')
def articleJSON(user_id, article_id):
    try:
        article = session.query(Article).filter_by(id = article_id, user_id = user_id).one()  
    except NoResultFound as e:
        article = {}
    finally:
        if article == {}:
            return json.dumps(article)
        else:
            return jsonify(Article= article.serialize)   
    

@app.route('/users/JSON')
def usersJSON():
    # get all users
    users = session.query(User).all()
    return jsonify(Users=[user.serialize for user in users])



#################### CRUD OPERATIONS ########################################

@app.route('/users')
def users():
    users = session.query(User).all()
    if not is_signed_in():
        username = "Bloggers world"
    else:
        username = login_session['username']
    return render_template('users.html', users = users, signed_in=is_signed_in(),user_name=username)  

@app.route('/users/<int:user_id>')
def userArticles(user_id):
    # search for user by ID
    user = getUserById(user_id)
    if user != None:
        if is_signed_in():
            is_creator = (user_id == login_session['user_id'])
        else:
            is_creator = False

        if not is_signed_in():
            username = "Bloggers world"
        else:
            username = login_session['username']
        # get all articles with user ID
        articles = session.query(Article).filter_by(user_id = user_id).all()
        return render_template('user_articles.html', user = user, articles = articles, signed_in=is_signed_in(), is_creator = is_creator,user_name=username)
    else:
        abort(404)

@app.route('/user/<int:user_id>/article/<int:article_id>/view', methods=['GET','POST'])
def viewUserArticle(user_id, article_id):
    # search article by user_id and article_id
    user = getUserById(user_id)
    if user != None:
        article =  getArticle(article_id, user_id)
        # error handling - if article does not exist
        if article != None:
            allComments = session.query(Comments).filter_by(article_id = article_id, writer_id = user_id).all()
            if request.method == 'POST':
                # error handling - no empty comment should be added
                if request.form['comment'] != "":
                    newComment = Comments(comment_text = request.form['comment'], article = article, user = article)
                    session.add(newComment)
                    session.commit()
                    return redirect(url_for('viewUserArticle', user_id = user.id, article_id = article.id ))
                else:
                    flash("Comment cannot be empty")
                    return redirect(url_for('viewUserArticle', user_id = user.id, article_id = article.id ))
            else:
                return render_template('view_article.html', user = user, article = article, comments = allComments, num_comments = len(allComments), signed_in=is_signed_in())
        else:
            abort(404)
    else:
        abort(404)

@app.route('/user/<int:user_id>/article/new' , methods=['GET','POST'])
def addArticle(user_id):
    if is_signed_in() and (user_id == login_session['user_id']):
        user = getUserById(user_id)
        # make sure that only blog owner can add to her blog
        # error handling - no empty articles can be added
        if request.method == 'POST':
            if request.form['title'] == "" and request.form['body'] == "":
                flash("Cannot Add Empty Post - Try again")
                return redirect(url_for('userArticles', user_id = user_id))
            else:
                newArticle = Article(title = request.form['title'], article_body =request.form['body'], user_id = user_id)
                session.add(newArticle)
                session.commit()
                flash("New Post Added Successfully!")
                return redirect(url_for('userArticles', user_id = user_id))
        else:
            return render_template('add_article.html', user = user, signed_in=is_signed_in())
    else:
        flash("You need to be logged in to add an article")
        return redirect(url_for('userArticles', user_id = user_id))

@app.route('/user/<int:user_id>/article/<int:article_id>/edit' , methods=['GET','POST'])
def editArticle(user_id, article_id):
    if is_signed_in() and (user_id == login_session['user_id']):
        # get article from database
        user = getUserById(user_id)
        # error handling - what happens in case of invalid article_id or invalid user_id
        toEditArticle = getArticle(article_id, user_id)
        if toEditArticle != None:
            if request.method == 'POST':
                if request.form['title']:
                    toEditArticle.title = request.form['title']
                if request.form['body']:
                    toEditArticle.article_body = request.form['body']
                session.add(toEditArticle)
                session.commit()
                flash("Post Successfully Updated !")
                return redirect(url_for('viewUserArticle', user_id = user_id, article_id = article_id))
            else:
                return render_template('edit_article.html', user = user, article = toEditArticle, signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to edit an article")
        return redirect(url_for('userArticles', user_id = user_id))

@app.route('/user/<int:user_id>/article/<int:article_id>/delete'  , methods=['GET','POST'])
def deleteArticle(user_id, article_id):
    # get article
    if is_signed_in() and (user_id == login_session['user_id']):
        user = getUserById(user_id)
        # error handling - what happens in case of invalid article_id or invalid user_id
        toDeleteArticle = getArticle(article_id, user_id)
        if toDeleteArticle != None:
            if request.method == 'POST':
                session.delete(toDeleteArticle)
                session.commit()
                flash("Post Successfully Deleted")
                return redirect(url_for('userArticles', user_id = user_id))
            else:
                return render_template('delete_article.html', user = user, article = toDeleteArticle, signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to delete an article")
        return redirect(url_for('userArticles', user_id = user_id))

def createUser(login_session):
    newUser = User(user_name=login_session['username'], user_email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = getUserByEmail(login_session['email'])
    return user.id

def getArticle(article_id, user_id):
    try:
        article = session.query(Article).filter_by(id = article_id, user_id = user_id).one()
        return article
    except NoResultFound as e:
        return None

def getUserById(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except NoResultFound as e:
        return None
    
def getUserByEmail(email):
    try:
        user = session.query(User).filter_by(user_email=email).one()
        return user
    except NoResultFound as e:
        return None

def getUserID(email):
    try:
        user = session.query(User).filter_by(user_email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_blog_keys'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
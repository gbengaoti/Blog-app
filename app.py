from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import User, Base, Article, Comments
import os
import json
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
import pathlib
import requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask(__name__)
app.secret_key = 'super_secret_blog_keys'

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

engine = create_engine('sqlite:///blogarticles.db')
Base.metadata.bind = engine

session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

#################### GOOGLE SIGN IN ########################################
GOOGLE_CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secrets.json")

flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile",
                                             "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                     redirect_uri="http://127.0.0.1:5000/callback")


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in login_session:
            return abort(401)  # authorization required
        else:
            return function()

    return wrapper


@app.route('/')
def index():
    return render_template('signin.html')


@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    login_session["state"] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)
    if not login_session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID)

    login_session["google_id"] = id_info.get("sub")
    login_session["username"] = id_info.get("name")
    login_session["provider"] = 'google'
    login_session["email"] = id_info.get("email")
    return redirect("/index")


@app.route('/clear')
def logout():
    login_session.clear()
    return redirect(url_for('signin'))


def is_signed_in():
    if 'google_id' in login_session:
        return True
    else:
        return False


@app.route('/index')
def signin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    if is_signed_in():
        username = login_session['username']
        print("you are signed in, " + username)
    else:
        username = "Bloggers world"
    return render_template('signin.html', STATE=state, signed_in=is_signed_in(), user_name=username)


#################### JSON CRUD OPERATIONS ###################################

@app.route('/user/<int:user_id>/article/<int:article_id>/comments/JSON')
def commentsJSON(user_id, article_id):
    allComments = session.query(Comments).filter_by(article_id=article_id, writer_id=user_id).all()
    return jsonify(Comments=[c.serialize for c in allComments])


@app.route('/user/<int:user_id>/articles/JSON')
def articlesJSON(user_id):
    articles = session.query(Article).filter_by(user_id=user_id).all()
    return jsonify(Articles=[article.serialize for article in articles])


@app.route('/user/<int:user_id>/article/<int:article_id>/JSON')
def articleJSON(user_id, article_id):
    try:
        article = session.query(Article).filter_by(id=article_id, user_id=user_id).one()
    except NoResultFound as e:
        article = {}
    finally:
        if article == {}:
            return json.dumps(article)
        else:
            return jsonify(Article=article.serialize)


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
    return render_template('users.html', users=users, signed_in=is_signed_in(), user_name=username)


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
        articles = session.query(Article).filter_by(user_id=user_id).all()
        return render_template('user_articles.html', user=user, articles=articles, signed_in=is_signed_in(),
                               is_creator=is_creator, user_name=username)
    else:
        abort(404)


@app.route('/user/<int:user_id>/article/<int:article_id>/view', methods=['GET', 'POST'])
def viewUserArticle(user_id, article_id):
    # search article by user_id and article_id
    user = getUserById(user_id)
    if user != None:
        article = getArticle(article_id, user_id)
        # error handling - if article does not exist
        if article != None:
            allComments = session.query(Comments).filter_by(article_id=article_id, writer_id=user_id).all()
            if request.method == 'POST':
                # error handling - no empty comment should be added
                if request.form['comment'] != "":
                    newComment = Comments(comment_text=request.form['comment'], article=article, user=article)
                    session.add(newComment)
                    session.commit()
                    return redirect(url_for('viewUserArticle', user_id=user.id, article_id=article.id))
                else:
                    flash("Comment cannot be empty")
                    return redirect(url_for('viewUserArticle', user_id=user.id, article_id=article.id))
            else:
                return render_template('view_article.html', user=user, article=article, comments=allComments,
                                       num_comments=len(allComments), signed_in=is_signed_in())
        else:
            abort(404)
    else:
        abort(404)


@app.route('/user/<int:user_id>/article/new', methods=['GET', 'POST'])
def addArticle(user_id):
    if is_signed_in() and (user_id == login_session['user_id']):
        user = getUserById(user_id)
        # make sure that only blog owner can add to her blog
        # error handling - no empty articles can be added
        if request.method == 'POST':
            if request.form['title'] == "" and request.form['body'] == "":
                flash("Cannot Add Empty Post - Try again")
                return redirect(url_for('userArticles', user_id=user_id))
            else:
                newArticle = Article(title=request.form['title'], article_body=request.form['body'], user_id=user_id)
                session.add(newArticle)
                session.commit()
                flash("New Post Added Successfully!")
                return redirect(url_for('userArticles', user_id=user_id))
        else:
            return render_template('add_article.html', user=user, signed_in=is_signed_in())
    else:
        flash("You need to be logged in to add an article")
        return redirect(url_for('userArticles', user_id=user_id))


@app.route('/user/<int:user_id>/article/<int:article_id>/edit', methods=['GET', 'POST'])
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
                return redirect(url_for('viewUserArticle', user_id=user_id, article_id=article_id))
            else:
                return render_template('edit_article.html', user=user, article=toEditArticle, signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to edit an article")
        return redirect(url_for('userArticles', user_id=user_id))


@app.route('/user/<int:user_id>/article/<int:article_id>/delete', methods=['GET', 'POST'])
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
                return redirect(url_for('userArticles', user_id=user_id))
            else:
                return render_template('delete_article.html', user=user, article=toDeleteArticle,
                                       signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to delete an article")
        return redirect(url_for('userArticles', user_id=user_id))


def createUser(login_session):
    newUser = User(user_name=login_session['username'], user_email=login_session[
        'email'])
    session.add(newUser)
    session.commit()
    user = getUserByEmail(login_session['email'])
    return user.id


def getArticle(article_id, user_id):
    try:
        article = session.query(Article).filter_by(id=article_id, user_id=user_id).one()
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
    app.run('localhost', 5000, debug=True)

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import User, Base, Article, Comments
import os
import json
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
import requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests
from pkg_resources import resource_filename

app = Flask(__name__)
app.secret_key = 'super_secret_blog_keys'

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

engine = create_engine('sqlite:///blog-articles.db')
Base.metadata.bind = engine

session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

# GOOGLE SIGN IN
secrets_filepath = resource_filename('flaskr', 'resources/client_secrets.json')

GOOGLE_CLIENT_ID = json.loads(
    open(secrets_filepath, 'r').read())['web']['client_id']

# client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "flaskr.client_secrets.json")

flow = Flow.from_client_secrets_file(client_secrets_file=secrets_filepath,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile",
                                             "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                     redirect_uri="http://127.0.0.1:5000/callback")


def login_is_required(function):
    def wrapper():
        if "google_id" not in login_session:
            return abort(401)  # authorization required
        else:
            return function()

    return wrapper


@app.route('/')
def index():
    if is_signed_in():
        return render_template('index.html', STATE=login_session['state'], signed_in=is_signed_in(),
                        user_name=login_session["username"])
    else:
        return render_template('index.html')


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
    # see if user exists, if not create user
    user_id = get_user_id(login_session["email"])
    if not user_id:
        user_id = create_user()
    login_session['user_id'] = user_id
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(32))
    login_session['state'] = state
    return render_template('index.html', STATE=login_session['state'], signed_in=is_signed_in(), user_name=login_session["username"])

@app.route('/clear')
def logout():
    login_session.clear()
    return redirect(url_for('index'))


def is_signed_in():
    if 'google_id' in login_session:
        return True
    else:
        return False


# JSON CRUD OPERATIONS

@app.route('/user/<int:user_id>/article/<int:article_id>/comments/JSON')
def comments_json(user_id, article_id):
    all_comments = session.query(Comments).filter_by(article_id=article_id, writer_id=user_id).all()
    return jsonify(Comments=[c.serialize for c in all_comments])


@app.route('/user/<int:user_id>/articles/JSON')
def articles_json(user_id):
    articles = session.query(Article).filter_by(user_id=user_id).all()
    return jsonify(Articles=[article.serialize for article in articles])


@app.route('/user/<int:user_id>/article/<int:article_id>/JSON')
def article_json(user_id, article_id):
    article = {}
    try:
        article = session.query(Article).filter_by(id=article_id, user_id=user_id).one_or_none()
    finally:
        if article == None:
            return json.dumps(article)
        else:
            return jsonify(Article=article.serialize)


@app.route('/users/JSON')
def users_json():
    # get all users
    all_users = session.query(User).all()
    return jsonify(Users=[user.serialize for user in all_users])


# CRUD OPERATIONS

@app.route('/users')
def users():
    try:
        all_users = session.query(User).all()
    except NoResultFound:
        all_users = {}
    if not is_signed_in():
        username = "Bloggers world"
    else:
        username = login_session['username']
    return render_template('users.html', users=all_users, signed_in=is_signed_in(), user_name=username)


@app.route('/users/<int:user_id>')
def user_articles(user_id):
    # search for user by ID
    user = get_user_by_id(user_id)
    if user is not None:
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
def view_user_article(user_id, article_id):
    # search article by user_id and article_id
    user = get_user_by_id(user_id)
    if user is not None:
        article = get_article(article_id, user_id)
        # error handling - if article does not exist
        if article is not None:
            all_comments = get_article_comments(article_id, user_id)
            if request.method == 'POST':
                # error handling - no empty comment  should be added
                if request.form['comment'] != "":
                    new_comment = Comments(comment_text=request.form['comment'], article=article, user=article)
                    session.add(new_comment)
                    session.commit()
                    return redirect(url_for('view_user_article', user_id=user.id, article_id=article.id))
                else:
                    flash("Comment cannot be empty")
                    return redirect(url_for('view_user_article', user_id=user.id, article_id=article.id))
            else:
                return render_template('view_article.html', user=user, article=article, comments=all_comments,
                                       num_comments=len(all_comments), signed_in=is_signed_in())
        else:
            abort(404)
    else:
        abort(404)


@app.route('/user/<int:user_id>/article/new', methods=['GET', 'POST'])
def add_article(user_id):
    if is_signed_in() and (user_id == login_session['user_id']):
        user = get_user_by_id(user_id)
        # make sure that only blog owner can add to her blog
        # error handling - no empty articles can be added
        if request.method == 'POST':
            if request.form['title'] == "" and request.form['body'] == "":
                flash("Cannot Add Empty Post - Try again")
                return redirect(url_for('user_articles', user_id=user_id))
            else:
                new_article = Article(title=request.form['title'], article_body=request.form['body'], user_id=user_id)
                session.add(new_article)
                session.commit()
                flash("New Post Added Successfully!")
                return redirect(url_for('user_articles', user_id=user_id))
        else:
            return render_template('add_article.html', user=user, signed_in=is_signed_in())
    else:
        flash("You need to be logged in to add an article")
        return redirect(url_for('user_articles', user_id=user_id))


@app.route('/user/<int:user_id>/article/<int:article_id>/edit', methods=['GET', 'POST'])
def edit_article(user_id, article_id):
    if is_signed_in() and (user_id == login_session['user_id']):
        # get article from database
        user = get_user_by_id(user_id)
        # error handling - what happens in case of invalid article_id or invalid user_id
        to_edit_article = get_article(article_id, user_id)
        if to_edit_article is not None:
            if request.method == 'POST':
                if request.form['title']:
                    to_edit_article.title = request.form['title']
                if request.form['body']:
                    to_edit_article.article_body = request.form['body']
                session.add(to_edit_article)
                session.commit()
                flash("Post Successfully Updated !")
                return redirect(url_for('view_user_article', user_id=user_id, article_id=article_id))
            else:
                return render_template('edit_article.html', user=user,
                                       article=to_edit_article, signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to edit an article")
        return redirect(url_for('user_articles', user_id=user_id))


@app.route('/user/<int:user_id>/article/<int:article_id>/delete', methods=['GET', 'POST'])
def delete_article(user_id, article_id):
    # get article
    if is_signed_in() and (user_id == login_session['user_id']):
        user = get_user_by_id(user_id)
        # error handling - what happens in case of invalid article_id or invalid user_id
        to_delete_article = get_article(article_id, user_id)
        to_delete_article_comments = get_article_comments(article_id, user_id)

        if to_delete_article is not None:
            if request.method == 'POST':
                session.delete(to_delete_article)
                session.commit()
                # delete comments on post too
                for comment in to_delete_article_comments:
                    session.delete(comment)
                session.commit()
                flash("Post Successfully Deleted")
                return redirect(url_for('user_articles', user_id=user_id))
            else:
                return render_template('delete_article.html', user=user, article=to_delete_article,
                                       signed_in=is_signed_in())
        else:
            abort(404)
    else:
        flash("You need to be logged in to delete an article")
        return redirect(url_for('userArticles', user_id=user_id))


def create_user():
    new_user = User(user_name=login_session['username'], user_email=login_session[
        'email'])
    session.add(new_user)
    session.commit()
    user = get_user_by_email(login_session['email'])
    return user.id


def get_article(article_id, user_id):
    article = session.query(Article).filter_by(id=article_id, user_id=user_id).one_or_none()
    return article

def get_article_comments(article_id, user_id):
    try:
        all_comments = session.query(Comments).filter_by(article_id=article_id, writer_id=user_id).all()
        return all_comments
    except NoResultFound:
        return None

def get_user_by_id(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user



def get_user_by_email(email):
    user = session.query(User).filter_by(user_email=email).one_or_none()
    return user



def get_user_id(email):
    user = session.query(User).filter_by(user_email=email).one_or_none()
    return user.id


if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)

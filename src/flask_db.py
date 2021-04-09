from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for
from flask import make_response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import requests
import json

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
app.config['SECRET_KEY'] = 'aec7739f166a5672707231bf2012d3c2cd2c79ea98d94f905689422dbf303b3132106ce345618566'

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    vkid = db.Column(db.String(100), unique=True, nullable=True)
    vkaccesstoken = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<users self.name>'

@app.route("/")
def index_page():

    if session.get('user_id'):
        return redirect(url_for('profile'))

    return render_template("index.html")

@app.route("/register_email", methods=("POST", "GET"))
def register_email():

    if request.method == 'POST':
        try:
            email = request.form['InputEmail']
            name = request.form['InputName']
            hash = generate_password_hash(request.form['InputPassword'])

            user = Users(email=email, password=hash, name=name)
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            print (error)
            print ("Ошибка при добавлении пользователя в БД")

    return redirect(url_for('index_page'))

@app.route('/login_email', methods=('GET', 'POST'))
def login_email():

    if request.method == 'POST':
        email = request.form['email']

        user = Users.query.filter_by(email=email).first()

        # Check email exist
        if user is None:
            return redirect(url_for('index_page'))

        # Check for password
        if not check_password_hash(user.password, request.form['password']):
            return redirect(url_for('index_page'))

    session['user_id'] = user.id
    return redirect(url_for('profile'))

@app.route("/profile")
def profile():

    if not session.get('user_id'):
        return redirect(url_for('index_page'))

    user = Users.query.filter_by(id=session.get('user_id')).first()

    return render_template("profile.html", user=user)

@app.route("/cookie_test")
def cookie_test():
    cookie = ""

    if request.cookies.get("cookie_test"):
        cookie = request.cookies.get("cookie_test")

    res = make_response(render_template('cookie_test.html', cookies=cookie))

    res.set_cookie("cookie_test", "yes")
    return res

@app.route("/visits")
def visits():

    if "visit" in session:
        session['visit'] = session.get('visit') + 1
    else:
        session['visit'] = 1

    return render_template("session.html", visits=session['visit'])

@app.route("/logout")
def logout():

    if not session.get('user_id'):
        return redirect(url_for('index_page'))

    session.pop('user_id', None)
    return redirect(url_for('index_page'))

# https://vk.com/dev/authcode_flow_user
@app.route("/vk_callback")
def vk_callback():

    user_code = request.args.get('code')

    if not user_code:
        return redirect(url_for('index_page'))

    # Get access token
    response = requests.get('https://oauth.vk.com/access_token?client_id=7811257&client_secret=auqCCtt2EF2wl16MyfkF&redirect_uri=http://127.0.0.1:5000/vk_callback&code=' + user_code)
    access_token_json = json.loads(response.text)

    if "error" in access_token_json:
        return redirect(url_for('index_page'))

    vk_id = access_token_json['user_id']
    access_token = access_token_json['access_token']

    # Get user name
    response = requests.get('https://api.vk.com/method/users.get?user_ids=' + str(vk_id) + '&fields=bdate&access_token=' + str(access_token) + '&v=5.130')
    vk_user = json.loads(response.text)

    print (vk_user)

    user = Users.query.filter_by(vkid=vk_id).first()

    # New user?
    if user is None:
        # Yes
        try:
            name = vk_user['response'][0]['first_name'] + " " + vk_user['response'][0]['last_name']
            new_user = Users(name=name, vkid=vk_id, vkaccesstoken=access_token)
            db.session.add(new_user)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            print(error)
            print("Ошибка при добавлении пользователя в БД")
            return redirect(url_for('index_page'))

        user = Users.query.filter_by(vkid=vk_id).first()

    session['user_id'] = user.id
    return redirect(url_for('index_page'))

@app.route("/vk_callback2")
def vk_callback2():

    user_code = request.args.get('code')

    if not user_code:
        return redirect(url_for('index_page'))

    # Get access token
    response = requests.get('https://oauth.vk.com/access_token?client_id=7809874&client_secret=s8XWVxUjChP5zGYgwz2y&redirect_uri=http://127.0.0.1:5000/vk_callback&code=' + user_code)
    access_token_json = json.loads(response.text)

    if "error" in access_token_json:
        return redirect(url_for('index_page'))

    vk_id = access_token_json['user_id']
    access_token = access_token_json['access_token']

    # Get user name
    response = requests.get('https://api.vk.com/method/users.get?user_ids=' + str(vk_id) + '&fields=bdate&access_token=' + str(access_token) + '&v=5.130')
    vk_user = json.loads(response.text)

    user = Users.query.filter_by(vkid=vk_id).first()

    # New user?
    if user is None:

        # Yes
        try:
            name = vk_user['response'][0]['first_name'] + " " + vk_user['response'][0]['last_name']
            new_user = Users(name=name, vkid=vk_id, vkaccesstoken=access_token)
            db.session.add(new_user)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            print(error)
            print("Ошибка при добавлении пользователя в БД")
            return redirect(url_for('index_page'))

        user = Users.query.filter_by(vkid=vk_id).first()

    session['user_id'] = user.id
    return redirect(url_for('profile'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)

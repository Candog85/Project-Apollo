# All imports
from flask import Flask, render_template, request
import pymysql
from dynaconf import Dynaconf
import flask_login
import requests
import csv
import json

# Declare Flask application
app = Flask(__name__)


# Config settings and secrets
conf = Dynaconf(
    settings_file = ["settings.toml"]
)


app.secret_key = conf.secret_key

# Establish database connection
def connect_db():
    """Connect to the phpMyAdmin database (LOCAL STEAM NETWORK ONLY)"""
    conn = pymysql.connect(
        host = "db.steamcenter.tech",
        database = "apollo",
        user = conf.user,
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn

# User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view=("/login")

# Classes
class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, first_name, last_name):
        self.id = user_id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self):
        return str(self.id)
    
# Load User Session
@login_manager.user_loader
def load_user(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `user` WHERE `id` = {id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close
    if result is not None:
        return User(result["id"], result["username"], result["email"], result["name"])

# Homepage initialization
@app.route("/")
def test_fetch():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `test`;")
    pulled = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("homepage.html.jinja", testers = pulled)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/getdata')
def get_data():
    colleges = []
    for page in range(0,1):
        response=requests.get(f"https://api.data.gov/ed/collegescorecard/v1/schools?api_key=fEZsVdtKgtVU4ODIpjHcP8vDttDK0ftSGZaWDcAk&fields=school.name,latest.cost.attendance.academic_year&page=1&per_page={page}")

        results = response.json()['results']

        colleges.extend(results)

    for college in colleges:

        name=college["school.name"]
        tuition=college["latest.cost.attendance.academic_year"]


        conn = connect_db()
        cursor = conn.cursor()

        request.path

        cursor.execute(f"""

        INSERT INTO `Colleges` (`name`, `tuition`)
        VALUES ('{name}', '{tuition}')
                            
                            """)
    return
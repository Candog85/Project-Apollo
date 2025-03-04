# All imports
from flask import Flask, render_template, request, redirect, flash

import pymysql
from dynaconf import Dynaconf
import flask_login
import requests

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

        # ALL VARIABLES MUST BE CONFIGURED DYNAMICALLY AND SECRETLY VIA settings.toml
        host = conf.host,
        database = conf.db,
        user = conf.user,
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn

# Homepage initialization
@app.route("/")
def homepage():
    return render_template("homepage.html.jinja")

if __name__ == '__main__':
    app.run(debug=True)

# User account system
## User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view=("/sign_in")

## Define user class
class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, name, username, email):
        self.id = user_id
        self.name = name
        self.username = username
        self.email = email

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


    conn.close
    if user_result is not None:
        return User(user_result["id"], user_result["name"], user_result["username"], user_result["email"])
    
## Signup page
@app.route("/sign_up", methods=["POST", "GET"])
def signup_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["pass"]
        confirm_password = request.form["confpass"]
        conn = connect_db()
        cursor = conn.cursor()
        if len(username.strip()) > 20:
            flash("Username must be 20 characters or less.")
        else:
            if len(password.strip()) < 8:
                flash("Password must be 8 characters or longer.")
            else:
                if password != confirm_password:
                    flash("Passwords do not match.")
                else:
                    try:
                        cursor.execute(f"""
                            
                        """)
                    except pymysql.err.IntegrityError:
                        flash("Username or email is already in use.")
                    else:
                        return redirect("/sign_in")
                    finally:
                        cursor.close()
                        conn.close()
    return render_template("sign_up.html.jinja")

## Sign in page
@app.route("/sign_in", methods=["POST", "GET"])
def login_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username = request.form["userVer"].strip()
        password = request.form["passVer"]
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `user` WHERE `username` = '{username}';")
        result = cursor.fetchone()
        
        if result is None:
            flash("Your username and/or password is incorrect.")
        elif password != result["password"]:
            flash("Your username and/or password is incorrect.")
        else:
            user = User(result["id"], result["username"], result["email"], result["name"])
            # Log user in
            flask_login.login_user(user)
            return redirect("/")
        cursor.close()
        conn.close()
    return render_template("sign_in.html.jinja")

# Browse colleges
@app.route("/browse")
def college_browse():
    query = request.args.get("query")
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `College`;")
    colleges = cursor.fetchall()
    return render_template("browse.html.jinja", results = colleges)

# Search system
def requestinfo(schoolname='', schoolstate=''):
    count = 0
    api="https://api.data.gov/ed/collegescorecard/v1/schools?api_key=fEZsVdtKgtVU4ODIpjHcP8vDttDK0ftSGZaWDcAk"
    queries={}
    request=''
    if schoolname:
        queries.update({"school.name":(f"{schoolname}")})
    
    if schoolstate:
        queries.update({"school.state":(f"{schoolstate}")})
=======
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




    test= requests.get(request).json()

        conn = connect_db()
        cursor = conn.cursor()

        request.path


        cursor.execute(f"""

        INSERT INTO `Colleges` (`name`, `tuition`)
        VALUES ('{name}', '{tuition}')
                            
                            """)
    return
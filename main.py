# All imports
from flask import Flask, render_template, request, redirect, flash
import pymysql
from dynaconf import Dynaconf
import flask_login

# Declare Flask application
app = Flask(__name__)

# Config settings and secrets
conf = Dynaconf(settings_file=["settings.toml"])
app.secret_key = conf.secret_key

# Establish database connection
def connect_db():
    """Connect to the phpMyAdmin database (LOCAL STEAM NETWORK ONLY)"""
    return pymysql.connect(
        host=conf.host,
        database=conf.db,
        user=conf.user,
        password=conf.password,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

# Homepage initialization
@app.route("/")
def homepage():
    return render_template("homepage.html.jinja")

# User account system
## User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/sign_in"

## Define user class
class User(flask_login.UserMixin):
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
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `User` WHERE `id` = %s", (id,))
            result = cursor.fetchone()
            if result:
                return User(result["id"], result["first_name"], result["username"], result["email"])
    finally:
        conn.close()
    return None

## Signup page
@app.route("/sign_up", methods=["POST", "GET"])
def signup_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    
    if request.method == "POST":
        # Declare form fields
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        zip_code = request.form["zip_code"]
        
        # Username/password validation
        if len(username.strip()) > 20:
            flash("Username must be 20 characters or less.")
        elif len(password.strip()) < 8:
            flash("Password must be 8 characters or longer.")
        elif password != confirm_password:
            flash("Passwords do not match.")
        else:
            try:
                conn = connect_db()
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO `User` (`username`, `password`, `first_name`, `last_name`, `email`, `zip_code`)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (username, password, first_name, last_name, email, zip_code))
                    conn.commit()
                    return redirect("/sign_in")
            except pymysql.MySQLError:
                flash("Username or email is already in use. Please use a different one.")
            finally:
                conn.close()
    return render_template("sign_up.html.jinja")

## Sign in page
@app.route("/sign_in", methods=["POST", "GET"])
def login_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        
        conn = connect_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM `User` WHERE `username` = %s", (username,))
                result = cursor.fetchone()
                if result and password == result["password"]:
                    user = User(result["id"], result["first_name"], result["username"], result["email"])
                    flask_login.login_user(user)
                    return redirect("/")
                flash("Your username and/or password is incorrect.")
        finally:
            conn.close()
    return render_template("sign_in.html.jinja")

# Analytics page (college and user graphs for comparison and analysis)
@app.route("/analytics")
def analytics_page():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `Graphs`;")
            graphs = cursor.fetchall()
    finally:
        conn.close()
    return render_template("analytics.html.jinja", results=graphs)

# Settings page for user preferences
@app.route("/settings", methods=["POST", "GET"])
@flask_login.login_required
def user_input():
    customer_id = flask_login.current_user.id
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `User` WHERE `id` = %s", (customer_id,))
            results = cursor.fetchone()
            if results:
                results['sat_score'] = results.get('sat_score', 0)
                results['tuition_budget'] = results.get('tuition_budget', 0)
                results['population_preferences'] = results.get('population_preferences', 0)
                results['tuition_budget'] = f"${results['tuition_budget']:,d}"
                results['population_preferences'] = f"{results['population_preferences']:,d}"
    finally:
        conn.close()
    return render_template("settings.html.jinja", results=results)

@app.route("/settings/update", methods=["POST", "GET"])
@flask_login.login_required
def update():
    customer_id = flask_login.current_user.id
    conn = connect_db()
    try:
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect("/settings")
        
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        zip_code = int(request.form["zip_code"])
        sat_score = int(request.form["sat_score"])
        tuition_budget = int(request.form["tuition_budget"].replace(",", "").replace("$", ""))
        population_preferences = int(request.form["population_preferences"].replace(",", ""))
        
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE `User` 
                SET `username` = %s, `password` = %s, `first_name` = %s, `last_name` = %s, 
                    `email` = %s, `zip_code` = %s, `sat_score` = %s, `tuition_budget` = %s, 
                    `population_preferences` = %s
                WHERE `id` = %s;
            """, (username, password, first_name, last_name, email, zip_code, sat_score, tuition_budget, population_preferences, customer_id))
            conn.commit()
        
        flash("Settings updated successfully", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        conn.close()
    return redirect("/settings")

# Log out
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect('/')

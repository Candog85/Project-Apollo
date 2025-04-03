# All imports
from flask import Flask, render_template, request, redirect, flash, Response
import pymysql
from dynaconf import Dynaconf
import flask_login
import requests
import io
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from math import radians, cos, sin, asin, sqrt
import matplotlib.pyplot as plt
import base64

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
    cursor.execute(f"SELECT * FROM `User` WHERE `id` = {id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close
    if result is not None:
        return User(result["id"], result["username"], result["first_name"], result["last_name"])


    conn.close
    if result is not None:
        return User(result["id"], result["name"], result["username"], result["email"])
    
## Signup page
@app.route("/sign_up", methods=["POST", "GET"])
def signup_page():
    
    
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    
    
    if request.method == "POST":
        
        username = request.form["username"]
        
        password = request.form["password"]
        
        first_name = request.form["first_name"]
        
        last_name = request.form["last_name"]
        
        
        password = request.form["password"]
        
        first_name = request.form["first_name"]
        
        last_name = request.form["last_name"]
        
        email = request.form["email"]
        
        zip_code = request.form["zip_code"]
        
        confirm_password = request.form["confirm_password"]
        
        
        zip_code = request.form["zip_code"]
        
        confirm_password = request.form["confirm_password"]
        
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
                        
                        INSERT INTO `User`
                        (`username`, `password`, `first_name`, `last_name`, `email`, `zip_code`)
                        VALUES
                        (%s, %s, %s, %s, %s, %s)
                        """,(username, password, first_name, last_name, email, zip_code))
                    except pymysql.err.IntegrityError:
                        flash("Username or email is already in use.")
                    else:
                        return redirect("/sign_in")
                    finally:
                        cursor.close()
                        conn.close()
    return redirect("/#sign_up")

## Sign in page
@app.route("/sign_in", methods=["POST", "GET"])
def login_page():
    if flask_login.current_user.is_authenticated:
        print('Redirect ran')
        return redirect("/")
    if request.method == "POST":
        username = request.form["username"].strip()
        print(username)
        password = request.form["password"]
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `User` WHERE `username` = '{username}';")
        result = cursor.fetchone()
        
        if result is None:
            flash("Your username and/or password is incorrect.")
        elif password != result["password"]:
            flash("Your username and/or password is incorrect.")
        else:
            user = User(result["id"], result["username"], result["first_name"], result["last_name"] )
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

# Analytics page (college and user graphs for comparison and analysis)
@app.route("/analytics", methods=["Post", "GET"])
def analytics_page():

    #Browse area
    page = int(request.args.get('page', '1'))
    query = request.args.get('query')
    
    customer_id=flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()
    
    if query==None:
       cursor.execute(f"""
        
        SELECT * FROM `Colleges`
        LIMIT 16 OFFSET %s
        
        """,((page-1) * 16))
    
    else:
        cursor.execute(f"""
        
        SELECT * FROM `Colleges`
        WHERE `name` LIKE '%{query}%'
        LIMIT 16 OFFSET {(page-1) * 16}
        
        """)
    
    colleges=cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("analytics.html.jinja", colleges=colleges, page=page, query=query, customer_id=customer_id)
    # Note: For now, the database connection and data fetcher are placeholders. This WILL be changed later as neccessary.  

@app.route('/plot')
def create_figure():
    #Constant id (change to dynamic later)
    customer_id=flask_login.current_user.id

    #Settings for which graph to generate (will change dynamically)
    comparing_catagory=2


    compare_sat=False
    compare_tuition=False
    compare_distance=False

    if comparing_catagory==0:
        compare_sat=True
        
    elif comparing_catagory==1:
        compare_tuition=True
        
    elif comparing_catagory==2:
        compare_distance=True

    if compare_sat==True:
        comparing="Student SAT Score vs College SAT Admission Requirements"
        
    elif compare_tuition==True:
        comparing="Student Tuition Budget vs Average College Tuition"

    elif compare_distance==True:
        comparing="Distance between Colleges and User's Zip Code"
        


    #Database connection
    conn = connect_db()
    cursor=conn.cursor()

    #Selects college info from every college on the user's list
    cursor.execute(f"""

    SELECT `name`, `tuition`, `admission_rate`, `average_sat`, `size`, `city`, `state`, `longitude`, `latitude`
    FROM `CollegeList`
    LEFT JOIN `Colleges`
    ON `CollegeList`.`college_id` = `Colleges`.`id`
    AND `CollegeList`.`user_id`= %s 
           """,(customer_id))

    #Stores college results
    college_results=cursor.fetchall()

    #Selects user's info based on their id
    cursor.execute(f"""
                    
    SELECT `first_name`, `sat_score`, `tuition_budget`, `zip_code`
    FROM `User`
    WHERE `id` = %s  
                    
                    """,(customer_id))

    #Stores user info, then converts into a single dictionary
    student_results=cursor.fetchall()
    student_results=student_results[0]

    if compare_distance==True:
        names=[]
        
    else:
        #Initializes name list with first index being the user's name
        names=[student_results['first_name']]



    #If each setting is selected, data list is set to the selected data comparisor
    if compare_sat==True:
        data=[student_results['sat_score']]

    elif compare_tuition==True:
        data=[student_results['tuition_budget']]

    if compare_distance==True:
        data=[]

    print(college_results)

    for college in college_results:
        names.append(college["name"])

        if compare_sat==True:
            if college["average_sat"]==None:
                data.append(0)
            else:
                data.append(college["average_sat"])

        elif compare_tuition==True:
            if college["tuition"]==None:
                data.append(0)
            else:
                data.append(college['tuition'])
                
        elif compare_distance==True:
            
            cursor.execute(f"""
                        
            SELECT `lat`, `lng`
            FROM `Locations`
            WHERE `zip` = %s               
                        
                        """, (student_results['zip_code']))
            
            student_coordinates=cursor.fetchone()
            
            def haversine(lon1, lat1, lon2, lat2):
                """
                Calculate the great circle distance in kilometers between two points 
                on the earth (specified in decimal degrees)
                """
                # convert decimal degrees to radians 
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

                # haversine formula 
                dlon = lon2 - lon1 
                dlat = lat2 - lat1 
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a)) 
                r = 3956 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
                return c * r
            
            print(college_results)
            print(student_coordinates)
            
            print(college['longitude'])
            print(college['latitude'])
            
            data.append(int(haversine(student_coordinates['lng'], student_coordinates['lat'], college['longitude'], college['latitude'])))


    fig=plt.figure(figsize=(10, 6), facecolor='#202020', edgecolor='#DEB64B')

    bar=plt.bar(names,data, color='#DEB64B', edgecolor='#202020', )
    plt.title(f"{comparing}")

    bar[0].set_color('#202020')
    bar[0].set_edgecolor('#DEB64B')

    ax=plt.gca()

    ax.set_facecolor('#202020')

    ax.spines['top'].set_color('#DEB64B')
    ax.spines['right'].set_color('#DEB64B')
    ax.spines['bottom'].set_color('#DEB64B')
    ax.spines['left'].set_color('#DEB64B')

    ax.tick_params(axis='x', colors='#DEB64B')

    ax.tick_params(axis='y', colors='#DEB64B')

    plt.xticks(rotation=320, ha='left')

    if compare_tuition==True:
        ax.yaxis.set_major_formatter('${x:,.0f}')
        
    plt.tight_layout()
        
    plt.savefig(f'static/images/plots/{customer_id}.png',dpi=100)
    
    return redirect('/analytics')

@app.route("/college/<college_id>", methods=["POST", "GET"])
def college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""
                   
    SELECT * from `Colleges`
    WHERE `id` = %s
                   
                   """,(college_id))  
    
    college=cursor.fetchone()
    
    if college['tuition']==None:
        college['tuition']="N/A"
    else:
        college['tuition']=f"${college['tuition']:,.2f}"
    
    if college['admission_rate']==None:
        college['admission_rate']="N/A"
    else:
        college['admission_rate']=(f"{college['admission_rate']*100}%")
        
    college['size']=f"{college['size']:,}"
    
    cursor.execute(f"""
                   
    SELECT * from `CollegeList`
    WHERE `user_id`={customer_id} AND `college_id`={college_id}            
                   """)
    
    added=cursor.fetchall()
    
    if added==():
        added=False
    else:
        added=True    
    
    return render_template("college.html.jinja", college_id=college_id, college=college, added=added)

@app.route("/college/<college_id>/add", methods=["POST", "GET"])
def add_college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""
                   
    INSERT INTO `CollegeList` (`user_id`, `college_id`)
    VALUES (%s, %s)
                   
                   """,(customer_id, college_id))
    
    return redirect(f"/college/{college_id}")

@app.route("/college/<college_id>/remove", methods=["POST", "GET"])
def remove_college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""
                   
    DELETE FROM `CollegeList`
    WHERE `user_id`= {customer_id} AND `college_id`= {college_id}
                   
                   """)
    
    return redirect(f"/college/{college_id}")

# User input on settings page
@app.route("/settings", methods=["POST", "GET"])
@flask_login.login_required
def settings():
    
    customer_id=flask_login.current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""
                   
    SELECT * 
    FROM `User`
    WHERE `id` = %s               


    """, (customer_id))
    
    results=cursor.fetchall()
    
    results=results[0]
    
    print(results)
    
    if results['sat_score']==None:
        results['sat_score']=0
    
    if results['tuition_budget']==None:
        results['tuition_budget']=0
    
    if results['population_preferences']==None:
        results['population_preferences']=0
    
    results['tuition_budget']=(f"${results['tuition_budget']:,d}")
    
    results['population_preferences']=(f"{results['population_preferences']:,d}")
    
    return render_template("settings.html.jinja", results=results)

@app.route("/settings/update", methods=["POST", "GET"])
@flask_login.login_required
def update():

    customer_id=flask_login.current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        
        username = request.form["username"]
        
        password = request.form["password"]
    
        confirm_password = request.form["confirm_password"]
        
        
        if password!=confirm_password:
            flash("Passwords do not match!", "error")
            return redirect("/settings")
        
        
        first_name = request.form["first_name"]
        
        last_name = request.form["last_name"]
        
        email = request.form["email"]
        
        zip_code = int(request.form["zip_code"])
        
        sat_score = int(request.form["sat_score"])
    
        tuition_budget = int(request.form["tuition_budget"].replace(",","").replace("$",""))  
    
        population_preferences = int(request.form["population_preferences"].replace(",",""))
    
        cursor.execute("""
                    
        UPDATE `User` 
        SET `username`= %s, 
            `password`=%s, 
            `first_name`=%s, 
            `last_name`=%s, 
            `email`=%s, 
            `zip_code`=%s, 
            `sat_score`=%s, 
            `tuition_budget`=%s, 
            `population_preferences`=%s
        WHERE id = %s;              
                    
        """, (username, password, first_name, last_name, email, zip_code, sat_score, tuition_budget, population_preferences, customer_id))
        
        flash("Settings updated succesfully", "success")
    
    except:
        flash("One or more of your fields are invalid!", 'error')
    
    return redirect("/settings")

# Log out
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect('/')
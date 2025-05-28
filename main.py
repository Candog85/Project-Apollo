# All imports
from flask import Flask, render_template, request, redirect, flash, Response, session
import pymysql
from dynaconf import Dynaconf
import flask_login
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from math import radians, cos, sin, asin, sqrt
import io
from datetime import datetime
import math

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


if __name__ == '__main__':
    app.run(debug=True)

# User account system
## User Login Manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = ("/sign_in")

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
    
# Homepage initialization
@app.route("/")
def homepage():

    user=None
    empty=None

    if flask_login.current_user.is_anonymous==False:

        customer_id=flask_login.current_user.id
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * 
            FROM `User` 
            WHERE `id` = %s 
    """,(customer_id))

        user=cursor.fetchone()

        user_parameters=[user['zip_code'], user['sat_score'], user['tuition_budget'], user['population_preferences']]

        empty=False

        for parameter in user_parameters:
            if parameter==None:
                empty=True


    return render_template("homepage.html.jinja", now=datetime.now(), user=user, empty=empty)
    
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

# Browse Colleges
@app.route("/browse/<page>", methods=["GET"])
@flask_login.login_required
def browse(page):
    customer_id = flask_login.current_user.id
    page = int(page)
    conn = connect_db()
    cursor = conn.cursor()

    # Get current filters from session
    filters = session.get("filters", {})
    query = filters.get("query", "") # Get query from filters

    sql = "SELECT * FROM `Colleges` WHERE 1=1"
    params = []
    sql_parts = []

    if query:
        sql_parts.append("`name` LIKE %s")
        params.append(f"%{query}%")

    # Apply filters
    def add_range(col, min_val_key, max_val_key, factor=1):
        min_val = filters.get(min_val_key)
        max_val = filters.get(max_val_key)
        if min_val:
            try:
                sql_parts.append(f"`{col}` >= %s")
                params.append(float(min_val) * factor)
            except ValueError:
                pass # Ignore invalid input
        if max_val:
            try:
                sql_parts.append(f"`{col}` <= %s")
                params.append(float(max_val) * factor)
            except ValueError:
                pass # Ignore invalid input


    add_range("tuition", "tuition_min", "tuition_max")
    add_range("average_sat", "sat_min", "sat_max")
    add_range("population", "pop_min", "pop_max")
    add_range("admission_rate", "admit_min", "admit_max", 0.01) # Admission rate is stored as decimal

    city = filters.get("city")
    if city:
        sql_parts.append("`city` = %s")
        params.append(city)

    state = filters.get("state")
    if state:
        sql_parts.append("`state` = %s")
        params.append(state)


    if sql_parts:
        sql += " AND " + " AND ".join(sql_parts)

    # Get college count for pagination
    count_sql = "SELECT COUNT(*) FROM `Colleges` WHERE 1=1"
    count_params = []
    if sql_parts:
         count_sql += " AND " + " AND ".join(sql_parts)
         count_params = params # Use the same parameters for count

    cursor.execute(count_sql, count_params)
    total_colleges = cursor.fetchone()["COUNT(*)"]
    length = math.ceil(total_colleges / 16)

    # Ensure page is within valid range
    # Redirect to page 1 if page is less than 1
    if page < 1:
        flash("Invalid page number.", "error")
        return redirect("/browse/1")

    # Redirect to the last page if current page is beyond the last page, ONLY if there are colleges
    if length > 0 and page > length:
        flash("This page does not exist!", "error")
        return redirect(f"/browse/{length}")

    # If length is 0, any page request (including page 1) should just render the empty results
    # No redirect needed if length is 0

    # Add LIMIT and OFFSET for pagination
    # Only apply LIMIT/OFFSET if there are colleges to display
    colleges = []
    if total_colleges > 0:
        sql += " LIMIT 16 OFFSET %s"
        params.append((page - 1) * 16)
        cursor.execute(sql, params)
        colleges = cursor.fetchall()


    # Calculate page range for pagination display
    start_page = max(1, page - 2)
    end_page = min(length, page + 2)
    # Adjust start/end if near the boundaries
    if page <= 3:
        end_page = min(length, 5)
    if length > 5 and page >= length - 2: # Only adjust if there are enough pages to shift
        start_page = max(1, length - 4)

    # Ensure page_range is not empty if length is 0, maybe show [1] or [] depending on desired UI
    page_range = list(range(start_page, end_page + 1))
    if length == 0:
        page_range = [1] # Or [] if you don't want to show page 1 when no results


    return render_template("browse.html.jinja",
        colleges=colleges, page=page, query=query, length=length,
        page_range=page_range, filters=filters) # Pass filters back to template to pre-fill form


# Search Colleges
@app.route("/browse/search", methods=["POST"]) # Changed to POST only as it's a form submission
@flask_login.login_required
def search():
    customer_id = flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()

    # Retrieve all filter values from the form
    filters = {
        "query": request.form.get("query", ""),
        "tuition_min": request.form.get("tuition_min", ""),
        "tuition_max": request.form.get("tuition_max", ""),
        "sat_min": request.form.get("sat_min", ""),
        "sat_max": request.form.get("sat_max", ""),
        "pop_min": request.form.get("pop_min", ""),
        "pop_max": request.form.get("pop_max", ""),
        "admit_min": request.form.get("admit_min", ""),
        "admit_max": request.form.get("admit_max", ""),
        "city": request.form.get("city", ""),
        "state": request.form.get("state", "")
    }

    # Store filters in the session
    session["filters"] = filters

    # Update user's page to 1 in the database (optional, but keeps existing logic)
    cursor.execute("""
        UPDATE `User`
        SET `page` = %s
        WHERE `id` = %s
    """, (1, customer_id))

    conn.commit()
    cursor.close()
    conn.close()

    # Redirect to the first page of browse results
    return redirect("/browse/1")

# Reset Page and Query
@app.route("/browse_reset", methods=["POST", "GET"])
def reset():
    # Clear all filters from the session
    if "filters" in session:
        del session["filters"]

    # Redirect to the first page of browse results
    flash("Your preferences have been reset. Why not start a new search?", 'info')
    return redirect("/browse/1")

# Get Data for Graph Generation
def graph_data(comparing_category):
    
    empty=0
    
    customer_id=flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""

    SELECT `id`, `name`, `tuition`, `admission_rate`, `average_sat`, `population`, `city`, `state`, `longitude`, `latitude`
    FROM `CollegeList`
    LEFT JOIN `Colleges`
    ON `CollegeList`.`college_id` = `Colleges`.`id`
    WHERE `CollegeList`.`user_id`= %s 
            """,(customer_id))
    
    colleges=cursor.fetchall()
    
    #User id (dynamic)
    customer_id=flask_login.current_user.id

    compare_sat=False
    compare_tuition=False
    compare_population=False

    if comparing_category==1:
        compare_sat=True
        comparing="average_sat"
        category="SAT scores"
        
    elif comparing_category==2:
        compare_tuition=True
        comparing="tuition"
        category="Tuition"
        
    elif comparing_category==3:
        compare_population=True
        comparing="population"
        category="Population"
        
    if compare_sat==True:
        title="Student SAT Score vs College SAT Admission Requirements"
        
    elif compare_tuition==True:
        title="Student Tuition Budget vs Average College Tuition"

    elif compare_population==True:
        title="Difference Between User's Prefered Popupation and College's Population"
        


    #Database connection
    conn = connect_db()
    cursor=conn.cursor()

    #Selects college info from every college on the user's list
    cursor.execute(f"""

    SELECT `name`, `tuition`, `admission_rate`, `average_sat`, `population`, `city`, `state`, `longitude`, `latitude`
    FROM `CollegeList`
    LEFT JOIN `Colleges`
    ON `CollegeList`.`college_id` = `Colleges`.`id`
    WHERE `CollegeList`.`user_id`= %s 
            """,(customer_id))

    #Stores college results
    college_results=cursor.fetchall()

    #Selects user's info based on their id
    cursor.execute(f"""
                    
    SELECT `first_name`, `sat_score`, `tuition_budget`, `zip_code`, `population_preferences`
    FROM `User`
    WHERE `id` = %s  
                    
                    """,(customer_id))

    #Stores user info, then converts into a single dictionary
    student_results=cursor.fetchall()
    student_results=student_results[0]
    
    #Initializes name list with first index being the user's name
    names=[student_results['first_name']]

    #If each setting is selected, data list is set to the selected data comparisor
    if compare_sat==True:
        data=[student_results['sat_score']]

    elif compare_tuition==True:
        data=[student_results['tuition_budget']]

    if compare_population==True:
        data=[student_results['population_preferences']]

    for college in college_results:
        names.append(college["name"])

        if compare_sat==True:
            if college["average_sat"]==None:
                names.remove(college["name"])
                empty+=0
            else:
                data.append(college["average_sat"])
                empty+=1

        elif compare_tuition==True:
            if college["tuition"]==None:
                names.remove(college["name"])
                empty+=0
            else:
                data.append(college['tuition'])
                empty+=1
                
        elif compare_population==True:
            
            if college["population"]==None:
                names.remove(college["name"])
                empty+=0
            else:
                data.append(college['population'])
                empty+=1
            
            # cursor.execute(f"""
                        
            # SELECT `lat`, `lng`
            # FROM `Locations`
            # WHERE `zip` = %s               
                        
            #             """, (student_results['zip_code']))
            
            # student_coordinates=cursor.fetchone()
            
            # def haversine(lon1, lat1, lon2, lat2):
            #     """
            #     Calculate the great circle distance in kilometers between two points 
            #     on the earth (specified in decimal degrees)
            #     """
            #     # convert decimal degrees to radians 
            #     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            #     # haversine formula 
            #     dlon = lon2 - lon1 
            #     dlat = lat2 - lat1 
            #     a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            #     c = 2 * asin(sqrt(a)) 
            #     r = 3956 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
            #     return c * r
        
            # data.append(int(haversine(student_coordinates['lng'], student_coordinates['lat'], college['longitude'], college['latitude'])))

    assert data
    
    if empty==0:
        empty=True
    else:
        empty=False
    
    d={}
    d["colleges"]=colleges
    d["empty"]=empty
    d["comparing"]=comparing
    d["category"]=category
    d["data"]=data
    d["names"]=names
    d["compare_tuition"]=compare_tuition
    d["compare_sat"]=compare_sat
    d["compare_population"]=compare_population
    # d["compare_distance"]=compare_distance
        
    return (d)

# Analytics page (college and user graphs for comparison and analysis)
@app.route("/analytics", methods=["POST", "GET"])
def analytics_page():

    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""
           
    SELECT `comparing_category` from `User`
    WHERE `id` = %s        
                   
                   """, (customer_id))
  
    
    comparing_category=(cursor.fetchone()['comparing_category'])
    
    cursor.execute(f"""
                   
    UPDATE `User`
    SET `comparing_category` = %s
    WHERE `id` = %s
                   
                   """,(comparing_category,customer_id))

    d=graph_data(comparing_category)      

    return render_template('analytics.html.jinja', colleges=d["colleges"], empty=d["empty"], comparing=d["comparing"], category=d["category"])

# Category Switch for Analytics
@app.route(f"/analytics/category_change/<category>", methods=["POST", "GET"])
def category_change(category):

    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""
                   
    UPDATE `User`
    SET `comparing_category` = %s
    WHERE `id` = %s
                   
                   """,(category,customer_id))
    
    return redirect("/analytics")

# Plot Graph Image
@app.route('/plot.png')
def plot():
    
    #Initialization
    customer_id=flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()
    
    #Get the user's compared category from the database
    cursor.execute("""
                   
    SELECT `comparing_category` FROM `User` 
    WHERE `id`=%s
                   
                   """,(customer_id))
    
    comparing_category=cursor.fetchone()
    
    comparing_category=comparing_category['comparing_category']
    
    #Runs the graph data generation script
    d=graph_data(comparing_category)
    
    #Stores data from graph data script
    names=d["names"]
    data=d["data"]
    compare_tuition=d["compare_tuition"]
    compare_sat=d["compare_sat"]
    compare_population=d["compare_population"]
    # compare_distance=d["compare_distance"]
    

    #Creates figure
    fig=Figure(figsize=(10,6), facecolor='#202020', edgecolor='#ffffff')

    #Set figure background color
    fig.set_facecolor('#202020')
    
    #Tightens figure
    fig.set_layout_engine("tight")

    #Creates a subplot over figure
    subplot=fig.subplots(1)

    #Subplot background color
    subplot.set_facecolor('#202020')
    
    subplot.tick_params("both", colors="#DEB64B", labelcolor="#DEB64B")
    
    #Spine colors
    subplot.spines['bottom'].set_color('#DEB64B')
    subplot.spines['top'].set_color('#DEB64B') 
    subplot.spines['right'].set_color('#DEB64B')
    subplot.spines['left'].set_color('#DEB64B')
    
    #Axes colors
    subplot.xaxis.label.set_color('#DEB64B')
    subplot.yaxis.label.set_color('#DEB64B')
    
    #Creates a bar graph in the subplot
    bar=subplot.bar(names,data,color='#202020', edgecolor='#DEB64B')
        
    # Changes the first bar to gold
    bar[0].set_color('#DEB64B')
    
    #Rotates the College labels to 
    subplot.xaxis.set_tick_params(rotation=315)
    
    #Sets x-label
    subplot.set_xlabel('Colleges')
    
    if compare_tuition==True:

        #Label names
        subplot.set_ylabel('Tuition')
        
        #Formats to use currency
        subplot.yaxis.set_major_formatter('${x:,.0f}')
    
    elif compare_sat==True:
        
        # Label names
        subplot.set_ylabel('SAT Score')
        
        # Changes the y label range to fit SAT scores
        subplot.set_yticks((1600, 1400, 1200, 1000, 800, 600, 400, 200))
    
    elif compare_population==True:
        
        # Label names
        subplot.set_ylabel('Population')
        
        #Formats to whole numbers
        subplot.yaxis.set_major_formatter('{x:,.0f}')
        
        
    fig.savefig("graph1.png", dpi='figure')

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

# Individual College Page
@app.route("/college/<college_id>", methods=["POST", "GET"])
def college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""
                   
    SELECT * from `User`
    WHERE `id` = %s               
                   
                   """,(customer_id))
    
    student=cursor.fetchone()
    
    page=student['page']

    empty=False
    parameters=[student['zip_code'],student['sat_score'],student['tuition_budget'],student['population_preferences']]

    for parameter in parameters:
        if parameter==None:
            empty=True



    cursor.execute(f"""
                   
    SELECT * from `Colleges`
    WHERE `id` = %s
                   
                   """,(college_id))  
    
    college=cursor.fetchone()
    
    college_tuition=college['tuition']

    college_sat=college['average_sat']

    college_population=college['population']

    if college['tuition']==None:
        college['tuition']="N/A"
    else:
        college['tuition']=f"${college['tuition']:,.0f}"
    
    if college['admission_rate']==None:
        college['admission_rate']="N/A"
    else:
        college['admission_rate']=(f"{college['admission_rate']*100:,.0f}%")
    
    if college['population']==None:
        college['population']="N/A"
    else:
        college['population']=f"{college['population']:,.0f}"

    if college['average_sat']==None:
        college['average_sat']="N/A"
    else:
        college['average_sat']=f"{college['average_sat']:.0f}"

    cursor.execute(f"""
                   
    SELECT * from `CollegeList`
    WHERE `user_id`={customer_id} AND `college_id`={college_id}            
                   """)
    
    added=cursor.fetchall()
    
    if added==():
        added=False
    else:
        added=True    
    
    cursor.execute(f"""
                                 
    SELECT * from `User` WHERE `id` = %s
            """, (customer_id))
    user = cursor.fetchone()

    return render_template("college.html.jinja", user=user, college_population=college_population, college_tuition=college_tuition, college_sat=college_sat, college_id=college_id, college=college, added=added, page=page, student=student)


# Add College from College Page
@app.route("/college/<college_id>/add", methods=["POST", "GET"])
def add_college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""

    SELECT `id`
    FROM `CollegeList`
    LEFT JOIN `Colleges`
    ON `CollegeList`.`college_id` = `Colleges`.`id`
    WHERE `CollegeList`.`user_id`= %s 
            """,(customer_id))
    
    length=cursor.fetchall()
    
    length
    
    if len(length)==5:
        
        flash("You can only have up to 5 colleges on a list!", 'error')
        return redirect (f"/college/{college_id}")
    
    cursor.execute(f"""
                   
    INSERT INTO `CollegeList` (`user_id`, `college_id`)
    VALUES (%s, %s)
                   
                   """,(customer_id, college_id))
    
    return redirect(f"/college/{college_id}")

# Remove College from College Page
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

# Remove College from Analytics Page
@app.route("/analytics/<college_id>/remove", methods=["POST", "GET"])
def remove_list_college(college_id):
    
    customer_id=flask_login.current_user.id
    
    conn=connect_db()
    cursor=conn.cursor()
    
    cursor.execute(f"""
                   
    DELETE FROM `CollegeList`
    WHERE `user_id`= {customer_id} AND `college_id`= {college_id}
                   
                   """)
    
    return redirect("/analytics")

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

# Update user college prefs
@app.route("/settings/update", methods=["POST", "GET"])
@flask_login.login_required
def update():
    customer_id = flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        sat_score = int(request.form["sat_score"])
        tuition_budget = int(request.form["tuition_budget"].replace(",", "").replace("$", ""))
        zip_code = int(request.form["zip_code"])
        population_preferences = int(request.form["population_preferences"].replace(",", ""))
        
        cursor.execute("""          
            UPDATE `User` 
            SET `sat_score`=%s, 
                `tuition_budget`=%s, 
                `zip_code`=%s,
                `population_preferences`=%s
            WHERE id = %s;
        """, (sat_score, tuition_budget, zip_code, population_preferences, customer_id))
        
        conn.commit()
        flash("College parameters updated successfully!", "success")
    
    except Exception as e:
        print("Update error:", e)  # Fallback
        flash("One or more of your fields are invalid!", 'error')
    
    return redirect("/analytics")

# Update user settings
@app.route("/settings/update_user", methods=["POST"])
@flask_login.login_required
def update_user():
    customer_id = flask_login.current_user.id
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Retrieve form values
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        zip_code = request.form["zip_code"]
        
        # Debugging output to check the values
        print("username:", username)
        print("password:", password)
        print("confirm_password:", confirm_password)
        print("first_name:", first_name)
        print("last_name:", last_name)
        print("email:", email)
        print("zip_code:", zip_code)

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect("/settings")

        # Update user information in the database
        cursor.execute("""
            UPDATE `User` 
            SET `username` = %s, 
                `password` = %s, 
                `first_name` = %s, 
                `last_name` = %s, 
                `email` = %s, 
                `zip_code` = %s
            WHERE `id` = %s;
        """, (username, password, first_name, last_name, email, zip_code, customer_id))

        # Commit the changes
        conn.commit()

        # Flash success message
        flash("Settings updated successfully", "success")
    
    # Flash error in the case of error
    except Exception as e:
        flash(f"An error occurred while updating your settings! Error: {str(e)}", "error")
        print(e)

    return redirect("/settings")

# Developer credits and link routing
@app.route('/credits')
@flask_login.login_required
def credits():
    return render_template("credits.html.jinja")

# Log out
@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect('/')
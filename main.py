from flask import Flask, render_template, request
import pymysql
from dynaconf import Dynaconf
import flask_login

# Declare Flask application
app = Flask(__name__)


# Config settings and secrets
conf = Dynaconf(
    settings_file = ["settings.toml"]
)


# Establish database connection
def connect_db():
    """Connect to the phpMyAdmin database (LOCAL STEAM NETWORK ONLY)"""
    conn = pymysql.connect(
        host = "db.steamcenter.tech",
        database = "apollo",
        user = "fchowdury",
        password = conf.password,
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )
    return conn

# # User Login Manager
# login_manager = flask_login.LoginManager()
# login_manager.init_app(app)
# login_manager.login_view=("/login")

# # Classes
# class User:
#     is_authenticated = True
#     is_anonymous = False
#     is_active = True

#     def __init__(self, user_id, username, email, first_name, last_name):
#         self.id = user_id
#         self.username = username
#         self.email = email
#         self.first_name = first_name
#         self.last_name = last_name

#     def get_id(self):
#         return str(self.id)

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        user_id = request.form['user_id']
        regents = request.form['regents']
        name = request.form['name']
        username = request.form['username']

        # Connect to the database
        conn = connect_db()
        cursor = conn.cursor()

        # Insert data into the database
        insert_query = """INSERT INTO `test` (user_id, regents, name, username)
                          VALUES (user_id, regents, name, username)"""
        cursor.execute(insert_query)

        # Commit changes to the database
        conn.commit()

        # Close the connection
        cursor.close()
        conn.close()
        return "Done"
    return render_template("homepage.html.jinja")



if __name__ == '__main__':
    app.run(debug=True)
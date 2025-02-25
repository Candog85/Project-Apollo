# THIS IS A TEST FILE FOR TESTING FUNCTIONS ONLY.

# All imports
import requests
import csv
import json
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

if __name__ == '__main__':
    app.run(debug=True)

@app.route("/")
def test_fetch():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `test`;")
    pulled = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("homepage.html.jinja", testers = pulled)



def requestinfo(schoolname='', schoolstate=''):

    count=0

    api="https://api.data.gov/ed/collegescorecard/v1/schools?api_key=fEZsVdtKgtVU4ODIpjHcP8vDttDK0ftSGZaWDcAk"

    queries={}
    request=''

    if schoolname:
        queries.update({"school.name":(f"{schoolname}")})
    
    if schoolstate:
        queries.update({"school.state":(f"{schoolstate}")})

    for query in queries:
        request+=(f"{query}={queries[query]}")
        count+=1
    
    request=f"{api}&{request}"

    test=requests.get(request).json()

    for key in test:{ 
        print(key,":", test[key]) 
    }
        
    return request

print(requestinfo("Harvard University"))
        


# print(test)

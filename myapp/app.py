from flask_wtf.csrf import CSRFProtect
import flask_wtf
import os
import sqlite3
import qrcode
from flask_bootstrap import Bootstrap
from datetime import date, datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from config import Config
from time import perf_counter
from PIL import Image
from io import BytesIO

""" Touch Ups

config.py: set-up and ensure you have the right environment vars in there

Set up a query module.

Figure out PATH and why flask_bootstrap, flask_session, helpers, or config
aren't detected when you "flask run" in the context of this projects venv.

Replace SQLite3 with a more powerful database.  Concurrency limitations.

Create better database helper functions that ensure connections are closed and opened properly.

Make notes on csrf and flask_wtf

PYTHONPATH / PATH so "flask run" works and detects all the modules and config vars.

Config.py & wsgi.py

DO THE MEGA FLASK TUTORIAL

"""


# Denote this moduile as the application
app = Flask(__name__)

# see config.py for application configuration.
app.config.from_object('config.Config')

# Cross-site request forgery protection
csrf = CSRFProtect(app)

# Enable bootstrap with this application
bootstrap = Bootstrap(app)

# Configure sessions & use filesystem (instead of signed cookies)
Session(app)

# set a database constant
DATABASE = "contact_trace.db"

# set-up database helper

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# ensure database closes after the application request ends by watching the application-level data


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db = db.cursor()
        db.row_factory = sqlite3.Row
    return db

# set up query helper


def query_db(query, args=(), one=False):
    cursor = get_db().execute(query, args)
    row_tuples = cursor.fetchall()
    cursor.close()
    return (row_tuples[0] if row_tuples else None) if one else row_tuples

# use of query helper
# https://www.kite.com/python/docs/sqlite3.Connection.row_factory

# for user in query_db('select * from users'):
#     print user['username'], 'has the id', user['user_id']


# prepare some reference data for accounts
prov_list = ["AB", "BC", "MB", "ON", "QB",
             "SK", "NFLD", "NS", "QB", "NWT", "YK"]

prov_length = len(prov_list)

# prepare QR code

qr_img = qrcode.make('http://www.tracebook.ca/trace_form.html')


# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def home():
    session.clear()
    if request.method == "GET":
        # userId = session["user_id"]
        return render_template("index.html")


@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")
    else:
        email = request.form.get("email")
        # Check email against database to see if user exists
        query = c.execute(
            "SELECT COUNT(*) FROM users WHERE email=?", (email,))
        email_check = query.fetchone()[0]
        if email_check > 0:
            return apology("Sorry! Email taken", 403)
        else:
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")
            # if username is already in db don't register!
            if password != confirmation or not password or not confirmation:
                return apology("Sorry passwords don't match!", 403)
            else:
                firstname = request.form.get("firstname")
                lastname = request.form.get("lastname")
                pwHash = generate_password_hash(password)
                insert_user = "INSERT INTO users (firstname, lastname, email, hash) VALUES(?, ?, ?, ?)"
                values = (firstname, lastname, email, pwHash)
                c.execute(insert_user, values)
                conn.commit()
                return redirect("/login.html")


@app.route("/trace_form.html", methods=["GET", "POST"])
def get_tracebook_form():
    today = date.today()
    now = datetime.now()
    date_textual = today.strftime("%B, %d, %Y")
    time_textual = now.strftime("%-I:%M:%S")
    date_f = today.strftime("%d, %m, %Y")
    time = now.strftime("%H:%M:%S")

    if request.method == "GET":
        hours = int(now.strftime("%H"))
        if (hours > 12):
            time_textual = time_textual + " PM"
        else:
            time_textual = time_textual + " AM"

        query = (
            "SELECT book_number FROM locations")
        tracebooks = query_db(query)

        return render_template("tracebooks/trace_form.html", date=date_textual, tracebooks=tracebooks)

    else:
        book_number = request.form.get("book_number")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        party_size = request.form.get("size")

        insert_user = "INSERT INTO log (book_number, date, time, firstname, lastname, email, phone, party_size) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        values = (book_number, date_f, time, firstname,
                  lastname, email, phone, party_size)
        c.execute(insert_user, values)
        conn.commit()

        session.clear()

        query = (
            "SELECT tracebook_name FROM locations WHERE book_number = ?")
        values = (book_number,)
        book_select = query_db(query, values)

        return render_template("/tracebooks/thank_you.html", book_number=book_number, tracebook=book_select)

# Create the new location in the database

# new location means you can create a dynamic URL for that location

# a person can then generate a QR code to hit that new URL

# when someone hits the site via the QR code, they can submit info on that form including data as to what page their on.

# save that data in the log table appropriately


@app.route("/account.html", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "GET":
        user_id = session['user_id']
        query = (
            "SELECT tracebook_name, st_name, date FROM locations WHERE usr_id = ?")
        value = (user_id,)
        print(user_id)

        c.execute(query, value)
        tracebooks = c.fetchall()

        if not tracebooks:
            return render_template("acc/account.html", length=prov_length, provinces=prov_list)
        else:
            today = date.today()
            last_date = 99/99/9999
            #  date_textual = today.strftime("%B, %d, %Y")
            # diff = date_textual - created_on

            # if diff.days > 30:
            #     last_date = date_textual - 30

            # else:
            #     last_date = created_on

            return render_template("acc/account.html", tracebooks=tracebooks, last_date=last_date, length=prov_length, provinces=prov_list)
    else:
        # get the form data
        usr_id = session['user_id']
        tracebook_name = request.form.get("name")
        st_num = request.form.get("streetnumber")
        st_name = request.form.get("streetname")
        unit_num = request.form.get("unitnumber")
        city = request.form.get("city")
        prov = request.form.get("province")
        post = request.form.get("post")
        country = "CANADA"
        today = date.today()
        date_textual = today.strftime("%B, %d, %Y")

        insert_tracebook = "INSERT INTO locations (usr_id, tracebook_name, st_num, st_name, unit_num, city, prov, post, country, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (usr_id, tracebook_name, st_num, st_name, unit_num,
                  city, prov, post, country, date_textual)
        c.execute(insert_tracebook, values)
        conn.commit()

        return redirect("/account.html")

        img = Image.open(BytesIO(qr_img))
        # validate the form data (?)

        # push it to the database


# make sure that if a user deletes an account, you remove the data from the db.  Drop every row from all tables that have that user_id.


@app.route("/settings.html", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return render_template("acc/settings.html")


@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")
    else:
        # Forget any user_id
        session.clear()

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email!", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        else:
            query = ("SELECT * FROM users WHERE email = ?")
            form_email = request.form.get("email")
            email_query = (form_email,)
            user = query_db(query, email_query)

            if user[0]["email"] != form_email or not check_password_hash(user[0]["hash"], request.form.get("password")):
                return apology("User not found!", 403)

            # Remember which user has logged in
            session["user_id"] = user[0]["_id"]
            firstname = user[0]["firstname"]
            # Redirect user to account page
            return redirect("/account.html")


@app.route("/logout.html", methods=["GET", "POST"])
@login_required
def logout():
    if request.method == "GET":
        session.clear()
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

    # make info into a dict with those tips?
    # cur = get_db().cursor()
    # rows = cur.execute()
    # for row in rows:
    #     print(row)

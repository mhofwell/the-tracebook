from flask_wtf.csrf import CSRFProtect
import flask_wtf
import os
import sqlite3
from flask_bootstrap import Bootstrap
from datetime import date
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from config import Config

""" Touch Ups

config.py: set-up and ensure you have the right environment vars in there

Set up a query module.

Figure out PATH and why flask_bootstrap, flask_session, helpers, or config
aren't detected when you "flask run" in the context of this projects venv.

Replace SQLite3 with a more powerful database.  Concurrency limitations.

Create better database helper functions that ensure connections are closed and opened properly.

Make notes on csrf and flask_wtf




# Denote this moduile as the application
app = Flask(__name__)

# see config.py for application configuration.
app.config.from_object(Config)

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

# def get_db():
#     db = getattr(g, '_database', None)
#     if db is None:
#         db = g._database = sqlite3.connect(DATABASE)
#         db = db.cursor()
#     return db

# # set up query helper

#     # db.row_factory = sqlite3.Row


# def query_db(query, args=(), one=False):
#     cursor = get_db().execute(query, args)
#     row_tuples = cursor.fetchall()
#     cursor.close()
#     return (row_tuples[0] if row_tuples else None) if one else row_tuples

# use of query helper
# https://www.kite.com/python/docs/sqlite3.Connection.row_factory

# for user in query_db('select * from users'):
#     print user['username'], 'has the id', user['user_id']


# ensure database closes after the application request ends by watching the application-level data


# prepare some reference data for accounts

prov_list = ["AB", "BC", "MB", "ON", "QB",
             "SK", "NFLD", "NS", "QB", "NWT", "YK"]

prov_length = len(prov_list)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Ensure responses aren't cached

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        # userId = session["user_id"]
        return render_template("index.html")


@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")
    else:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
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
            print(password)
            print(confirmation)
            # if username is already in db don't register!
            if password != confirmation or not password or not confirmation:
                return apology("Sorry passwords don't match!", 403)
            else:
                pwHash = generate_password_hash(password)
                print(firstname)
                print(lastname)
                print(pwHash)
                insert_user = "INSERT INTO users (firstname, lastname, email, hash) VALUES(?, ?, ?, ?)"
                values = (firstname, lastname, email, pwHash)
                c.execute(insert_user, values)
                conn.commit()
                return redirect("/login.html")


@app.route("/trace_form.html", methods=["GET", "POST"])
def get_tracebook_form():
    if request.method == "GET":
        return render_template("tracebooks/trace_form.html")
    else:
        session.clear()
        return render_template("/tracebooks/thank_you.html")

# Create the new location in the database

# new location means you can create a dynamic URL for that location

# a person can then generate a QR code to hit that new URL

# when someone hits the site via the QR code, they can submit info on that form including data as to what page their on.

# save that data in the log table appropriately


@app.route("/account.html", methods=["GET", "POST"])
def account():
    if request.method == "GET":
        return render_template("acc/account.html", provinces=prov_list, length=prov_length)


# make sure that if a user deletes an account, you remove the data from the db.  Drop every row from all tables that have that user_id.


@app.route("/settings.html", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return render_template("acc/settings.html")


@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")
    # else:
    #     # Forget any user_id
    #     session.clear()

    #     # User reached route via POST (as by submitting a form via POST)
    #     if request.method == "POST":

    #         # Ensure username was submitted
    #         if not request.form.get("username"):
    #                 return apology("must provide username", 403)

    #             # Ensure password was submitted
    #             elif not request.form.get("password"):
    #                 return apology("must provide password", 403)

    #             """ Redo this for SQLite3 connection with cursor. """
    #             # cur = get_db().cursor()
    #             # rows = get_db().cursor("SELECT * FROM users WHERE username = :username",
    #             #                 username=request.form.get("username"))

    #             # Ensure username exists and password is correct
    #             if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
    #                 return apology("invalid username and/or password", 403)

    #             # Remember which user has logged in
    #             session["user_id"] = rows[0]["id"]

    #             # Redirect user to home page
    #             return redirect("/")


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

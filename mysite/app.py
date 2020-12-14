import os
import sqlite3
from flask_bootstrap import Bootstrap
from datetime import date
from flask import Flask, flash, jsonify, redirect, render_template, request, session, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Configure bootstrap with this application
bootstrap = Bootstrap(app)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# set a database constant
DATABASE = "/contact_trace.db"

# set-up database helper


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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


# ensure database closes after the application request ends by watching the application-level data


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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET"])
def home():
    if request.method == "GET":
        # userId = session["user_id"]
        return render_template("index.html")


@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    """DO THIS NEXT"""
    # else:
    #     username = request.form.get("username")
    #     password = request.form.get("password")
    #     confirmation = request.form.get("confirmation")
    #     # if username is already in db don't register!
    #     if password != confirmation or not password or not confirmation:
    #         return apology("Sorry passwords don't match!", 403)
    #     else:
    #         pwHash = generate_password_hash(password)
    #         db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
    #                     username=username, hash=pwHash)
    #         return redirect("/login")


@app.route("/account.html", methods=["GET", "POST"])
def account():
    if request.method == "GET":
        return render_template("acc/account.html")


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

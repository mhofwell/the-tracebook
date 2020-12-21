from flask_wtf.csrf import CSRFProtect
import flask_wtf
import os
from os import path
import os.path
import sqlite3
import csv
from flask_bootstrap import Bootstrap
from datetime import date, datetime
from flask import abort, Flask, safe_join, flash, jsonify, redirect, render_template, request, session, g, send_file, send_from_directory, abort
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from config import Config
from time import perf_counter
from PIL import Image
from io import BytesIO
import shutil

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

# Error flash messages instead of apology, keep state of the app, no refresh.

# tuples vs lists vs dicts and when to use each.

# research cursor object

"""


# Denote this module as the application
app = Flask(__name__)

# see config.py for application configuration.
app.config.from_object('config.Config')

# Cross-site request forgery protection
csrf = CSRFProtect(app)

# Enable bootstrap with this application
bootstrap = Bootstrap(app)

# Configure sessions & use filesystem (instead of signed cookies)
Session(app)

# Config csv directory
app.config["CLIENT_CSV"] = "myapp/static/client/csv/"
app.config["ABS_PATH_CSV"] = "/Users/hofweller/Documents/GitHub/pyProject_flask/myapp/static/client/csv/"

# set a database constant
DATABASE = "myapp/contact_trace.db"

# set a database constant for running the prog from primary directory
# DATABASE = "myapp/contact_trace.db"

# database helper


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

# delete function


def delete_entry(tracebook_name):
    # set-up database helper
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    query = ("DELETE FROM locations where tracebook_name=?")
    value = (tracebook_name,)
    c.execute(query, value)
    conn.commit()
    return


# ensure database closes after the application request ends by watching the application-level data


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# prepare some reference data for accounts
prov_list = ["AB", "BC", "MB", "ON", "QB",
             "SK", "NFLD", "NS", "QB", "NWT", "YK"]

prov_length = len(prov_list)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    return render_template("index.html")


@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")
    else:
        # set-up database helper
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
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
    # set-up database helper
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

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
        c.execute(query, values)
        book_name = c.fetchall()
        print(book_name[0])

        return render_template("/tracebooks/thank_you.html", book_number=book_number, tracebook=book_name[0][0])


@app.route("/account.html", methods=["GET", "POST"])
@login_required
def account():
    # set-up database helper
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == "GET":
        usr_id = session['user_id']
        query = (
            "SELECT tracebook_name, st_name, date, book_number FROM locations WHERE usr_id = ?")
        value = (usr_id,)
        c.execute(query, value)
        tracebooks = c.fetchall()

        tracebook_list = list(tracebooks)
        length = len(tracebook_list)
        i = 0
        count_list = []

        for tracebook in tracebooks:
            query = (
                "SELECT COUNT(*) FROM log WHERE book_number = ?")
            value = (tracebook[3],)
            c.execute(query, value)
            count = c.fetchone()
            count_list.append(count)

        for i in range(length):
            tracebook_list[i] = tracebook_list[i] + count_list[i]

        if not tracebooks:
            return render_template("acc/account.html", length=prov_length, provinces=prov_list)
        else:
            return render_template("acc/account.html", tracebooks=tracebook_list, length=prov_length, provinces=prov_list)

    else:
        if request.form.get('delete'):
            print("DEL")
            tracebook_name = request.form.get('delete')
            print(tracebook_name)
            delete_entry(tracebook_name)
            return redirect('/account.html')

        elif request.form.get('csv'):
            print("CSV")
            book_num = request.form.get('csv')
            print(book_num)
            csv_name = str("Tracebook " + book_num + ".csv")
            print(csv_name)
            path = app.config['CLIENT_CSV']+csv_name
            path = path.strip()
            print(path)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:  # name the Exception `e`
                    print("Failed with:", e.strerror)  # look what it says

            # get all of the rows
            query = (
                "SELECT * FROM log WHERE book_number=?")
            value = (book_num,)
            c.execute(query, value)
            logs = c.fetchall()
            if logs:
                print("Exporting data to csv.....")
                # set-up a send_file with not a format string.  Save filename to variable.
                with open(f"Tracebook {book_num}.csv", "w") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=",")
                    csv_writer.writerow([i[0] for i in c.description])
                    for log in logs:
                        csv_writer.writerow(log)
                print("Moving the csv")
                try:
                    shutil.move(f"Tracebook {book_num}.csv",
                                "myapp/static/client/csv")
                except:
                    print("Could not move")

                try:
                    dir_path = app.config['ABS_PATH_CSV']
                    print("Sending the csv")
                    print(dir_path)
                    return send_from_directory(dir_path, f"Tracebook {book_num}.csv", as_attachment=True)
                except OSError as e:
                    return print("Failed with:", e.strerror)
            else:
                return redirect("account.html")
        else:
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

            # query for matching location data
            query = (
                "SELECT tracebook_name FROM locations WHERE tracebook_name=? AND usr_id = ?")
            value = (tracebook_name, usr_id,)
            c.execute(query, value)
            tracebooks = c.fetchall()

            # check if location exists.

            if tracebooks:
                return apology("Location already created!")

            else:
                insert_tracebook = "INSERT INTO locations (usr_id, tracebook_name, st_num, st_name, unit_num, city, prov, post, country, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                values = (usr_id, tracebook_name, st_num, st_name, unit_num,
                          city, prov, post, country, date_textual)
                c.execute(insert_tracebook, values)
                conn.commit()

                return redirect("/account.html")

# make sure that if a user deletes an account, you remove the data from the db.  Drop every row from all tables that have that user_id.


@app.route("/settings.html", methods=["GET", "POST"])
@login_required
def settings():
    # set-up database helper
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    usr_id = session['user_id']

    if request.method == "GET":
        query = (
            "SELECT firstname, lastname, email FROM users WHERE _id = ?")
        value = (usr_id,)
        print(usr_id)
        c.execute(query, value)
        user = c.fetchone()

        if not user:
            return apology("something went wrong!", 400)
        else:
            query = (
                "SELECT COUNT(*) FROM locations WHERE usr_id = ?")
            value = (usr_id,)
            print(usr_id)
            c.execute(query, value)
            count = c.fetchone()

            return render_template("acc/settings.html", user=user, count=count)

    else:
        if request.form.get('firstname'):
            firstname = request.form.get('firstname')
            update = "UPDATE users SET firstname=? WHERE _id=?"
            values = (firstname, usr_id)
            c.execute(update, values)
            conn.commit()
            return redirect("/account.html")

        elif request.form.get('lastname'):
            lastname = request.form.get('lastname')
            update = "UPDATE users SET lastname=? WHERE _id=?"
            values = (lastname, usr_id)
            c.execute(update, values)
            conn.commit()
            return redirect("/account.html")

        elif request.form.get('email'):
            email = request.form.get('email')
            update = "UPDATE users SET email=? WHERE _id=?"
            values = (email, usr_id)
            c.execute(update, values)
            conn.commit()
            return redirect("/account.html")

        elif request.form.get('password'):
            password = request.form.get('password')
            hash = generate_password_hash(password)
            update = "UPDATE users SET hash=? WHERE _id=?"
            values = (hash, usr_id)
            c.execute(update, values)
            conn.commit()
            return redirect("/account.html")

        else:
            update = "DELETE FROM users WHERE _id=?"
            values = (usr_id,)
            c.execute(update, values)
            conn.commit()
            return redirect("/")


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
            if user:
                if user[0]["email"] != form_email or not check_password_hash(user[0]["hash"], request.form.get("password")):
                    return apology("User not found!", 403)

                # Remember which user has logged in
                session["user_id"] = user[0]["_id"]
                # Redirect user to account page
                return redirect("/account.html")
            else:
                return redirect("/login.html")


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

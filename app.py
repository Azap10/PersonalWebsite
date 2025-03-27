import os
import scheduler
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from pymongo import MongoClient
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure db
client = MongoClient()
db = client.musical_db
users = db.users
songs = db.songs

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# general use functions

def login_required(f):
    # Decorate routes to require login.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    return render_template("apology.html", code=code, message=message), code

# specific direction and routing functions

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username and check password
        user = users.find_one({"username": username})
        if not user or not check_password_hash(user["password_hash"], password):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # is username empty?
        username = request.form.get("username")
        if not username:
            return apology("please provide a username")

        # is password empty?
        elif not request.form.get("password"):
            return apology("please provide a password")

        # is username taken?
        elif users.find_one({"username": username}):
            return apology("username is taken")

        # to passwords match?
        elif not (request.form.get("password") == request.form.get("confirmation")):
            return apology("passwords do not match")

        # if all tests pass, add new user to DB
        users.insert_one({"username": username, "password_hash": generate_password_hash(request.form.get("password"))})
        return redirect("/login")

    else:
        # when loading the page from a url, render the template.
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def upload():
    return render_template("upload_files.html")

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")

@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    songs_file = request.files['songsFile']
    if not songs_file:
        return apology("must provide song file", 403)
    songs_file.save(songs_file.filename)

    timeslots_file = request.files['timeslotsFile']
    if not songs_file:
        return apology("must provide timeslots file", 403)
    timeslots_file.save(timeslots_file.filename)

    if not request.form.get("maxDays"):
        return apology("must provide max days per student", 403)
    if not request.form.get("rehearsalsPerDay"):
        return apology("must provide max rehearsals per day", 403)
    if not request.form.get("iterations"):
        return apology("must provide number of iterations", 403)
    if not request.form.get("topRecorded"):
        return apology("must provide number of displayed schedules", 403)

    timeslot_lists, student_lists = scheduler.scheduler_main(songs_file, timeslots_file, int(request.form.get("maxDays")),
                                                    int(request.form.get("rehearsalsPerDay")), int(request.form.get("iterations")), int(request.form.get("topRecorded")))

    return render_template('display_response.html', timeslot_lists = timeslot_lists, student_lists = student_lists)

# error functions

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
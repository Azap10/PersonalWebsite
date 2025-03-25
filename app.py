import os
import scheduler
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# # Ensure responses aren't cached
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     response.headers["Expires"] = 0
#     response.headers["Pragma"] = "no-cache"
#     return response

# # Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

@app.get("/")
def upload():
    return render_template("upload_files.html")

@app.get("/instructions")
def instructions():
    return render_template("instructions.html")

@app.post('/view')
def view():
    songs_file = request.files['songsFile']
    timeslots_file = request.files['timeslotsFile']
    songs_file.save(songs_file.filename)
    timeslots_file.save(timeslots_file.filename)

    timeslot_lists, student_lists = scheduler.scheduler_main(songs_file, timeslots_file, int(request.form.get("maxDays")),
                                                    int(request.form.get("rehearsalsPerDay")), int(request.form.get("iterations")), int(request.form.get("topRecorded")))

    return render_template('display_response.html', timeslot_lists = timeslot_lists, student_lists = student_lists)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("construction.html")


# # Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
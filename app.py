import os

import pandas as pd
import random
import copy

from flask import Flask, flash, redirect, render_template, request, session
# from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

class Song:
    def __init__(self, song_name, leader, priority, length, stage, students):
        self.song_name = song_name
        self.leader = leader
        self.priority = priority
        self.length = length
        self.stage = bool(stage)  # Convert to boolean
        self.students = students

    def __repr__(self):
        return f"Song(song_name='{self.song_name}', leader='{self.leader}', priority={self.priority}, length={self.length}, stage={self.stage}, students={self.students})"

class Timeslot:
    def __init__(self, weekday, leader, length, stage, song="", taken=False):
        self.weekday = weekday
        self.leader = leader
        self.length = length
        self.stage = bool(stage)  # Convert to boolean
        self.song = song  # Default empty string
        self.taken = taken  # Default false

    def __repr__(self):
        return f"Timeslot(weekday='{self.weekday}', leader='{self.leader}', length={self.length}, stage={self.stage}, song='{self.song}', taken={self.taken})"

def read_songs_from_excel(file_path):
    df = pd.read_excel(file_path)  # Read the spreadsheet without column headers
    songs = []
    student_rehearsals = {}
    
    for _, row in df.iterrows():
        song_name = row["Song Name"]  # First column is the song name
        leader = row["Leader"]  # Second column is the leader
        priority = row["Priority"]  # Third column is the priority
        length = row["Length"]  # Fourth column is the length
        stage = row["Stage"]  # Fifth column is the stage
        
        # Ensure length is 0, 1, or 2
        if length not in [0, 1, 2]:
            raise ValueError(f"Invalid length value: {length}. Allowed values are 0, 1, or 2.")
        
        students = row.iloc[5:].dropna().tolist()  # Remaining columns are students, ignoring NaN values
        
        # Add students to student_rehearsals if not already present
        for student in students:
            if student not in student_rehearsals:
                student_rehearsals[student] = 0
        
        songs.append(Song(song_name, leader, priority, length, stage, students))
    
    # Sort songs by priority in descending order (highest priority first)
    songs.sort(key=lambda song: song.priority, reverse=True)
    
    return songs, student_rehearsals

def read_timeslots_from_excel(file_path):
    df = pd.read_excel(file_path)  # Read the spreadsheet with headers
    timeslots = []
    
    for _, row in df.iterrows():
        length = row["Length"]
        # Ensure length is 0, 1, or 2
        if length not in [0, 1, 2]:
            raise ValueError(f"Invalid length value: {length}. Allowed values are 0, 1, or 2.")
        
        weekday = row["Weekday"]
        if weekday == "Monday":
            weekday = 0
        elif weekday == "Tuesday":
            weekday = 1
        elif weekday == "Wednesday":
            weekday = 2
        elif weekday == "Thursday":
            weekday = 3
        elif weekday == "Friday":
            weekday = 3
        else:
            raise ValueError(f"Invalid weekday name: {weekday}. Allowed calues are 'Monday', 'Tuesday', 'Wedndesday', 'Thursday', or 'Friday'")
        
        timeslot = Timeslot(
            weekday=weekday,
            leader=row["Leader"],
            length=length,
            stage=row["Stage"]
        )
        timeslots.append(timeslot)
    
    return timeslots

def schedule(songs, timeslots, student_rehearsals, max_days, max_per_day):
    weekday_dicts = []
    for i in range(5): # loop for each day of the week
        weekday_dicts.append(student_rehearsals.copy())

    for song in songs:
        matching_timeslot = None
        alternative_timeslot = None
        
        for timeslot in timeslots:
            student_unavailable = False
            # first check if timeslot works with song's student demands
            for student in song.students:
                total_days = 0
                for i in range(5):
                    if weekday_dicts[i][student] > 0:
                        total_days += 1

                if weekday_dicts[timeslot.weekday][student] >= max_per_day or total_days >= max_days:
                    student_unavailable = True
                    

            if not student_unavailable and not timeslot.taken and timeslot.stage == song.stage:
                if timeslot.length == song.length:
                    matching_timeslot = timeslot
                    break
                elif alternative_timeslot is None or (timeslot.length > song.length and alternative_timeslot.length < song.length):
                    alternative_timeslot = timeslot
        
        selected_timeslot = matching_timeslot if matching_timeslot else alternative_timeslot
        if selected_timeslot:
            selected_timeslot.song = song.song_name
            selected_timeslot.taken = True
            for student in song.students:
                weekday_dicts[selected_timeslot.weekday][student] += 1
                student_rehearsals[student] += 1

def scheduler_main(file_path_songs, file_path_timeslots, max_days, max_per_day):
    file_path_songs = "songsTest.xlsx"
    file_path_timeslots = "timeslotsTest.xlsx"
    
    iterations = 5
    top_recorded = 3
    
    try:
        songs, student_rehearsals = read_songs_from_excel(file_path_songs)
        student_rehearsals_empty = student_rehearsals.copy()
        timeslots = read_timeslots_from_excel(file_path_timeslots)
        timeslots_empty = copy.deepcopy(timeslots)
        
        best_timeslots = [0 for i in range(top_recorded)]
        best_lists = [[] for i in range(top_recorded)]
        student_dicts = [{} for i in range(top_recorded)]
        student_lists = [[] for i in range(top_recorded)]

        for iteration in range(iterations):
            # super scientific method for achieving ideal list
            new_songs = []
            tmp_songs = []
            current_priority = songs[0].priority
            for song in songs:
                if song.priority == current_priority:
                    tmp_songs.append(song)
                else:
                    random.shuffle(tmp_songs)
                    for tmp_song in tmp_songs:
                        new_songs.append(tmp_song)
                    tmp_songs = []
                    tmp_songs.append(song)
                    current_priority = song.priority
            random.shuffle(tmp_songs)
            for tmp_song in tmp_songs:
                new_songs.append(tmp_song)
            songs = new_songs

            timeslots = copy.deepcopy(timeslots_empty)
            random.shuffle(timeslots)
            student_rehearsals = student_rehearsals_empty.copy()
            schedule(songs, timeslots, student_rehearsals, max_days, max_per_day)
            
            best_min = 1000
            best_min_idx = 0
            for i in range(top_recorded):
                if best_timeslots[i] < best_min:
                    best_min = best_timeslots[i]
                    best_min_idx = i

            total_scheduled_timeslots = 0
            for timeslot in timeslots:
                if timeslot.taken:
                    total_scheduled_timeslots += 1
            if total_scheduled_timeslots > best_min:
                best_timeslots[best_min_idx] = total_scheduled_timeslots
                best_lists[best_min_idx] = timeslots
                student_dicts[best_min_idx] = student_rehearsals
        
        for i in range(len(student_dicts)):
            student_list_new = []
            for student, rehearsals in student_dicts[i].items():
                student_list_new.append([student, rehearsals])
            student_list_new.sort(key=lambda x: x[1], reverse=True)
            student_lists[i] = student_list_new

        return best_lists, student_lists
            
    except ValueError as e:
        print("Error:", e)


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

    timeslot_lists, student_lists = scheduler_main(songs_file, timeslots_file, int(request.form.get("maxDays")), int(request.form.get("rehearsalsPerDay")))

    return render_template('display_response.html', timeslots = timeslot_lists[0], student_list = student_lists[0])

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("construction.html")


# # Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
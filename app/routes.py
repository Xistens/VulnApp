#!/usr/bin/python3
from functools import wraps
from flask import request, render_template, session, flash, redirect, url_for, jsonify
from app import *
from lxml import etree


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id", None) is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        if not (username and password):
            flash("Username or Password cannot be empty.", "warning")
            return redirect(url_for("login"))

        user = ""
        # Check if user exists
        if CHALLENGE == Challenge.LOGIN_SQLI:
            user = db.sql_query(f"SELECT id, username FROM users WHERE username = '{username}' AND password = '{password}'")
        else:
            user = db.sql_query("SELECT id FROM users WHERE username = ? AND password = ?", 
                [username, password], one=True)
            user = db.sql_query("SELECT id FROM users WHERE username = ? AND password = ?", 
                [username, password])
        if user:
            if CHALLENGE == Challenge.LOGIN_SQLI:
                data = []
                for row in user:
                    data.append([x for x in row])
                app.logger.debug(data)
                session["user_id"] = data[0][0]
                session["userobj"] = data
                app.logger.debug(f"Session: {session['user_id']} {session['userobj']}")
            else:
                session["user_id"] = user["id"]
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")
#admin' union select 1,group_concat(password) from users--

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        if not (username and password):
            flash("Username or Password cannot be empty.")
            return redirect(url_for("signup"))
        
        # No error checking etc...
        if db.insertUser(username, password):
            return redirect(url_for("login"))
        else:
            flash("Username already exists.", "danger")
    return render_template("registration.html")


@app.route("/home")
@login_required
def home():
    return render_template("index.html")


@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():
    user = db.sql_query("SELECT username FROM users WHERE id=?",
        [session["user_id"]], one=True)

    if request.method == "POST":
        title = request.form["title"]
        note = request.form["note"]
        db.sql_insert("INSERT INTO notes (username, title, note) VALUES (?, ?, ?)", 
            [user["username"], title, note])
        return redirect(url_for("notes"))
    
    if CHALLENGE == Challenge.NOTES:
        notes = db.sql_query(f"SELECT title, note FROM notes WHERE username = '{user['username']}'")
    else:
        notes = db.sql_query(f"SELECT title, note FROM notes WHERE username = ?", [user['username']])
    return render_template("notes.html", notes = notes, user = user["username"])


@app.route("/changepwd", methods=["GET", "POST"])
@login_required
def changepwd():
    if request.method == "POST":
        current_pwd = request.form["current-password"]
        new_pwd = request.form["password"]
        new_pwd2 = request.form["password2"]
    
        if not (new_pwd == new_pwd2):
            flash("Passwords doesn't match.")
            return redirect(url_for("changepwd"))
        
        user = db.sql_query("SELECT username, password FROM users WHERE id = ?",
            [session["user_id"]], one=True)
        
        if not (current_pwd == user["password"]):
            flash("Wrong password supplied.", "danger")
            return redirect(url_for("changepwd"))
        
        if CHALLENGE == Challenge.LOGIN:
            db.sql_insert(f"UPDATE users SET password = ? WHERE username = '{user['username']}'",
                [new_pwd])
        else:
            db.sql_insert(f"UPDATE users SET password = ? WHERE username = ?",
                [user['username'], new_pwd])

        flash("Password changed", "info")
        return redirect(url_for("changepwd"))
    return render_template("updatepwd.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/book", methods=["GET"])
@login_required
def book():
    if request.method == "GET":
        title = request.args.get("title", "")
        book = None

        if BOOK_CHALLENGE == Challenge_Book.BOOK_HARD:
            bid = db.sql_query(f"SELECT id FROM books WHERE title = '{title}'", one=True)
            if bid:
                book = db.sql_query(f"SELECT * FROM books WHERE id = '{bid['id']}'", one=True)
        else:
            book = db.sql_query(f"SELECT * from books WHERE id = (SELECT id FROM books WHERE title='{title}')", one=True)
        if book:
            return jsonify(
                title=book["title"],
                description=book["description"],
                author=book["author"]
            )
        return ""


@app.route("/xml", methods=["POST", "GET"])
def xml():
    """
    XXE Vulnerable
    """
    parsed_xml = b""
    if request.method == "POST":
        xml = request.form["xml"]
        try:
            try:
                parser = etree.XMLParser(no_network=False, dtd_validation=True)
                doc = etree.fromstring(str(xml), parser)
                parsed_xml = etree.tostring(doc)
            except:
                parser = etree.XMLParser(no_network=False)
                doc = etree.fromstring(str(xml), parser)
                parsed_xml = etree.tostring(doc)
        except etree.XMLSyntaxError:
            parsed_xml = b"Invalid XML"
    return render_template("xml.html", result=parsed_xml.decode("utf-8"))
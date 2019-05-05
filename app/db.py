#!/usr/bin/python3
import sqlite3
from flask import g
from app import app, DATABASE

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    
    # Use namedtuple's. Access them by index or key.
    db.row_factory = sqlite3.Row
    return db

def init_db(schema):
    with app.app_context():
        db = get_db()
        with app.open_resource(schema, mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def sql_query(query, args=(), one=False):
    """
    user = sql_query('select * from users where username = ?', 
        [username], one=True)
    """
    try:
        app.logger.debug(query)
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
    except sqlite3.OperationalError as e:
        app.logger.debug(e)
        rv = {}
    return (rv[0] if rv else None) if one else rv

def sql_insert(query, args=()):
    app.logger.debug(query)
    cur = get_db().execute(query, args)
    cur.execute("COMMIT")

def insertUser(username, password):
    # Check if user already exists
    if sql_query("SELECT username FROM users WHERE username=?", [username]):
        return False

    # insert user
    sql_insert("INSERT INTO users (username, password) VALUES (?, ?)", [username, password])
    return True
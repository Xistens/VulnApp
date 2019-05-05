#!/usr/bin/python3
from flask import Flask
from enum import Enum
import logging

app = Flask(__name__)
# Yes, hack it
app.secret_key = b"changeme"
app.debug = True
logging.basicConfig(level=logging.DEBUG)

class Challenge(Enum):
    NOTES = 1
    LOGIN = 2

class Challenge_Book(Enum):
    BOOK_EASY = 1
    BOOK_HARD = 2

CHALLENGE = Challenge.NOTES
BOOK_CHALLENGE = Challenge_Book.BOOK_EASY
DATABASE = "database.db"

from app import db, routes

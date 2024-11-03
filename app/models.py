from app import db
from datetime import datetime


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    youtube_link = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Song {self.title}>'


class AdminKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_value = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime)
    description = db.Column(db.String(200))

class Scheduler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    day_of_week = db.Column(db.String, nullable=False)
    play_time = db.Column(db.Time, nullable=False)
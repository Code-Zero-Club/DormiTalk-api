from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from datetime import datetime
import random
import string


app = Flask(__name__)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    youtube_link = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Song {self.title}>'


class SongSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "youtube_link")

song_schema = SongSchema()
songs_schema = SongSchema(many=True)

@app.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs)

@app.route('/add', methods=['POST'])
def add_song_web():
    title = request.form['title']
    youtube_link = request.form['youtube_link']
    new_song = Song(title=title, youtube_link=youtube_link)
    db.session.add(new_song)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/songs', methods=['POST'])
def add_song_api():
    try:
        data = song_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_song = Song(title=data['title'], youtube_link=data['youtube_link'])
    db.session.add(new_song)
    db.session.commit()
    return song_schema.jsonify(new_song), 201

@app.route('/api/songs', methods=['GET'])
def get_songs():
    all_songs = Song.query.all()
    return songs_schema.jsonify(all_songs)

@app.route('/api/songs/<int:id>', methods=['GET'])
def get_song(id):
    song = Song.query.get_or_404(id)
    return song_schema.jsonify(song)

@app.route('/api/songs/<int:id>', methods=['PUT'])
def update_song(id):
    song = Song.query.get_or_404(id)
    
    try:
        data = song_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    song.title = data['title']
    song.youtube_link = data['youtube_link']
    
    db.session.commit()
    return song_schema.jsonify(song)

@app.route('/api/songs/<int:id>', methods=['DELETE'])
def delete_song(id):
    song = Song.query.get_or_404(id)
    db.session.delete(song)
    db.session.commit()
    return '', 204


class LoginKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def generate_random_key(length=20):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

@app.route('/api/generate_key', methods=['POST'])
def generate_key():
    new_key = generate_random_key()
    login_key = LoginKey(key=new_key)
    db.session.add(login_key)
    db.session.commit()
    return jsonify({"key": new_key}), 201

@app.route('/api/validate_key', methods=['POST'])
def validate_key():
    key = request.json.get('key')
    login_key = LoginKey.query.filter_by(key=key).first()
    if login_key:
        return jsonify({"message": "Valid key"}), 200
    else:
        return jsonify({"message": "Invalid key"}), 401


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
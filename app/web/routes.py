from flask import Blueprint, render_template, redirect, url_for, request
from app.models import Song
from app import db
from sqlalchemy.sql.expression import func

bp = Blueprint('web', __name__)

@bp.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs)

@bp.route('/add', methods=['POST'])
def add_song():
    title = request.form['title']
    youtube_link = request.form['youtube_link']
    new_song = Song(title=title, youtube_link=youtube_link)
    db.session.add(new_song)
    db.session.commit()
    return redirect(url_for('web.index'))

@bp.route('/play')
def play_songs():
    num_songs = int(request.args.get('num', 10))
    songs = Song.query.order_by(func.random()).limit(num_songs).all()
    return render_template('play.html', songs=songs)
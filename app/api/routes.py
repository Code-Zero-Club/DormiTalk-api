from flask import Blueprint, request, jsonify
from app.models import Song, AdminKey
from app.schemas import SongSchema, AdminKeySchema
from app.auth import require_admin_key
from app import db
from datetime import datetime, timedelta
import secrets

from app.models import Scheduler, Song
from app.schemas import SchedulerSchema

bp = Blueprint('api', __name__)
song_schema = SongSchema()
songs_schema = SongSchema(many=True)
admin_key_schema = AdminKeySchema()
scheduler_schema = SchedulerSchema()
schedulers_schema = SchedulerSchema(many=True)


@bp.route('/songs', methods=['GET'])
def get_songs():
    songs = Song.query.all()
    result = songs_schema.dump(songs)
    for song in result:
        song['last_modified'] = song['last_modified'].isoformat() if song['last_modified'] else None
    return jsonify(result)


@bp.route('/songs/<int:id>', methods=['GET'])
def get_song(id):
    song = Song.query.get_or_404(id)
    result = song_schema.dump(song)
    result['last_modified'] = song.last_modified.isoformat() if song.last_modified else None
    return jsonify(result)


@bp.route('/songs', methods=['POST'])
@require_admin_key
def create_song():
    data = request.get_json()
    new_song = Song(
        title=data['title'],
        youtube_link=data['youtube_link']
    )
    db.session.add(new_song)
    db.session.commit()
    return song_schema.jsonify(new_song), 201

@bp.route('/schedulers', methods=['POST'])
@require_admin_key
def create_scheduler():
    data = request.get_json()
    new_scheduler = Scheduler(
        song_id=data['song_id'],
        play_time=datetime.strptime(data['play_time'], '%H:%M:%S').time(),
        day_of_week=data['day_of_week']
    )
    db.session.add(new_scheduler)
    db.session.commit()
    return scheduler_schema.jsonify(new_scheduler), 201


@bp.route('/schedulers', methods=['GET'])
def get_schedulers():
    schedulers = Scheduler.query.all()
    return schedulers_schema.jsonify(schedulers), 200


@bp.route('/admin/key', methods=['POST'])
def generate_key():
    data = request.get_json()
    key = secrets.token_hex(32)
    validity_days = data.get('validity_days', 7)
    description = data.get('description', '')

    new_key = AdminKey(
        key_value=key,
        expires_at=datetime.utcnow() + timedelta(days=validity_days),
        description=description
    )
    db.session.add(new_key)
    db.session.commit()

    return admin_key_schema.jsonify(new_key), 201
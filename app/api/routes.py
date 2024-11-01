from flask import Blueprint, request, jsonify
from app.models import Song, AdminKey
from app.schemas import SongSchema, AdminKeySchema
from app.auth import require_admin_key
from app import db
from datetime import datetime, timedelta
import secrets

bp = Blueprint('api', __name__)
song_schema = SongSchema()
songs_schema = SongSchema(many=True)
admin_key_schema = AdminKeySchema()


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
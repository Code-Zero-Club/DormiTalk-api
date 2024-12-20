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
    return jsonify(result)

@bp.route('/songs/<int:id>', methods=['GET'])
def get_song(id):
    song = Song.query.get_or_404(id)
    result = song_schema.dump(song)
    return jsonify(result)

@bp.route('/songs', methods=['POST'])
@require_admin_key
def create_song():
    data = request.get_json()
    new_song = Song(
        title=data['title'],
        youtube_id=data['youtube_id'],
        play_time=data['play_time']
    )
    db.session.add(new_song)
    db.session.commit()
    return song_schema.jsonify(new_song), 201

@bp.route('/songs/<int:id>', methods=['DELETE'])
@require_admin_key
def delete_song(id):
    song = Song.query.get_or_404(id)
    db.session.delete(song)
    db.session.commit()
    return '', 204


@bp.route('/schedulers', methods=['POST'])
@require_admin_key
def create_scheduler():
    data = request.get_json()
    new_scheduler = Scheduler(
        start_time=datetime.strptime(data['start_time'], '%H:%M:%S').time(),
        day_of_week=','.join(data['day_of_week']),
        play_time=data['play_time']
    )
    db.session.add(new_scheduler)
    db.session.commit()
    return scheduler_schema.jsonify(new_scheduler), 201

@bp.route('/schedulers/<int:id>', methods=['PUT'])
@require_admin_key
def update_scheduler(id):
    data = request.get_json()
    scheduler = Scheduler.query.get_or_404(id)
    scheduler.start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
    scheduler.day_of_week = ','.join(data['day_of_week'])
    scheduler.play_time = data['play_time']
    db.session.commit()
    return scheduler_schema.jsonify(scheduler), 200

@bp.route('/schedulers', methods=['GET'])
def get_schedulers():
    schedulers = Scheduler.query.all()
    result = schedulers_schema.dump(schedulers)
    for scheduler in result:
        scheduler['day_of_week'] = scheduler['day_of_week'].split(',')
    return jsonify(result), 200


@bp.route('/auth/key', methods=['GET'])
def check_key():
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'Key is required'}), 400

    admin_key = AdminKey.query.filter_by(key_value=key).first()
    if admin_key and admin_key.is_active and admin_key.expires_at > datetime.utcnow():
        return jsonify({
            'message': 'Key is valid',
            'description': admin_key.description,
            'expires_at': admin_key.expires_at.isoformat()
        }), 200
    else:
        return jsonify({'error': 'Invalid or expired key'}), 401

@bp.route('/admin/key', methods=['POST'])
def generate_key():
    data = request.get_json()
    key = secrets.token_hex(32)
    validity_days = data.get('validity_days', 7)
    description = data.get('description', '')

    expires_at = (
        datetime.utcnow() + timedelta(days=36500)
        if validity_days == 0
        else datetime.utcnow() + timedelta(days=validity_days)
    )

    new_key = AdminKey(
        key_value=key,
        expires_at=expires_at,
        description=description
    )
    db.session.add(new_key)
    db.session.commit()

    return admin_key_schema.jsonify(new_key), 201
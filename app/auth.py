from functools import wraps
from flask import request, jsonify
from app import db
from app.models import AdminKey
from datetime import datetime


def require_admin_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authentication token provided'}), 401

        key = auth_header.split(' ')[1]
        admin_key = AdminKey.query.filter_by(key_value=key).first()

        if not admin_key:
            return jsonify({'error': 'Invalid key'}), 401

        if not admin_key.is_active:
            return jsonify({'error': 'Inactive key'}), 401

        if admin_key.expires_at < datetime.utcnow():
            return jsonify({'error': 'Expired key'}), 401

        admin_key.last_used = datetime.utcnow()
        db.session.commit()

        return f(*args, **kwargs)

    return decorated_function
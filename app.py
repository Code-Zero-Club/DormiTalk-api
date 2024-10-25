from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from sqlalchemy.sql.expression import func
from functools import wraps
from datetime import datetime, timedelta
import sqlite3
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

# 노래 목록
@app.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs)

# 노래 추가
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

# 노래 목록 조회
@app.route('/api/songs', methods=['GET'])
def get_songs():
    all_songs = Song.query.all()
    return songs_schema.jsonify(all_songs)

# 특정 노래 조회
@app.route('/api/songs/<int:id>', methods=['GET'])
def get_song(id):
    song = Song.query.get_or_404(id)
    return song_schema.jsonify(song)

# 노래 무작위 선택
@app.route('/play', methods=['GET'])
def play_songs():
    try:
        num_songs = int(request.args.get('num', 10))  # 쿼리 매개변수 'num'을 정수로 변환, 기본값은 10
    except ValueError:
        return jsonify({"error": "Invalid number of songs"}), 400  # 'num'이 유효하지 않은 경우 오류 반환
    
    songs = Song.query.order_by(func.random()).limit(num_songs).all()  # 무작위로 지정된 수의 노래를 데이터베이스에서 가져옴
    return render_template('play.html', songs=songs)  # 노래 목록을 템플릿에 전달하여 렌더링

# 노래 수정
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

# 노래 삭제
@app.route('/api/songs/<int:id>', methods=['DELETE'])
def delete_song(id):
    song = Song.query.get_or_404(id)
    db.session.delete(song)
    db.session.commit()
    return '', 204


class SongsDB:
    def __init__(self, db_name='songs.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.setup_admin_table()
    
    def setup_admin_table(self):
        """songs.db에 관리자 키 테이블을 추가합니다."""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_value TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_used TIMESTAMP,
            description TEXT
        )
        ''')
        self.conn.commit()
    
    def generate_admin_key(self, validity_days=7, description=""):
        """새로운 관리자 키를 생성합니다."""
        try:
            key = secrets.token_hex(32)
            expires_at = datetime.now() + timedelta(days=validity_days)
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO admin_auth (key_value, expires_at, description)
            VALUES (?, ?, ?)
            ''', (key, expires_at, description))
            self.conn.commit()
            
            return {
                'key': key,
                'expires_at': expires_at.isoformat(),
                'description': description
            }
        except sqlite3.Error as e:
            return {'error': f'Database error: {str(e)}'}
    
    def verify_admin_key(self, key):
        """관리자 키의 유효성을 검증합니다."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT expires_at, is_active 
            FROM admin_auth 
            WHERE key_value = ?
            ''', (key,))
            
            result = cursor.fetchone()
            if not result:
                return False, "Invalid key"
            
            expires_at, is_active = result
            expires_at = datetime.fromisoformat(expires_at)
            
            if not is_active:
                return False, "Inactive key"
            
            if expires_at < datetime.now():
                return False, "Expired key"
            
            # 마지막 사용 시간 업데이트
            cursor.execute('''
            UPDATE admin_auth 
            SET last_used = ? 
            WHERE key_value = ?
            ''', (datetime.now().isoformat(), key))
            self.conn.commit()
            
            return True, "Valid key"
            
        except sqlite3.Error as e:
            return False, f'Database error: {str(e)}'
    
    def list_admin_keys(self):
        """모든 관리자 키 목록을 반환합니다."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT key_value, created_at, expires_at, is_active, last_used, description
            FROM admin_auth
            ORDER BY created_at DESC
            ''')
            
            keys = cursor.fetchall()
            return [{
                'key': k[0],
                'created_at': k[1],
                'expires_at': k[2],
                'is_active': k[3],
                'last_used': k[4],
                'description': k[5]
            } for k in keys]
            
        except sqlite3.Error as e:
            return {'error': f'Database error: {str(e)}'}
    
    def deactivate_admin_key(self, key):
        """관리자 키를 비활성화합니다."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE admin_auth 
            SET is_active = FALSE 
            WHERE key_value = ?
            ''', (key,))
            
            if cursor.rowcount == 0:
                return False, "Key not found"
            
            self.conn.commit()
            return True, "Key deactivated successfully"
            
        except sqlite3.Error as e:
            return False, f'Database error: {str(e)}'

# 데이터베이스 인스턴스 생성
db = SongsDB()

# 인증 데코레이터
def require_admin_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authentication token provided'}), 401
        
        key = auth_header.split(' ')[1]
        is_valid, message = db.verify_admin_key(key)
        
        if not is_valid:
            return jsonify({'error': message}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# API 엔드포인트
@app.route('/api/admin/key', methods=['POST'])
def generate_key():
    """새로운 관리자 키를 생성합니다."""
    data = request.get_json()
    validity_days = data.get('validity_days', 7)
    description = data.get('description', '')
    
    key_data = db.generate_admin_key(validity_days, description)
    if 'error' in key_data:
        return jsonify(key_data), 500
    return jsonify(key_data), 201

@app.route('/api/admin/verify', methods=['POST'])
def verify_key():
    """관리자 키의 유효성을 검증합니다."""
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    
    is_valid, message = db.verify_admin_key(key)
    return jsonify({
        'valid': is_valid,
        'message': message
    })

@app.route('/api/admin/keys', methods=['GET'])
@require_admin_key
def list_keys():
    """모든 관리자 키 목록을 반환합니다."""
    keys = db.list_admin_keys()
    if 'error' in keys:
        return jsonify(keys), 500
    return jsonify(keys)

@app.route('/api/admin/key/deactivate', methods=['POST'])
@require_admin_key
def deactivate_key():
    """관리자 키를 비활성화합니다."""
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    
    success, message = db.deactivate_admin_key(key)
    if not success:
        return jsonify({'error': message}), 404
    
    return jsonify({'message': message})

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
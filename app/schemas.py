from app import ma
from app.models import Song, AdminKey


class SongSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Song

    id = ma.auto_field()
    title = ma.auto_field()
    youtube_link = ma.auto_field()
    created_at = ma.auto_field()

song_schema = SongSchema()
songs_schema = SongSchema(many=True)

class AdminKeySchema(ma.SQLAlchemySchema):
    class Meta:
        model = AdminKey

    key_value = ma.auto_field()
    created_at = ma.auto_field()
    expires_at = ma.auto_field()
    is_active = ma.auto_field()
    last_used = ma.auto_field()
    description = ma.auto_field()
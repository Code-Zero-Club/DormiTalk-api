from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    # Register blueprints
    with app.app_context():
        from app.api.routes import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')

    print("Registered endpoints:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    return app
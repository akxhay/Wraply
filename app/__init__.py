from flask import Flask
from .database import db
from .routes.config_routes import config_bp
from .routes.execute_routes import execute_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(config_bp)
    app.register_blueprint(execute_bp)

    @app.route("/")
    def home():
        return "<h2>API Wrapper Running</h2><a href='/configs'>Configs</a>"

    return app
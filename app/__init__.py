from flask import Flask, render_template

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
        return render_template("index.html")

    return app
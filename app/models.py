from .database import db


class APIConfig(db.Model):
    __tablename__ = "api_configs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    url = db.Column(db.String(500))
    method = db.Column(db.String(10))
    headers = db.Column(db.Text)
    auth_type = db.Column(db.String(50))
    auth_value = db.Column(db.String(255))
    response_mapping = db.Column(db.Text)
    enabled = db.Column(db.Boolean, default=True)
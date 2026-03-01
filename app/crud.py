from .models import APIConfig
from .database import db


def create_config(data):
    config = APIConfig(**data)
    db.session.add(config)
    db.session.commit()
    return config


def get_all_configs():
    return APIConfig.query.all()


def get_config(config_id):
    return APIConfig.query.get(config_id)


def update_config(config_id, data):
    config = get_config(config_id)

    for key, value in data.items():
        setattr(config, key, value)

    db.session.commit()
    return config


def delete_config(config_id):
    config = get_config(config_id)
    db.session.delete(config)
    db.session.commit()
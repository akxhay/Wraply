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

def clone_config(config_id):
    original = APIConfig.query.get(config_id)

    if not original:
        return None

    count = APIConfig.query.filter(
        APIConfig.name.like(f"{original.name}_copy%")
    ).count()

    new_name = f"{original.name}_copy_{count+1}"

    cloned = APIConfig(
        name=new_name,
        url=original.url,
        method=original.method,
        headers=original.headers,
        auth_type=original.auth_type,
        auth_value=original.auth_value,
        response_mapping=original.response_mapping,
        enabled=False,  # safer default
    )

    db.session.add(cloned)
    db.session.commit()
    return cloned

def delete_config(config_id):
    config = get_config(config_id)
    db.session.delete(config)
    db.session.commit()

def toggle_config(config_id):
    config = get_config(config_id)
    if not config:
        return None
    config.enabled = not config.enabled
    db.session.commit()
    return config
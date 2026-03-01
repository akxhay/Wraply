from .models import APIConfig
from .database import db
from .utils import serialize_model


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
    if not config:
        return None

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

    new_name = f"{original.name}_copy_{count + 1}"

    cloned = APIConfig(
        name=new_name,
        url=original.url,
        method=original.method,
        headers=original.headers,
        header_transform=original.header_transform,
        auth_type=original.auth_type,
        auth_value=original.auth_value,
        auth_header_name=original.auth_header_name,
        path_params_schema=original.path_params_schema,
        query_params_schema=original.query_params_schema,
        body_transform=original.body_transform,
        response_transform=original.response_transform,
        sample_payload=original.sample_payload,
        enabled=False,  # safer default
    )

    db.session.add(cloned)
    db.session.commit()
    return cloned


def delete_config(config_id):
    config = get_config(config_id)
    if not config:
        return None
    db.session.delete(config)
    db.session.commit()


def toggle_config(config_id):
    config = get_config(config_id)
    if not config:
        return None
    config.enabled = not config.enabled
    db.session.commit()
    return config

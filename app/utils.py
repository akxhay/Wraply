import json
from copy import deepcopy

FIELDS_TO_STRINGIFY = [
    "headers",
    "header_transform",
    "path_params_schema",
    "query_params_schema",
    "body_transform",
    "response_transform",
    "sample_payload",
]


def serialize_model(obj):
    """Convert SQLAlchemy model to dictionary safely"""
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def serialize_list(objects):
    return [serialize_model(obj) for obj in objects]


def to_original_shape(cfg: dict, fields_to_stringify=None) -> dict:
    """
    Return a copy of cfg where specified fields are JSON-encoded strings.
    """
    if fields_to_stringify is None:
        fields_to_stringify = FIELDS_TO_STRINGIFY
    out = deepcopy(cfg)
    for key in fields_to_stringify:
        if key in out and not isinstance(out[key], str):
            # Compact JSON with a space after colon for readability like your sample
            out[key] = json.dumps(out[key], separators=(",", ": "))
    return out

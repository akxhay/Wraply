import json
from flask import Blueprint, request, jsonify

from ..crud import get_config
from ..executor import execute_sync
from ..models import APIConfig
from ..utils import to_original_shape

execute_bp = Blueprint("execute", __name__, url_prefix="/execute")


@execute_bp.route("", methods=["POST"])
def create():
    data = request.json
    original_data = to_original_shape(data)
    config = APIConfig(**original_data)
    result = execute_sync(config, config.sample_payload)
    return jsonify(result)


@execute_bp.route("/<int:id>", methods=["POST"])
def execute(id):
    """
    Execute an API config with an optional payload.
    The payload is used as the source for all dynamic transformations.
    """
    config = get_config(id)

    if not config or not config.enabled:
        return jsonify({"error": "Config not found or not enabled"}), 404

    try:
        result = execute_sync(config, request.json)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@execute_bp.route("/<int:id>/sample", methods=["POST"])
def execute_with_sample(id):
    """
    Execute an API config using its stored sample_payload.
    Useful for testing a config without needing to provide a payload.
    Optionally, a partial payload in the request body will be merged on
    top of the sample (request body values take precedence).
    """
    config = get_config(id)

    if not config or not config.enabled:
        return jsonify({"error": "Config not found or not enabled"}), 404

    # Start from stored sample
    payload = {}
    if config.sample_payload:
        payload = json.loads(config.sample_payload)

    # Merge any override values from the request body
    if request.json:
        payload.update(request.json)

    try:
        result = execute_sync(config, payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@execute_bp.route("/<int:id>/dry-run", methods=["POST"])
def dry_run(id):
    """
    Return the fully resolved request that would be sent — URL, headers,
    query params, body — without actually making the upstream HTTP call.
    Useful for debugging transformation configs.
    """
    import json as _json
    from ..executor import (
        _build_headers, _build_url, _build_query_params, _build_body
    )

    config = get_config(id)

    if not config:
        return jsonify({"error": "Config not found"}), 404

    payload = {}
    if config.sample_payload:
        payload = _json.loads(config.sample_payload)
    if request.json:
        payload.update(request.json)

    return jsonify({
        "method": config.method,
        "url": _build_url(config, payload),
        "headers": _build_headers(config, payload),
        "query_params": _build_query_params(config, payload),
        "body": _build_body(config, payload),
    })

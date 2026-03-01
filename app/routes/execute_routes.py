from flask import Blueprint, request, jsonify
from ..crud import get_config
from ..executor import execute_sync

execute_bp = Blueprint("execute", __name__, url_prefix="/execute")


@execute_bp.route("/<int:id>", methods=["POST"])
def execute(id):
    config = get_config(id)

    if not config or not config.enabled:
        return jsonify({"error": "Config not enabled"}), 404

    result = execute_sync(config, request.json)
    return jsonify(result)
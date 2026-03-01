from flask import Blueprint, request, jsonify
from ..crud import (
    create_config,
    get_all_configs,
    update_config,
    delete_config,
)

config_bp = Blueprint("configs", __name__, url_prefix="/configs")


@config_bp.route("", methods=["GET"])
def list_configs():
    configs = get_all_configs()
    return jsonify([c.__dict__ for c in configs])


@config_bp.route("", methods=["POST"])
def create():
    data = request.json
    config = create_config(data)
    return jsonify({"id": config.id})


@config_bp.route("/<int:id>", methods=["PUT"])
def update(id):
    config = update_config(id, request.json)
    return jsonify({"updated": config.id})


@config_bp.route("/<int:id>", methods=["DELETE"])
def delete(id):
    delete_config(id)
    return jsonify({"status": "deleted"})
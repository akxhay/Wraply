from flask import Blueprint, request, jsonify, render_template

from ..crud import (
    create_config,
    get_all_configs,
    toggle_config,
    update_config,
    delete_config,
    clone_config
)
from ..utils import serialize_list

config_bp = Blueprint("configs", __name__, url_prefix="/configs")


@config_bp.route("/ui")
def ui():
    return render_template("configs.html")


@config_bp.route("", methods=["GET"])
def list_configs():
    configs = get_all_configs()
    return jsonify(serialize_list(configs))


@config_bp.route("", methods=["POST"])
def create():
    data = request.json
    config = create_config(data)
    return jsonify({"id": config.id})


@config_bp.route("/<int:id>", methods=["PUT"])
def update(id):
    config = update_config(id, request.json)
    return jsonify({"updated": config.id})

@config_bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    config = clone_config(id)

    if not config:
        return {"error": "Config not found"}, 404

    return jsonify({"updated": config.id})


@config_bp.route("/<int:id>", methods=["DELETE"])
def delete(id):
    delete_config(id)
    return jsonify({"status": "deleted"})

@config_bp.route("/<int:id>/toggle", methods=["PATCH"])
def toggle(id):
    config = toggle_config(id)

    if not config:
        return {"error": "Not found"}, 404

    return jsonify({"enabled": config.enabled})

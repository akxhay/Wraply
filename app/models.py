from .database import db


class APIConfig(db.Model):
    __tablename__ = "api_configs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    url = db.Column(db.String(500))
    method = db.Column(db.String(10))

    # --- Auth ---
    auth_type = db.Column(db.String(50))   # "bearer", "basic", "api_key", "none"
    auth_value = db.Column(db.String(255))
    auth_header_name = db.Column(db.String(100), default="Authorization")  # for api_key type

    # --- Static headers (JSON object) ---
    # e.g. {"Content-Type": "application/json", "X-App-Id": "abc"}
    headers = db.Column(db.Text)

    # --- Header transformation (JSON object) ---
    # Dynamically inject headers from incoming request payload at call time.
    # e.g. {"X-Tenant-Id": "$.tenant_id"}  → reads tenant_id from call payload
    header_transform = db.Column(db.Text)

    # --- Path params schema (JSON array of objects) ---
    # Declares which path params exist and how to resolve them from the call payload.
    # e.g. [{"name": "user_id", "source": "$.user_id"}]
    # URL template uses {user_id} syntax: https://api.example.com/users/{user_id}
    path_params_schema = db.Column(db.Text)

    # --- Query params schema (JSON array of objects) ---
    # Declares static or dynamic query params.
    # e.g. [{"name": "limit", "value": "10"}, {"name": "filter", "source": "$.filter"}]
    query_params_schema = db.Column(db.Text)

    # --- Request body transformation (JSON object) ---
    # Maps the call payload fields to the outgoing API request body.
    # e.g. {"username": "$.user.name", "email": "$.user.email"}
    # Use "$PASSTHROUGH" as the sole value to forward payload as-is.
    body_transform = db.Column(db.Text)

    # --- Response transformation (JSON object) ---
    # Maps the upstream API response fields to the returned response.
    # e.g. {"userId": "$.data.id", "fullName": "$.data.attributes.name"}
    # Use "$PASSTHROUGH" as the sole value to return response as-is.
    response_transform = db.Column(db.Text)

    # --- Sample payload (JSON object) ---
    # A representative example payload that can be used to test the config.
    # e.g. {"user_id": 42, "filter": "active"}
    sample_payload = db.Column(db.Text)

    enabled = db.Column(db.Boolean, default=True)

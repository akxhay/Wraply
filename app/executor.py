import httpx
import json
import asyncio
import base64
from urllib.parse import urlencode

try:
    import jmespath
    _JMESPATH_AVAILABLE = True
except ImportError:
    _JMESPATH_AVAILABLE = False


# ---------------------------------------------------------------------------
# JMESPath / dotpath resolver
# ---------------------------------------------------------------------------

def _resolve(source_expr: str, payload: dict):
    """
    Resolve a source expression against a payload dict.

    Supports:
    - JMESPath expressions (if jmespath is installed):  "user.name", "items[0].id"
    - Simple dot-path fallback:                         "user.name"
    - Literal values prefixed with "$LITERAL:":        "$LITERAL:hello"
    - Full passthrough sentinel:                        "$PASSTHROUGH"
    """
    if source_expr is None:
        return None

    if source_expr.startswith("$LITERAL:"):
        return source_expr[len("$LITERAL:"):]

    if payload is None:
        return None

    # Strip leading "$." for compatibility with both styles
    expr = source_expr.lstrip("$").lstrip(".")

    if _JMESPATH_AVAILABLE:
        try:
            return jmespath.search(expr, payload)
        except Exception:
            pass

    # Simple dot-path fallback
    keys = expr.split(".")
    result = payload
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return None
    return result


# ---------------------------------------------------------------------------
# Transformation helpers
# ---------------------------------------------------------------------------

def _build_headers(config, call_payload: dict) -> dict:
    """Merge static headers + auth header + dynamic header_transform."""
    headers = {}

    # 1. Static headers
    if config.headers:
        headers.update(json.loads(config.headers))

    # 2. Auth
    if config.auth_type == "bearer":
        headers["Authorization"] = f"Bearer {config.auth_value}"

    elif config.auth_type == "basic":
        # auth_value expected as "username:password"
        encoded = base64.b64encode(config.auth_value.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"

    elif config.auth_type == "api_key":
        header_name = config.auth_header_name or "X-API-Key"
        headers[header_name] = config.auth_value

    # 3. Dynamic header transform from payload
    if config.header_transform and call_payload:
        transform = json.loads(config.header_transform)
        for header_name, source_expr in transform.items():
            value = _resolve(source_expr, call_payload)
            if value is not None:
                headers[header_name] = str(value)

    return headers


def _build_url(config, call_payload: dict) -> str:
    """Interpolate path params into the URL template."""
    url = config.url  # e.g. https://api.example.com/users/{user_id}/posts/{post_id}

    if config.path_params_schema and call_payload:
        schema = json.loads(config.path_params_schema)
        for param in schema:
            name = param["name"]
            value = _resolve(param.get("source"), call_payload)
            if value is not None:
                url = url.replace(f"{{{name}}}", str(value))

    return url


def _build_query_params(config, call_payload: dict) -> dict:
    """Build query string params from static values and dynamic sources."""
    params = {}

    if config.query_params_schema:
        schema = json.loads(config.query_params_schema)
        for param in schema:
            name = param["name"]
            if "value" in param:
                # Static value
                params[name] = param["value"]
            elif "source" in param and call_payload:
                # Dynamic value from payload
                value = _resolve(param["source"], call_payload)
                if value is not None:
                    params[name] = value

    return params


def _build_body(config, call_payload: dict):
    """
    Transform the incoming call payload into the outgoing request body.

    - If body_transform is absent → pass payload as-is
    - If body_transform is {"$PASSTHROUGH": true} → pass payload as-is
    - Otherwise map fields according to the transform spec
    """
    if not config.body_transform:
        return call_payload

    transform = json.loads(config.body_transform)

    if transform.get("$PASSTHROUGH"):
        return call_payload

    body = {}
    for out_key, source_expr in transform.items():
        value = _resolve(source_expr, call_payload)
        if value is not None:
            body[out_key] = value

    return body


def _apply_response_transform(config, response_data: dict):
    """
    Transform the upstream response into the final response.

    - If response_transform is absent → return as-is
    - If response_transform is {"$PASSTHROUGH": true} → return as-is
    - Otherwise map fields according to the transform spec
    """
    if not config.response_transform:
        return response_data

    transform = json.loads(config.response_transform)

    if transform.get("$PASSTHROUGH"):
        return response_data

    result = {}
    for out_key, source_expr in transform.items():
        result[out_key] = _resolve(source_expr, response_data)

    return result


# ---------------------------------------------------------------------------
# Core executor
# ---------------------------------------------------------------------------

async def execute_api(config, payload: dict = None):
    """
    Execute the API call described by `config`, using `payload` as the
    source of dynamic values for all transformations.
    """
    headers = _build_headers(config, payload)
    url = _build_url(config, payload)
    query_params = _build_query_params(config, payload)
    body = _build_body(config, payload)

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(
            config.method,
            url,
            json=body if config.method.upper() not in ("GET", "HEAD", "DELETE") else None,
            params=query_params or None,
            headers=headers,
            timeout=10,
        )

    response.raise_for_status()
    data = response.json()

    return _apply_response_transform(config, data)


def execute_sync(config, payload: dict = None):
    return asyncio.run(execute_api(config, payload))

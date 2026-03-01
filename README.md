# API Wrapper Admin

A lightweight Flask-based API proxy and transformation engine. Define, store, and execute upstream API calls through a central admin interface — with full support for path params, query params, request body transforms, response transforms, header transforms, auth, and sample payloads.

---
https://duckxharma.pythonanywhere.com - pw - email

---
## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Database Migration](#database-migration)
- [Config Fields Reference](#config-fields-reference)
- [Transformation System](#transformation-system)
  - [Source Expressions](#source-expressions)
  - [Path Parameters](#path-parameters)
  - [Query Parameters](#query-parameters)
  - [Body Transform](#body-transform)
  - [Response Transform](#response-transform)
  - [Header Transform](#header-transform)
  - [Static Headers](#static-headers)
- [Auth Types](#auth-types)
- [Sample Payload](#sample-payload)
- [API Reference](#api-reference)
  - [Config Endpoints](#config-endpoints)
  - [Execute Endpoints](#execute-endpoints)
- [cURL Examples](#curl-examples)
  - [1. Simple GET — No Auth](#1-simple-get--no-auth)
  - [2. GET with Path Param + Query Params](#2-get-with-path-param--query-params)
  - [3. POST with Bearer Token + Body Transform](#3-post-with-bearer-token--body-transform)
  - [4. POST with Basic Auth](#4-post-with-basic-auth)
  - [5. GET with API Key Header](#5-get-with-api-key-header)
  - [6. PUT with Dynamic Header Transform](#6-put-with-dynamic-header-transform)
  - [7. DELETE with Path Param](#7-delete-with-path-param)
  - [8. Full Kitchen Sink](#8-full-kitchen-sink)
- [Admin UI](#admin-ui)
- [Feature Dots Legend](#feature-dots-legend)

---

## Overview

API Wrapper Admin lets you store upstream API configurations in a SQLite database and execute them by posting a payload. Every aspect of the request — URL, headers, query string, body, and response — can be transformed dynamically using dot-path or JMESPath expressions resolved against the incoming payload.

```
Your App  →  POST /execute/:id  { payload }
                ↓
         Transform payload into upstream request
                ↓
         Call upstream API
                ↓
         Transform upstream response
                ↓
         Return shaped response to your app
```

---

## Project Structure

```
app/
├── __init__.py          # App factory (create_app)
├── config.py            # SQLAlchemy config, DB path
├── database.py          # db = SQLAlchemy()
├── models.py            # APIConfig model
├── crud.py              # DB operations
├── executor.py          # HTTP execution + all transformations
├── utils.py             # serialize_model / serialize_list
└── routes/
    ├── config_routes.py # CRUD endpoints for configs
    └── execute_routes.py# Execute, sample, dry-run endpoints
templates/
├── index.html           # Landing page
└── configs.html         # Admin UI
run.py                   # Entry point
migrate.py               # DB migration for new columns
configs.db               # SQLite database (auto-created)
```

---

## Installation

```bash
# Clone / copy project files
cd your-project

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-sqlalchemy httpx

# Optional: install jmespath for advanced response path queries
pip install jmespath
```

---

## Running the App

```bash
python run.py
```

The server starts at `http://localhost:5000`.

- Landing page: `http://localhost:5000/`
- Admin UI: `http://localhost:5000/configs/ui`

---

## Database Migration

If you are upgrading an existing `configs.db` that was created before the transformation columns were added, run the migration script once:

```bash
python migrate.py
```

This safely `ALTER TABLE`s the existing table to add the 7 new columns without touching existing data.

For fresh installs, the database and all columns are created automatically on first startup via `db.create_all()`.

---

## Config Fields Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | ✅ | Unique identifier for this config |
| `url` | string | ✅ | URL template, supports `{param}` placeholders |
| `method` | string | ✅ | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `enabled` | boolean | | Whether this config can be executed. Default `true` |
| `auth_type` | string | | `bearer`, `basic`, `api_key`, or omit for none |
| `auth_value` | string | | Token, `user:pass`, or API key depending on auth type |
| `auth_header_name` | string | | Header name for `api_key` auth. Default `X-API-Key` |
| `headers` | JSON object | | Static headers always sent with the request |
| `header_transform` | JSON object | | Dynamic headers resolved from call payload |
| `path_params_schema` | JSON array | | Bindings for `{placeholder}` segments in the URL |
| `query_params_schema` | JSON array | | Static and dynamic query string parameters |
| `body_transform` | JSON object | | Maps call payload → outgoing request body |
| `response_transform` | JSON object | | Maps upstream response → returned response |
| `sample_payload` | JSON object | | Stored example payload used for sample runs and dry runs |

---

## Transformation System

All transformations use **source expressions** resolved against the incoming call payload.

### Source Expressions

| Expression | Behaviour | Example |
|---|---|---|
| `field` | Top-level key | `"user_id"` → `payload["user_id"]` |
| `parent.child` | Dot-path traversal | `"user.email"` → `payload["user"]["email"]` |
| `items[0].id` | JMESPath (requires `jmespath`) | First item's id from an array |
| `$LITERAL:value` | Hardcoded constant | `"$LITERAL:viewer"` → `"viewer"` |
| `$PASSTHROUGH` | Skip transform, use as-is | See Body / Response transform |

If `jmespath` is not installed, the system falls back to simple dot-path splitting.

---

### Path Parameters

Inject dynamic values into URL placeholders using `{param_name}` syntax.

**Schema format:** JSON array of objects.

| Key | Description |
|---|---|
| `name` | Matches the `{name}` placeholder in the URL |
| `source` | Source expression resolved against the call payload |

**Example:**

URL: `https://api.example.com/orgs/{org_id}/users/{user_id}`

```json
[
  { "name": "org_id",  "source": "org.id" },
  { "name": "user_id", "source": "user.id" }
]
```

Call payload `{ "org": { "id": "org_42" }, "user": { "id": "usr_7" } }` produces:

`https://api.example.com/orgs/org_42/users/usr_7`

---

### Query Parameters

Append static or dynamic query string parameters.

**Schema format:** JSON array of objects.

| Key | Description |
|---|---|
| `name` | Query parameter name |
| `value` | Static string value |
| `source` | Dynamic source expression from payload (overrides `value`) |

**Example:**

```json
[
  { "name": "limit",   "value": "10" },
  { "name": "status",  "source": "filter.status" },
  { "name": "page",    "source": "page" }
]
```

Call payload `{ "filter": { "status": "active" }, "page": 2 }` produces:

`?limit=10&status=active&page=2`

---

### Body Transform

Controls what the outgoing HTTP request body looks like.

**Format:** JSON object mapping output field names to source expressions.

```json
{
  "username":    "user.name",
  "email":       "user.email",
  "role":        "$LITERAL:viewer",
  "external_id": "meta.id"
}
```

**Passthrough** — forward the call payload as the request body without any mapping:

```json
{ "$PASSTHROUGH": true }
```

Omitting `body_transform` entirely also passes the payload through unchanged.

> For `GET`, `HEAD`, and `DELETE` methods the body is never sent regardless of this setting.

---

### Response Transform

Controls what your endpoint returns after receiving the upstream response.

**Format:** JSON object mapping output field names to source expressions (resolved against the upstream response body).

```json
{
  "userId":   "data.id",
  "fullName": "data.attributes.name",
  "email":    "data.attributes.email"
}
```

**Passthrough** — return the upstream response as-is:

```json
{ "$PASSTHROUGH": true }
```

Omitting `response_transform` also returns the raw upstream response.

---

### Header Transform

Dynamically inject request headers resolved from the call payload at runtime. Useful for multi-tenant systems where each call carries a tenant ID, user token, etc.

**Format:** JSON object mapping header names to source expressions.

```json
{
  "X-Tenant-Id":  "tenant_id",
  "X-User-Email": "user.email",
  "X-Request-Id": "meta.request_id"
}
```

These are merged on top of the static `headers` field (header transform values take precedence for the same key).

---

### Static Headers

Always-sent headers regardless of call payload. Defined as a plain JSON object.

```json
{
  "Content-Type":  "application/json",
  "X-App-Version": "3.0",
  "X-App-Id":      "my-service"
}
```

**Header merge order (highest wins):**

```
Static headers  →  Auth header  →  Header transform
```

---

## Auth Types

| `auth_type` | Behaviour | `auth_value` format |
|---|---|---|
| *(omitted)* | No auth header added | — |
| `bearer` | Adds `Authorization: Bearer <value>` | Raw token string |
| `basic` | Adds `Authorization: Basic <base64>` | `username:password` (plain text, encoded automatically) |
| `api_key` | Adds `<auth_header_name>: <value>` | Raw API key string |

For `api_key`, the header name defaults to `X-API-Key`. Override it with `auth_header_name`.

---

## Sample Payload

`sample_payload` is a stored JSON object used as the default payload for:

- `POST /execute/:id/sample` — run the config without providing a payload
- `POST /execute/:id/dry-run` — inspect the resolved request without making an HTTP call

You can override individual fields by including them in the request body — they are merged on top of the stored sample (request body takes precedence).

```bash
# Run with stored sample exactly as-is
curl -X POST http://localhost:5000/execute/1/sample \
  -H "Content-Type: application/json" \
  -d '{}'

# Override one field from the sample
curl -X POST http://localhost:5000/execute/1/sample \
  -H "Content-Type: application/json" \
  -d '{"user_id": 99}'
```

---

## API Reference

### Config Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/configs` | List all configs |
| `POST` | `/configs` | Create a new config |
| `PUT` | `/configs/:id` | Update an existing config |
| `DELETE` | `/configs/:id` | Delete a config |
| `PATCH` | `/configs/:id/toggle` | Toggle `enabled` on/off |
| `POST` | `/configs/:id/clone` | Clone a config (disabled by default) |
| `GET` | `/configs/ui` | Admin UI (HTML) |

**Create / Update body:** any combination of the fields from the [Config Fields Reference](#config-fields-reference).

**List response:**
```json
[
  {
    "id": 1,
    "name": "get_user",
    "url": "https://api.example.com/users/{user_id}",
    "method": "GET",
    "auth_type": "bearer",
    "enabled": true,
    ...
  }
]
```

---

### Execute Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/execute/:id` | Execute config with provided payload |
| `POST` | `/execute/:id/sample` | Execute using stored `sample_payload` (merged with request body) |
| `POST` | `/execute/:id/dry-run` | Return the resolved request without making the HTTP call |

All three accept a JSON body. For `/execute/:id`, the body is the full call payload. For `/sample` and `/dry-run`, it is an optional override merged on top of `sample_payload`.

**Dry-run response shape:**
```json
{
  "method": "POST",
  "url": "https://api.example.com/orgs/org_42/users/usr_7",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer tok_xyz",
    "X-Tenant-Id": "acme-corp"
  },
  "query_params": {
    "limit": "10",
    "status": "active"
  },
  "body": {
    "username": "Ada Lovelace",
    "email": "ada@acme.com",
    "role": "viewer"
  }
}
```

**Error responses:**

```json
{ "error": "Config not found or not enabled" }   // 404
{ "error": "<upstream error message>" }           // 500
```

---

## cURL Examples

All examples target `http://localhost:5000`. Replace IDs in execute calls with the `id` returned from the create call.

---

### 1. Simple GET — No Auth

Plain passthrough with no transforms.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_public_ip",
    "url": "https://httpbin.org/get",
    "method": "GET",
    "enabled": true
  }'

# Execute
curl -s -X POST http://localhost:5000/execute/1 \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 2. GET with Path Param + Query Params

URL uses `{user_id}` placeholder; appends static and dynamic query params.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_user_posts",
    "url": "https://jsonplaceholder.typicode.com/users/{user_id}/posts",
    "method": "GET",
    "path_params_schema":  "[{\"name\": \"user_id\", \"source\": \"user_id\"}]",
    "query_params_schema": "[{\"name\": \"_limit\", \"value\": \"5\"}, {\"name\": \"_page\", \"source\": \"page\"}]",
    "sample_payload": "{\"user_id\": 1, \"page\": 2}",
    "enabled": true
  }'

# Dry run — inspect resolved URL and params
curl -s -X POST http://localhost:5000/execute/2/dry-run \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3, "page": 1}'

# Execute with sample
curl -s -X POST http://localhost:5000/execute/2/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 3. POST with Bearer Token + Body Transform

Reshapes the call payload into the upstream request body. Maps the response.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "create_user_bearer",
    "url": "https://httpbin.org/post",
    "method": "POST",
    "auth_type": "bearer",
    "auth_value": "my-secret-token-abc123",
    "body_transform": "{\"username\": \"user.name\", \"email\": \"user.email\", \"role\": \"$LITERAL:viewer\"}",
    "response_transform": "{\"sentBody\": \"json\", \"requestUrl\": \"url\"}",
    "sample_payload": "{\"user\": {\"name\": \"Jane Doe\", \"email\": \"jane@acme.com\"}}",
    "enabled": true
  }'

# Execute with sample
curl -s -X POST http://localhost:5000/execute/3/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 4. POST with Basic Auth

`auth_value` is `username:password` — base64-encoded automatically.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "basic_auth_post",
    "url": "https://httpbin.org/post",
    "method": "POST",
    "auth_type": "basic",
    "auth_value": "admin:supersecret",
    "body_transform": "{\"$PASSTHROUGH\": true}",
    "sample_payload": "{\"action\": \"sync\", \"target\": \"db\"}",
    "enabled": true
  }'

# Execute
curl -s -X POST http://localhost:5000/execute/4/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 5. GET with API Key Header

Custom header name — useful for OpenWeatherMap, Stripe, etc.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weather_api",
    "url": "https://httpbin.org/get",
    "method": "GET",
    "auth_type": "api_key",
    "auth_value": "abc123weatherkey",
    "auth_header_name": "X-API-Key",
    "query_params_schema": "[{\"name\": \"city\", \"source\": \"city\"}, {\"name\": \"units\", \"value\": \"metric\"}]",
    "sample_payload": "{\"city\": \"London\"}",
    "enabled": true
  }'

# Execute
curl -s -X POST http://localhost:5000/execute/5/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 6. PUT with Dynamic Header Transform

Injects `X-Tenant-Id` and `X-User-Email` from the call payload at runtime.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "update_tenant_resource",
    "url": "https://httpbin.org/put",
    "method": "PUT",
    "auth_type": "bearer",
    "auth_value": "platform-level-token",
    "headers": "{\"Content-Type\": \"application/json\", \"X-App-Version\": \"2.1\"}",
    "header_transform": "{\"X-Tenant-Id\": \"tenant_id\", \"X-User-Email\": \"user.email\"}",
    "body_transform": "{\"resourceId\": \"resource.id\", \"payload\": \"resource.data\"}",
    "response_transform": "{\"echoedBody\": \"json\"}",
    "sample_payload": "{\"tenant_id\": \"acme-corp\", \"user\": {\"email\": \"ops@acme.com\"}, \"resource\": {\"id\": \"res_99\", \"data\": {\"status\": \"active\"}}}",
    "enabled": true
  }'

# Dry run — verify headers are resolved correctly
curl -s -X POST http://localhost:5000/execute/6/dry-run \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 7. DELETE with Path Param

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "delete_post",
    "url": "https://jsonplaceholder.typicode.com/posts/{post_id}",
    "method": "DELETE",
    "path_params_schema": "[{\"name\": \"post_id\", \"source\": \"post_id\"}]",
    "sample_payload": "{\"post_id\": 101}",
    "enabled": true
  }'

# Execute
curl -s -X POST http://localhost:5000/execute/7/sample \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 8. Full Kitchen Sink

Path params + query params + bearer auth + static headers + header transform + body transform + response transform + sample payload.

```bash
curl -s -X POST http://localhost:5000/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "full_kitchen_sink",
    "url": "https://httpbin.org/anything/{org_id}/users/{user_id}",
    "method": "POST",
    "auth_type": "bearer",
    "auth_value": "tok_live_xyz987",
    "headers": "{\"Content-Type\": \"application/json\", \"X-SDK-Version\": \"3.0\"}",
    "header_transform": "{\"X-Tenant\": \"org.slug\", \"X-Request-Id\": \"meta.request_id\"}",
    "path_params_schema": "[{\"name\": \"org_id\", \"source\": \"org.id\"}, {\"name\": \"user_id\", \"source\": \"user.id\"}]",
    "query_params_schema": "[{\"name\": \"expand\", \"value\": \"profile,roles\"}, {\"name\": \"locale\", \"source\": \"meta.locale\"}]",
    "body_transform": "{\"email\": \"user.email\", \"displayName\": \"user.name\", \"orgRole\": \"user.role\", \"source\": \"$LITERAL:api-wrapper\"}",
    "response_transform": "{\"echoedBody\": \"json\", \"requestUrl\": \"url\"}",
    "sample_payload": "{\"org\": {\"id\": \"org_42\", \"slug\": \"acme\"}, \"user\": {\"id\": \"usr_7\", \"name\": \"Ada Lovelace\", \"email\": \"ada@acme.com\", \"role\": \"admin\"}, \"meta\": {\"locale\": \"en-US\", \"request_id\": \"req_abc123\"}}",
    "enabled": true
  }'

# Dry run — see the fully resolved request
curl -s -X POST http://localhost:5000/execute/8/dry-run \
  -H "Content-Type: application/json" \
  -d '{}'

# Execute with stored sample
curl -s -X POST http://localhost:5000/execute/8/sample \
  -H "Content-Type: application/json" \
  -d '{}'

# Execute with a live override (merges on top of sample)
curl -s -X POST http://localhost:5000/execute/8/sample \
  -H "Content-Type: application/json" \
  -d '{"user": {"id": "usr_99", "name": "Override User", "email": "new@acme.com", "role": "viewer"}}'
```

---

## Admin UI

The web UI is served at `/configs/ui` and provides:

- **Table view** of all configs with method badges and feature indicator dots
- **5-tab modal** for creating and editing configs (Basic / Auth / Params / Transform / Sample)
- **Sample** button — runs the config using its stored `sample_payload`
- **Dry Run** button — shows the fully resolved request without making an HTTP call
- **Toggle** switch — enable/disable a config without deleting it
- **Clone** — duplicate a config (cloned configs are disabled by default)

---

## Feature Dots Legend

In the admin UI table, each config row displays 6 small dots indicating which features are configured:

| Position | Feature | Colour when active |
|---|---|---|
| 1 | Path params schema | Green |
| 2 | Query params schema | Green |
| 3 | Body transform | Green |
| 4 | Response transform | Green |
| 5 | Header transform | Green |
| 6 | Sample payload | Green |

A grey dot means that feature is not configured for that config.

---

## Quick Reference

```
Source expression syntax
────────────────────────
user_id              → payload["user_id"]
user.email           → payload["user"]["email"]
items[0].id          → payload["items"][0]["id"]   (JMESPath)
$LITERAL:admin       → "admin"  (hardcoded)
$PASSTHROUGH         → skip transform, use value as-is

Auth types
──────────
bearer    →  Authorization: Bearer <auth_value>
basic     →  Authorization: Basic base64(<auth_value>)
api_key   →  <auth_header_name>: <auth_value>

Header merge order (highest priority wins)
──────────────────────────────────────────
static headers  →  auth header  →  header_transform

Execute endpoints
─────────────────
POST /execute/:id            real call, full payload in body
POST /execute/:id/sample     real call, uses stored sample_payload
POST /execute/:id/dry-run    no HTTP call, returns resolved request
```

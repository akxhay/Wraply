import httpx
import json
import asyncio


async def execute_api(config, payload=None):

    headers = {}

    if config.headers:
        headers.update(json.loads(config.headers))

    if config.auth_type == "bearer":
        headers["Authorization"] = f"Bearer {config.auth_value}"

    async with httpx.AsyncClient() as client:
        response = await client.request(
            config.method,
            config.url,
            json=payload,
            headers=headers,
            timeout=10,
        )

    data = response.json()

    if config.response_mapping:
        mapping = json.loads(config.response_mapping)
        data = {k: data.get(v) for k, v in mapping.items()}

    return data


def execute_sync(config, payload=None):
    return asyncio.run(execute_api(config, payload))
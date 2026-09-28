"""Parse OpenAPI/Swagger specs and Postman collections into a normalised
endpoint list the scanner understands."""
import json
import re
from typing import Any

import yaml


def _load(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)


def _id_params(path: str, parameters: list) -> list[str]:
    """Path template parameters, e.g. {id} in /accounts/{id}."""
    ids = re.findall(r"\{([^}]+)\}", path)
    return ids


def _body_fields(operation: dict, root: dict) -> list[str]:
    """Best-effort list of request body property names (for mass-assignment tests)."""
    fields: list[str] = []
    body = operation.get("requestBody", {})
    content = body.get("content", {}) if isinstance(body, dict) else {}
    for media in content.values():
        schema = media.get("schema", {})
        schema = _resolve_ref(schema, root)
        props = schema.get("properties", {})
        fields.extend(props.keys())
    return sorted(set(fields))


def _resolve_ref(schema: dict, root: dict) -> dict:
    if not isinstance(schema, dict):
        return {}
    ref = schema.get("$ref")
    if ref and ref.startswith("#/"):
        node: Any = root
        for part in ref[2:].split("/"):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        return node if isinstance(node, dict) else {}
    return schema


def _base_url_from_openapi(spec: dict) -> str:
    servers = spec.get("servers") or []
    if servers and isinstance(servers, list):
        url = servers[0].get("url", "")
        if url:
            return url.rstrip("/")
    # Swagger 2.0
    host = spec.get("host")
    if host:
        scheme = (spec.get("schemes") or ["http"])[0]
        base = spec.get("basePath", "")
        return f"{scheme}://{host}{base}".rstrip("/")
    return ""


def parse_openapi(spec: dict) -> tuple[str, list[dict]]:
    base_url = _base_url_from_openapi(spec)
    endpoints: list[dict] = []
    paths = spec.get("paths", {}) or {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        common_params = item.get("parameters", [])
        for method, op in item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(op, dict):
                continue
            params = common_params + (op.get("parameters", []) or [])
            query_params = [
                p.get("name") for p in params
                if isinstance(p, dict) and p.get("in") == "query" and p.get("name")
            ]
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "id_params": _id_params(path, params),
                "query_params": query_params,
                "body_fields": _body_fields(op, spec),
                "summary": op.get("summary", "") or op.get("operationId", ""),
                "tags": op.get("tags", []),
                "security": op.get("security", spec.get("security", [])),
            })
    return base_url, endpoints


def parse_postman(collection: dict) -> tuple[str, list[dict]]:
    endpoints: list[dict] = []
    base_url = ""

    def walk(items: list):
        nonlocal base_url
        for it in items or []:
            if "item" in it:
                walk(it["item"])
                continue
            req = it.get("request")
            if not isinstance(req, dict):
                continue
            method = (req.get("method") or "GET").upper()
            url = req.get("url", {})
            if isinstance(url, str):
                raw = url
                path = "/" + "/".join(url.split("/")[3:]) if "://" in url else url
            else:
                raw = url.get("raw", "")
                path = "/" + "/".join(url.get("path", []))
            if raw and "://" in raw and not base_url:
                base_url = "/".join(raw.split("/")[:3])
            # Postman uses :param style for path variables.
            path = re.sub(r":([A-Za-z0-9_]+)", r"{\1}", path)
            body_fields: list[str] = []
            body = req.get("body", {})
            if body.get("mode") == "raw":
                try:
                    parsed = json.loads(body.get("raw", "") or "{}")
                    if isinstance(parsed, dict):
                        body_fields = list(parsed.keys())
                except json.JSONDecodeError:
                    pass
            endpoints.append({
                "method": method,
                "path": path or "/",
                "id_params": re.findall(r"\{([^}]+)\}", path),
                "query_params": [],
                "body_fields": body_fields,
                "summary": it.get("name", ""),
                "tags": [],
                "security": [],
            })

    walk(collection.get("item", []))
    return base_url, endpoints


def parse_spec(text: str) -> tuple[str, list[dict], str]:
    """Return (base_url, endpoints, kind). Raises ValueError on unparseable input."""
    data = _load(text)
    if not isinstance(data, dict):
        raise ValueError("Spec must be a JSON/YAML object")
    if "openapi" in data or "swagger" in data:
        base, eps = parse_openapi(data)
        return base, eps, "openapi"
    if "info" in data and "item" in data:
        base, eps = parse_postman(data)
        return base, eps, "postman"
    # Fall back: maybe it's already a bare list of endpoints.
    if "endpoints" in data and isinstance(data["endpoints"], list):
        return data.get("base_url", ""), data["endpoints"], "manual"
    raise ValueError("Unrecognised spec: expected OpenAPI, Swagger or Postman collection")

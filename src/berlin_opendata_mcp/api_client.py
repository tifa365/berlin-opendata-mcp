"""
Shared HTTP client and utilities for Berlin Open Data API.

Supported APIs:
- CKAN (datenregister.berlin.de) – Open Data catalog
"""

from typing import Any, Optional

import httpx

# ─── Constants ────────────────────────────────────────────────────────────────

CKAN_BASE_URL = "https://datenregister.berlin.de"
CKAN_API_URL = f"{CKAN_BASE_URL}/api/3/action"
PORTAL_URL = "https://daten.berlin.de"

REQUEST_TIMEOUT = 30.0
USER_AGENT = "BerlinOpenDataMCP/0.1 (MCP Server; +https://github.com/tifa365/berlin-opendata-mcp)"

BERLIN_GROUPS = [
    "arbeit",
    "bildung",
    "demographie",
    "erholung",
    "geo",
    "gesundheit",
    "gleichstellung",
    "jugend",
    "justiz",
    "kultur",
    "oeffentlich",
    "protokolle",
    "sicherheit",
    "sonstiges",
    "sozial",
    "tourismus",
    "transport",
    "umwelt",
    "verbraucher",
    "verentsorgung",
    "verkehr",
    "verwaltung",
    "wahl",
    "wirtschaft",
    "wohnen",
]


# ─── HTTP Client ──────────────────────────────────────────────────────────────


async def _get_client() -> httpx.AsyncClient:
    """Create a configured async HTTP client."""
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


async def ckan_request(action: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Make a CKAN API request and return the result.

    Args:
        action: CKAN API action name (e.g. 'package_search')
        params: Query parameters

    Returns:
        The 'result' field from the CKAN response

    Raises:
        RuntimeError: If the CKAN API returns an error
    """
    async with await _get_client() as client:
        url = f"{CKAN_API_URL}/{action}"
        response = await client.get(url, params=params or {})
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            error_msg = data.get("error", {}).get("message", "Unknown CKAN error")
            raise RuntimeError(f"CKAN API error: {error_msg}")

        return data["result"]


async def http_get_json(url: str, params: Optional[dict[str, Any]] = None) -> Any:
    """Generic JSON GET request."""
    async with await _get_client() as client:
        response = await client.get(url, params=params or {})
        response.raise_for_status()
        return response.json()


# ─── Formatting Helpers ───────────────────────────────────────────────────────


def format_dataset_summary(dataset: dict[str, Any]) -> str:
    """Format a CKAN dataset into a readable Markdown summary."""
    title = dataset.get("title", "Unbekannt")
    name = dataset.get("name", "")
    author = dataset.get("author", "Unbekannt")
    notes = (dataset.get("notes") or "")[:300]
    license_title = dataset.get("license_title", "Unbekannt")
    num_resources = dataset.get("num_resources", 0)
    modified = dataset.get("metadata_modified", "")[:10]
    groups = [g.get("title", g.get("name", "")) for g in dataset.get("groups", [])]
    tags = [t.get("display_name", t.get("name", "")) for t in dataset.get("tags", [])]

    # Berlin-specific extras
    extras = {e["key"]: e["value"] for e in dataset.get("extras", [])}
    berlin_type = extras.get("berlin_type", "")
    geo_coverage = extras.get("geographical_coverage", "")
    date_updated = extras.get("date_updated", "")

    url = f"{PORTAL_URL}/datensaetze/{name}"

    lines = [
        f"### {title}",
        f"- **ID**: `{name}`",
        f"- **Autor**: {author}",
        f"- **Lizenz**: {license_title}",
        f"- **Ressourcen**: {num_resources}",
        f"- **Letzte Aenderung**: {modified}",
    ]
    if berlin_type:
        lines.append(f"- **Typ**: {berlin_type}")
    if date_updated:
        lines.append(f"- **Daten aktualisiert**: {date_updated}")
    if geo_coverage:
        lines.append(f"- **Raeumliche Abdeckung**: {geo_coverage}")
    if groups:
        lines.append(f"- **Kategorien**: {', '.join(groups)}")
    if tags:
        lines.append(f"- **Tags**: {', '.join(tags[:10])}")
    if notes:
        lines.append(f"- **Beschreibung**: {notes}...")
    lines.append(f"- **URL**: {url}")

    return "\n".join(lines)


def format_resource_info(resource: dict[str, Any]) -> str:
    """Format a CKAN resource into a readable summary."""
    return (
        f"  - **{resource.get('name', 'Unbenannt')}** "
        f"({resource.get('format', '?')}) – "
        f"{resource.get('url', 'Keine URL')}"
    )


def handle_api_error(e: Exception, context: str = "") -> str:
    """Consistent error formatting."""
    prefix = f"Fehler bei {context}: " if context else "Fehler: "
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return f"{prefix}Ressource nicht gefunden. Bitte ID/Name pruefen."
        elif status == 403:
            return f"{prefix}Zugriff verweigert."
        elif status == 429:
            return f"{prefix}Zu viele Anfragen. Bitte warten."
        return f"{prefix}HTTP-Fehler {status}"
    elif isinstance(e, httpx.TimeoutException):
        return f"{prefix}Zeitueberschreitung. Bitte erneut versuchen."
    return f"{prefix}{type(e).__name__}: {e}"

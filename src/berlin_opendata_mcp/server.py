"""
Berlin Open Data MCP Server
============================
MCP Server fuer den Zugriff auf Open Data des Landes Berlin.
Integriert CKAN (datenregister.berlin.de) fuer 2500+ Datensaetze.
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .api_client import (
    BERLIN_GROUPS,
    PORTAL_URL,
    ckan_request,
    format_dataset_summary,
    format_resource_info,
    handle_api_error,
)

# ─── Server Setup ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "berlin_opendata_mcp",
    instructions=(
        "MCP Server fuer Open Data des Landes Berlin. "
        "Bietet Zugriff auf 2500+ Datensaetze via CKAN API (datenregister.berlin.de). "
        "Kategorien: Arbeit, Bildung, Demographie, Gesundheit, Kultur, "
        "Umwelt, Verkehr, Verwaltung, Wirtschaft, Wohnen u.v.m. "
        "Daten unter verschiedenen offenen Lizenzen (CC0, CC-BY, dl-de-zero-2.0, dl-de-by-2.0)."
    ),
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CKAN TOOLS – Datensatz-Suche und -Exploration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SearchDatasetsInput(BaseModel):
    """Input fuer die Datensatz-Suche."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="Suchbegriff(e), z.B. 'Einwohner', 'Verkehr', 'Kita'. "
        "Unterstuetzt Solr-Syntax: AND, OR, NOT, Wildcards (*), Fuzzy (~).",
        min_length=1,
        max_length=500,
    )
    rows: int = Field(default=10, description="Anzahl Ergebnisse (max. 50)", ge=1, le=50)
    offset: int = Field(default=0, description="Offset fuer Paginierung", ge=0)
    sort: Optional[str] = Field(
        default=None,
        description="Sortierung, z.B. 'metadata_modified desc', 'title asc', 'score desc'",
    )
    filter_group: Optional[str] = Field(
        default=None,
        description=f"Nach Kategorie filtern. Verfuegbar: {', '.join(BERLIN_GROUPS)}",
    )


@mcp.tool(
    name="berlin_search_datasets",
    annotations={
        "title": "Datensaetze suchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_search_datasets(params: SearchDatasetsInput) -> str:
    """Durchsucht den Open-Data-Katalog des Landes Berlin nach Datensaetzen.

    Nutzt die CKAN-Suchmaschine (Solr) fuer Volltextsuche ueber Titel,
    Beschreibung, Tags und Metadaten aller 2500+ Datensaetze.

    Returns:
        Markdown-formatierte Liste mit Datensatz-Zusammenfassungen
    """
    try:
        api_params: dict = {
            "q": params.query,
            "rows": params.rows,
            "start": params.offset,
        }
        if params.sort:
            api_params["sort"] = params.sort
        if params.filter_group:
            api_params["fq"] = f"groups:{params.filter_group}"

        result = await ckan_request("package_search", api_params)
        total = result["count"]
        datasets = result["results"]

        if not datasets:
            return f"Keine Datensaetze gefunden fuer '{params.query}'."

        lines = [
            f"## Suchergebnis: {total} Datensaetze fuer '{params.query}'",
            f"Zeige {len(datasets)} von {total} (Offset: {params.offset})\n",
        ]
        for ds in datasets:
            lines.append(format_dataset_summary(ds))
            lines.append("")

        if total > params.offset + len(datasets):
            lines.append(f"*→ Weitere Ergebnisse mit offset={params.offset + len(datasets)}*")

        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Datensatzsuche")


class GetDatasetInput(BaseModel):
    """Input fuer Datensatz-Details."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dataset_id: str = Field(
        ...,
        description="ID oder Name des Datensatzes, z.B. 'einwohnerinnen-und-einwohner-berlin-lor-planungsraeume'",
        min_length=1,
    )


@mcp.tool(
    name="berlin_get_dataset",
    annotations={
        "title": "Datensatz-Details abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_get_dataset(params: GetDatasetInput) -> str:
    """Ruft vollstaendige Metadaten und Ressourcen eines Datensatzes ab.

    Gibt Titel, Beschreibung, Autor, Lizenz, alle verfuegbaren
    Dateiformate und Download-URLs zurueck.

    Returns:
        Detaillierte Markdown-Ansicht des Datensatzes mit allen Ressourcen
    """
    try:
        result = await ckan_request("package_show", {"id": params.dataset_id})

        lines = [format_dataset_summary(result), "\n#### Ressourcen / Downloads\n"]
        for res in result.get("resources", []):
            lines.append(format_resource_info(res))

        # Extra metadata
        extras = {e["key"]: e["value"] for e in result.get("extras", [])}
        if extras:
            lines.append("\n#### Zusaetzliche Metadaten")
            for k, v in extras.items():
                if not k.startswith("harvest"):
                    lines.append(f"- **{k}**: {v}")

        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Datensatz-Details")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CKAN TOOLS – Kategorien und Tags
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ListGroupInput(BaseModel):
    """Input fuer Gruppen-/Kategorie-Details."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    group_id: Optional[str] = Field(
        default=None,
        description=f"Gruppen-ID fuer Details. Verfuegbar: {', '.join(BERLIN_GROUPS)}. "
        "Wenn leer, werden alle Kategorien aufgelistet.",
    )


@mcp.tool(
    name="berlin_list_categories",
    annotations={
        "title": "Datenkategorien auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_list_categories(params: ListGroupInput) -> str:
    """Listet alle Datenkategorien (Gruppen) im Katalog auf oder zeigt Details einer Kategorie.

    Das Land Berlin organisiert seine Datensaetze in 25 thematische Kategorien
    wie Bildung, Demographie, Verkehr, Umwelt etc.

    Returns:
        Markdown-Liste der Kategorien mit Datensatz-Anzahl
    """
    try:
        if params.group_id:
            result = await ckan_request(
                "group_show",
                {
                    "id": params.group_id,
                    "include_datasets": True,
                    "include_dataset_count": True,
                },
            )
            lines = [
                f"## Kategorie: {result['title']}",
                f"**Datensaetze**: {result.get('package_count', 0)}\n",
            ]
            for ds in result.get("packages", []):
                lines.append(f"- **{ds['title']}** (`{ds['name']}`)")
            return "\n".join(lines)
        else:
            result = await ckan_request("group_list", {"all_fields": True, "include_dataset_count": True})
            lines = ["## Datenkategorien des Landes Berlin\n"]
            for group in result:
                count = group.get("package_count", 0)
                lines.append(f"- **{group['title']}** (`{group['name']}`) – {count} Datensaetze")
            return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Kategorien")


class TagSearchInput(BaseModel):
    """Input fuer Tag-Suche."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: Optional[str] = Field(
        default=None,
        description="Suchbegriff fuer Tags, z.B. 'einwohner', 'bezirk', 'kita'",
    )
    limit: int = Field(default=30, description="Maximale Anzahl Tags", ge=1, le=100)


@mcp.tool(
    name="berlin_list_tags",
    annotations={
        "title": "Tags durchsuchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_list_tags(params: TagSearchInput) -> str:
    """Durchsucht verfuegbare Tags im Open-Data-Katalog.

    Tags helfen, thematisch verwandte Datensaetze zu finden.
    Z.B. 'einwohner', 'bezirk', 'kita' fuer verschiedene Themenbereiche.

    Returns:
        Liste passender Tags
    """
    try:
        api_params: dict = {}
        if params.query:
            api_params["query"] = params.query

        result = await ckan_request("tag_list", api_params)

        if not result:
            return f"Keine Tags gefunden fuer '{params.query}'."

        tags = result[: params.limit]
        lines = [f"## Tags ({len(tags)} Ergebnisse)\n"]
        for tag in tags:
            lines.append(f"- `{tag}`")

        lines.append("\n*Tipp: Nutze `berlin_search_datasets` mit `filter_group` oder Solr-Query `tags:tagname`*")
        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Tag-Suche")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYSE-TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AnalyzeDatasetInput(BaseModel):
    """Input fuer Datensatz-Analyse."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="Suchbegriff fuer die Analyse, z.B. 'Einwohner', 'Verkehr', 'Wohnen'",
        min_length=1,
    )
    max_datasets: int = Field(default=5, description="Maximale Anzahl zu analysierender Datensaetze", ge=1, le=20)
    include_structure: bool = Field(default=True, description="Ressourcen-Formate einschliessen")
    include_freshness: bool = Field(default=True, description="Aktualitaets-Analyse einschliessen")


@mcp.tool(
    name="berlin_analyze_datasets",
    annotations={
        "title": "Datensaetze analysieren",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_analyze_datasets(params: AnalyzeDatasetInput) -> str:
    """Analysiert Datensaetze umfassend: Relevanz, Aktualitaet und verfuegbare Formate.

    Kombiniert Suche mit Analyse der Metadaten und Ressourcen-Formate.
    Besonders nuetzlich um herauszufinden, welche Daten verfuegbar sind
    und wie aktuell sie sind.

    Hinweis: Berlins CKAN hat keinen DataStore – Daten muessen ueber
    die Ressourcen-URLs heruntergeladen werden.

    Returns:
        Umfassender Analyse-Report mit Relevanz, Aktualitaet und Formaten
    """
    try:
        result = await ckan_request(
            "package_search",
            {
                "q": params.query,
                "rows": params.max_datasets,
                "sort": "score desc",
            },
        )
        datasets = result["results"]
        total = result["count"]

        if not datasets:
            return f"Keine Datensaetze gefunden fuer '{params.query}'."

        lines = [
            f"## Analyse: '{params.query}'",
            f"**{total} Datensaetze gefunden**, Top {len(datasets)} analysiert:\n",
        ]

        for i, ds in enumerate(datasets, 1):
            name = ds.get("name", "")
            title = ds.get("title", "?")
            modified = ds.get("metadata_modified", "?")[:10]
            resources = ds.get("resources", [])
            formats = sorted(set(r.get("format", "?") for r in resources))

            # Berlin-specific extras
            extras = {e["key"]: e["value"] for e in ds.get("extras", [])}
            date_updated = extras.get("date_updated", "")
            geo_coverage = extras.get("geographical_coverage", "")

            lines.append(f"### {i}. {title}")
            lines.append(f"- **ID**: `{name}`")
            lines.append(f"- **Formate**: {', '.join(formats)}")
            lines.append(f"- **Ressourcen**: {len(resources)}")

            if params.include_freshness:
                lines.append(f"- **Letzte Aenderung**: {modified}")
                if date_updated:
                    lines.append(f"- **Daten aktualisiert**: {date_updated}")

            if params.include_structure:
                for res in resources:
                    res_format = res.get("format", "?")
                    res_name = res.get("name", "Unbenannt")
                    res_url = res.get("url", "")
                    lines.append(f"  - {res_name} ({res_format}): {res_url}")

            if geo_coverage:
                lines.append(f"- **Raeumliche Abdeckung**: {geo_coverage}")

            lines.append(f"- **URL**: {PORTAL_URL}/datensaetze/{name}\n")

        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Datensatz-Analyse")


@mcp.tool(
    name="berlin_catalog_stats",
    annotations={
        "title": "Katalog-Statistiken",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def berlin_catalog_stats() -> str:
    """Gibt einen Ueberblick ueber den gesamten Open-Data-Katalog des Landes Berlin.

    Zeigt Gesamtzahl der Datensaetze, Verteilung nach Kategorien,
    haeufigste Formate und Tags.

    Returns:
        Statistik-Uebersicht des Katalogs
    """
    try:
        result = await ckan_request(
            "package_search",
            {
                "q": "*:*",
                "rows": 0,
                "facet.field": '["groups", "res_format", "tags"]',
                "facet.limit": "15",
            },
        )
        total = result["count"]
        facets = result.get("search_facets", result.get("facets", {}))

        lines = [
            "## Open Data Katalog – Land Berlin",
            f"**Gesamtzahl Datensaetze**: {total}\n",
            f"**Portal**: {PORTAL_URL}",
            "**Lizenzen**: CC0, CC-BY, Datenlizenz Deutschland (Zero/Namensnennung), GeoNutzV u.a.\n",
        ]

        # Groups
        if "groups" in facets:
            lines.append("### Kategorien")
            groups = facets["groups"]
            if isinstance(groups, dict):
                items = groups.get("items", [])
            else:
                items = groups if isinstance(groups, list) else []
            for item in sorted(items, key=lambda x: x.get("count", 0), reverse=True):
                lines.append(f"- **{item.get('display_name', item.get('name', '?'))}**: {item.get('count', 0)}")

        # Formats
        if "res_format" in facets:
            lines.append("\n### Haeufigste Formate")
            fmts = facets["res_format"]
            if isinstance(fmts, dict):
                items = fmts.get("items", [])
            else:
                items = fmts if isinstance(fmts, list) else []
            for item in sorted(items, key=lambda x: x.get("count", 0), reverse=True)[:10]:
                lines.append(f"- **{item.get('display_name', item.get('name', '?'))}**: {item.get('count', 0)}")

        return "\n".join(lines)

    except Exception as e:
        return handle_api_error(e, "Katalog-Statistiken")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESOURCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.resource("berlin://dataset/{name}")
async def get_dataset_resource(name: str) -> str:
    """Datensatz-Metadaten als MCP Resource."""
    result = await ckan_request("package_show", {"id": name})
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


@mcp.resource("berlin://category/{group_id}")
async def get_category_resource(group_id: str) -> str:
    """Kategorie-Details als MCP Resource."""
    result = await ckan_request(
        "group_show",
        {
            "id": group_id,
            "include_datasets": True,
        },
    )
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRYPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    """Start the Berlin Open Data MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

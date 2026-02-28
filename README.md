# Berlin Open Data MCP Server

MCP Server fuer den Zugriff auf Open Data des Landes Berlin. Bietet 6 Tools fuer CKAN-Katalogsuche, Analyse und Exploration ueber 2500+ Datensaetze.

## Features

- **6 MCP Tools** fuer Datensatz-Suche, Details, Kategorien, Tags, Analyse und Katalog-Statistiken
- **2 MCP Resources** fuer direkten Zugriff auf Datensaetze und Kategorien
- **2500+ Datensaetze** ueber die CKAN API (datenregister.berlin.de)
- **25 Kategorien**: Arbeit, Bildung, Demographie, Gesundheit, Kultur, Umwelt, Verkehr, Verwaltung, Wirtschaft, Wohnen u.v.m.

## Installation

```bash
uv sync
```

## Verwendung

### Stdio (lokal, z.B. Claude Desktop)

```bash
uv run berlin-opendata-mcp
```

### SSE (remote)

```bash
MCP_TRANSPORT=sse MCP_PORT=8000 uv run berlin-opendata-mcp
```

## Konfiguration

### Claude Desktop

Editiere die Claude Desktop Config:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "berlin-opendata": {
      "command": "uv",
      "args": ["run", "berlin-opendata-mcp"],
      "env": {}
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add berlin-opendata -- uv run berlin-opendata-mcp
```

### Cursor / Windsurf / VS Code

Fuege zu `.cursor/mcp.json` bzw. `.vscode/settings.json` hinzu:

```json
{
  "mcpServers": {
    "berlin-opendata": {
      "command": "uv",
      "args": ["run", "berlin-opendata-mcp"]
    }
  }
}
```

### Remote (SSE) – z.B. fuer ChatGPT, Open WebUI

```bash
MCP_TRANSPORT=sse MCP_PORT=8000 uv run berlin-opendata-mcp
```

Dann den SSE-Endpunkt `http://localhost:8000/sse` im Client eintragen.

## Beispiel-Abfragen

Nach der Konfiguration kannst du den AI-Assistenten fragen:

- *"Welche Datensaetze gibt es zu Kitas in Berlin?"*
- *"Zeig mir die Kategorien im Berliner Open-Data-Katalog"*
- *"Wie viele Datensaetze hat Berlin insgesamt?"*
- *"Finde Datensaetze zum Thema Einwohner in Berlin"*
- *"Welche Datenformate sind im Berliner Katalog am haeufigsten?"*

## Tools

| Tool | Beschreibung |
|------|-------------|
| `berlin_search_datasets` | Volltextsuche ueber 2500+ Datensaetze (Solr-Syntax) |
| `berlin_get_dataset` | Vollstaendige Metadaten + Download-URLs eines Datensatzes |
| `berlin_list_categories` | 25 thematische Kategorien durchsuchen |
| `berlin_list_tags` | Tag-basierte Suche |
| `berlin_analyze_datasets` | Relevanz-, Aktualitaets- und Format-Analyse |
| `berlin_catalog_stats` | Katalog-Uebersicht mit Statistiken |

## Resources

| URI | Beschreibung |
|-----|-------------|
| `berlin://dataset/{name}` | Datensatz-Metadaten (JSON) |
| `berlin://category/{group_id}` | Kategorie-Details mit Datensaetzen |

## Kategorien

`arbeit`, `bildung`, `demographie`, `erholung`, `geo`, `gesundheit`, `gleichstellung`, `jugend`, `justiz`, `kultur`, `oeffentlich`, `protokolle`, `sicherheit`, `sonstiges`, `sozial`, `tourismus`, `transport`, `umwelt`, `verbraucher`, `verentsorgung`, `verkehr`, `verwaltung`, `wahl`, `wirtschaft`, `wohnen`

## Hinweise

- **Kein DataStore**: Berlins CKAN dient als Katalog mit Download-Links. Daten muessen ueber Ressourcen-URLs heruntergeladen werden.
- **Lizenzen**: CC0, CC-BY, Datenlizenz Deutschland (Zero/Namensnennung), GeoNutzV u.a.
- **API**: `datenregister.berlin.de/api/3/action/` (oeffentlich, keine Authentifizierung)
- **Portal**: [daten.berlin.de](https://daten.berlin.de)

## Entwicklung

```bash
uv run ruff check src/
uv run ruff format src/
uv run pytest --asyncio-mode=auto tests/
```

## Lizenz

MIT

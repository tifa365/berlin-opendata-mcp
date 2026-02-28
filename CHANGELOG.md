# Changelog

## 0.1.0 (2026-02-28)

### Erste Version

- 6 MCP Tools fuer CKAN-Katalogsuche und -Exploration
  - `berlin_search_datasets` – Volltextsuche (Solr)
  - `berlin_get_dataset` – Datensatz-Details und Download-URLs
  - `berlin_list_categories` – 25 Kategorien durchsuchen
  - `berlin_list_tags` – Tag-basierte Suche
  - `berlin_analyze_datasets` – Relevanz- und Aktualitaetsanalyse
  - `berlin_catalog_stats` – Katalog-Statistiken
- 2 MCP Resources (`berlin://dataset/{name}`, `berlin://category/{group_id}`)
- Integration mit CKAN API (datenregister.berlin.de)
- 2500+ Datensaetze des Landes Berlin
- Docker- und Render.com-Deployment
- Integration Tests gegen Live-API

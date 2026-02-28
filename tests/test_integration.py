"""
Integration tests for Berlin Open Data MCP Server.
Tests all tools against the live CKAN API.
"""

import asyncio
import sys

# Add src to path
sys.path.insert(0, "src")

from berlin_opendata_mcp.server import (
    AnalyzeDatasetInput,
    GetDatasetInput,
    ListGroupInput,
    SearchDatasetsInput,
    TagSearchInput,
    berlin_analyze_datasets,
    berlin_catalog_stats,
    berlin_get_dataset,
    berlin_list_categories,
    berlin_list_tags,
    berlin_search_datasets,
)


async def test_search():
    print("=" * 60)
    print("TEST 1: berlin_search_datasets('Einwohner')")
    print("=" * 60)
    result = await berlin_search_datasets(SearchDatasetsInput(query="Einwohner", rows=3))
    print(result[:500])
    assert "Datensaetze" in result or "Einwohner" in result
    print("PASSED\n")


async def test_get_dataset():
    print("=" * 60)
    print("TEST 2: berlin_get_dataset('kurse')")
    print("=" * 60)
    result = await berlin_get_dataset(GetDatasetInput(dataset_id="kurse"))
    print(result[:500])
    assert "Volkshochschule" in result or "Kurse" in result or "kurse" in result
    print("PASSED\n")


async def test_categories():
    print("=" * 60)
    print("TEST 3: berlin_list_categories() - all")
    print("=" * 60)
    result = await berlin_list_categories(ListGroupInput())
    print(result[:500])
    assert "Bildung" in result
    assert "Demographie" in result or "demographie" in result.lower()
    print("PASSED\n")


async def test_category_bildung():
    print("=" * 60)
    print("TEST 4: berlin_list_categories('bildung')")
    print("=" * 60)
    result = await berlin_list_categories(ListGroupInput(group_id="bildung"))
    print(result[:500])
    assert "Bildung" in result
    print("PASSED\n")


async def test_tags():
    print("=" * 60)
    print("TEST 5: berlin_list_tags('einwohner')")
    print("=" * 60)
    result = await berlin_list_tags(TagSearchInput(query="einwohner"))
    print(result[:400])
    assert "einwohner" in result.lower()
    print("PASSED\n")


async def test_analyze():
    print("=" * 60)
    print("TEST 6: berlin_analyze_datasets('Verkehr')")
    print("=" * 60)
    result = await berlin_analyze_datasets(AnalyzeDatasetInput(query="Verkehr", max_datasets=3, include_structure=True))
    print(result[:600])
    assert "Analyse" in result
    print("PASSED\n")


async def test_catalog_stats():
    print("=" * 60)
    print("TEST 7: berlin_catalog_stats()")
    print("=" * 60)
    result = await berlin_catalog_stats()
    print(result[:600])
    assert "Katalog" in result
    print("PASSED\n")


async def main():
    print("\nBerlin Open Data MCP Server – Integration Tests\n")

    tests = [
        test_search,
        test_get_dataset,
        test_categories,
        test_category_bildung,
        test_tags,
        test_analyze,
        test_catalog_stats,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"FAILED: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Ergebnis: {passed} bestanden, {failed} fehlgeschlagen von {len(tests)}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

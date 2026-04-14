"""Lightweight tests (no LLM / Neo4j required)."""

from cybereye4_wrapper.engine import _normalize_object_information


def test_normalize_simple_string_values():
    d = _normalize_object_information(
        {"forklift": "color: blue, region hint: Warehouse"},
        current_region="Warehouse",
    )
    assert "forklift" in d
    assert d["forklift"][0]["information"] == "color: blue, region hint: Warehouse"
    assert d["forklift"][0]["region"] == "Warehouse"


def test_normalize_list_of_dicts():
    d = _normalize_object_information(
        {
            "panel": [
                {"object": "panel", "region": "A", "information": "speed: 1.0"},
            ]
        },
        current_region=None,
    )
    assert d["panel"][0]["information"] == "speed: 1.0"

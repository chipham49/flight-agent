"""Smoke test for the web UI: the page loads without errors (free, no API calls)."""
from streamlit.testing.v1 import AppTest


def test_ui_page_loads():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert not at.exception
    assert "Cheapest Flight Finder" in at.title[0].value
    assert any(b.label == "Save preferences" for b in at.button)

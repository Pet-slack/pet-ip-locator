"""
tests/test_app.py
Unit tests for the IP Locator Flask application.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Make sure app.py is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, get_ip_info


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


MOCK_SUCCESS = {
    "status": "success",
    "country": "United States",
    "countryCode": "US",
    "region": "CA",
    "regionName": "California",
    "city": "Mountain View",
    "zip": "94043",
    "lat": 37.4056,
    "lon": -122.0775,
    "timezone": "America/Los_Angeles",
    "isp": "Google LLC",
    "org": "Google Public DNS",
    "as": "AS15169 Google LLC",
    "query": "8.8.8.8",
}

MOCK_FAIL = {
    "status": "fail",
    "message": "private range",
    "query": "192.168.1.1",
}


# ── Unit tests: get_ip_info ───────────────────────────────────────────────────

class TestGetIpInfo:
    @patch("app.requests.get")
    def test_successful_lookup(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SUCCESS
        mock_get.return_value = mock_resp

        result = get_ip_info("8.8.8.8")

        assert result["ip"] == "8.8.8.8"
        assert result["country"] == "United States"
        assert result["country_code"] == "US"
        assert result["city"] == "Mountain View"
        assert result["lat"] == 37.4056
        assert result["isp"] == "Google LLC"

    @patch("app.requests.get")
    def test_failed_lookup_private_ip(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_FAIL
        mock_get.return_value = mock_resp

        result = get_ip_info("192.168.1.1")

        assert "error" in result
        assert result["error"] == "private range"

    @patch("app.requests.get")
    def test_timeout(self, mock_get):
        import requests as req_module
        mock_get.side_effect = req_module.exceptions.Timeout()

        result = get_ip_info("8.8.8.8")

        assert "error" in result
        assert "timed out" in result["error"]

    @patch("app.requests.get")
    def test_connection_error(self, mock_get):
        import requests as req_module
        mock_get.side_effect = req_module.exceptions.ConnectionError()

        result = get_ip_info("8.8.8.8")

        assert "error" in result
        assert "Connection" in result["error"]


# ── Integration tests: routes ─────────────────────────────────────────────────

class TestRoutes:
    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    @patch("app.get_ip_info")
    def test_lookup_with_ip_param(self, mock_info, client):
        mock_info.return_value = {"ip": "8.8.8.8", "country": "US"}
        r = client.get("/api/lookup?ip=8.8.8.8")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["ip"] == "8.8.8.8"

    @patch("app.get_ip_info")
    @patch("app.get_client_ip")
    def test_lookup_without_ip_uses_client_ip(self, mock_client_ip, mock_info, client):
        mock_client_ip.return_value = "1.2.3.4"
        mock_info.return_value = {"ip": "1.2.3.4"}
        r = client.get("/api/lookup")
        assert r.status_code == 200
        mock_info.assert_called_once_with("1.2.3.4")

    def test_my_ip_endpoint(self, client):
        r = client.get("/api/my-ip")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "ip" in data


# ── Build script test ─────────────────────────────────────────────────────────

class TestBuildScript:
    def test_build_creates_dist(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib, build_static
        importlib.reload(build_static)
        build_static.build()

        dist = tmp_path / "dist"
        assert dist.exists()
        assert (dist / "index.html").exists()
        assert (dist / ".nojekyll").exists()

    def test_index_html_has_required_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import importlib, build_static
        importlib.reload(build_static)
        build_static.build()

        content = (tmp_path / "dist" / "index.html").read_text()
        assert "IP Locator" in content
        assert "ip-api.com" in content
        assert "lookupIP" in content

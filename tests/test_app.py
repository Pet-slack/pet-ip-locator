"""
tests/test_app.py
Unit tests for the IP Locator Flask application (ipinfo.io backend).
"""

import pytest
import importlib
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Make sure app.py is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, get_ip_info


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ipinfo.io success response shape
MOCK_SUCCESS = {
    "ip": "8.8.8.8",
    "hostname": "dns.google",
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "loc": "37.4056,-122.0775",
    "org": "AS15169 Google LLC",
    "postal": "94043",
    "timezone": "America/Los_Angeles",
}

# ipinfo.io error response shape (e.g. private/reserved range)
MOCK_FAIL = {
    "ip": "192.168.1.1",
    "error": {
        "title": "Wrong ip",
        "message": "192.168.1.1 is a private IP address",
    },
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
        assert result["country_code"] == "US"
        assert result["city"] == "Mountain View"
        assert result["region"] == "California"
        assert result["zip"] == "94043"
        assert result["lat"] == 37.4056
        assert result["lon"] == -122.0775
        assert result["timezone"] == "America/Los_Angeles"
        assert result["org"] == "AS15169 Google LLC"
        assert result["hostname"] == "dns.google"

    @patch("app.requests.get")
    def test_loc_is_split_into_lat_lon(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {**MOCK_SUCCESS, "loc": "51.5074,-0.1278"}
        mock_get.return_value = mock_resp

        result = get_ip_info("1.2.3.4")

        assert result["lat"] == 51.5074
        assert result["lon"] == -0.1278

    @patch("app.requests.get")
    def test_missing_loc_returns_none(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {k: v for k, v in MOCK_SUCCESS.items() if k != "loc"}
        mock_get.return_value = mock_resp

        result = get_ip_info("8.8.8.8")

        assert result["lat"] is None
        assert result["lon"] is None

    @patch("app.requests.get")
    def test_isp_is_none_on_free_tier(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SUCCESS
        mock_get.return_value = mock_resp

        result = get_ip_info("8.8.8.8")

        assert result["isp"] is None  # not provided on free tier

    @patch("app.requests.get")
    def test_failed_lookup_private_ip(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_FAIL
        mock_get.return_value = mock_resp

        result = get_ip_info("192.168.1.1")

        assert "error" in result
        assert "private IP" in result["error"]

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

    @patch("app.requests.get")
    def test_http_error_is_caught(self, mock_get):
        import requests as req_module
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.side_effect = req_module.exceptions.HTTPError(response=mock_resp)

        result = get_ip_info("8.8.8.8")

        assert "error" in result
        assert "429" in result["error"]

    @patch("app.requests.get")
    def test_token_sent_in_auth_header(self, mock_get, monkeypatch):
        monkeypatch.setenv("IPINFO_TOKEN", "test-token-123")
        import app as app_module
        importlib.reload(app_module)

        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SUCCESS
        mock_get.return_value = mock_resp

        app_module.get_ip_info("8.8.8.8")

        _, kwargs = mock_get.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-token-123"

    @patch("app.requests.get")
    def test_no_token_omits_auth_header(self, mock_get, monkeypatch):
        monkeypatch.delenv("IPINFO_TOKEN", raising=False)
        import app as app_module
        importlib.reload(app_module)

        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_SUCCESS
        mock_get.return_value = mock_resp

        app_module.get_ip_info("8.8.8.8")

        _, kwargs = mock_get.call_args
        assert "Authorization" not in kwargs["headers"]


# ── Integration tests: routes ─────────────────────────────────────────────────

class TestRoutes:
    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    @patch("app.get_ip_info")
    def test_lookup_with_ip_param(self, mock_info, client):
        mock_info.return_value = {"ip": "8.8.8.8", "country_code": "US"}
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


# ── Build script tests ────────────────────────────────────────────────────────

class TestBuildScript:
    def test_build_creates_dist(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import build_static
        importlib.reload(build_static)
        build_static.build()

        dist = tmp_path / "dist"
        assert dist.exists()
        assert (dist / "index.html").exists()
        assert (dist / ".nojekyll").exists()

    def test_index_html_has_required_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import build_static
        importlib.reload(build_static)
        build_static.build()

        content = (tmp_path / "dist" / "index.html").read_text()
        assert "IP Locator" in content
        assert "ipinfo.io" in content
        assert "lookupIP" in content

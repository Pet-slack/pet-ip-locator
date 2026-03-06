from flask import Flask, render_template, jsonify, request
import requests
import os

app = Flask(__name__)

# Optional: set IPINFO_TOKEN env var for higher rate limits (50k/mo free without token)
IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN", "")


def get_ip_info(ip: str) -> dict:
    """Fetch geolocation data for a given IP address using ipinfo.io."""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        headers = {"Accept": "application/json"}
        if IPINFO_TOKEN:
            headers["Authorization"] = f"Bearer {IPINFO_TOKEN}"

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        # ipinfo.io returns {"error": {"title": ..., "message": ...}} for invalid IPs
        if "error" in data:
            err = data["error"]
            return {"error": err.get("message", "Lookup failed"), "ip": ip}

        # ipinfo.io returns "loc" as "lat,lon" string
        lat, lon = None, None
        if loc := data.get("loc"):
            parts = loc.split(",")
            if len(parts) == 2:
                lat, lon = float(parts[0]), float(parts[1])

        # ipinfo.io returns "country" as a 2-letter code (e.g. "US")
        # and does not include the full country name on the free tier
        country_code = data.get("country", "")

        return {
            "ip": data.get("ip", ip),
            "country": data.get("country_name") or country_code,
            "country_code": country_code,
            "region": data.get("region"),
            "region_code": None,          # not provided by ipinfo.io free tier
            "city": data.get("city"),
            "zip": data.get("postal"),
            "lat": lat,
            "lon": lon,
            "timezone": data.get("timezone"),
            "isp": None,                  # available on paid plans only
            "org": data.get("org"),       # e.g. "AS15169 Google LLC"
            "as": data.get("org"),
            "hostname": data.get("hostname"),
        }
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "ip": ip}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error", "ip": ip}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}", "ip": ip}
    except Exception as e:
        return {"error": str(e), "ip": ip}


def get_client_ip() -> str:
    """Detect the real client IP from request headers."""
    for header in ("X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return request.remote_addr


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/lookup", methods=["GET"])
def lookup():
    ip = request.args.get("ip", "").strip()
    if not ip:
        ip = get_client_ip()
    data = get_ip_info(ip)
    return jsonify(data)


@app.route("/api/my-ip", methods=["GET"])
def my_ip():
    ip = get_client_ip()
    return jsonify({"ip": ip})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


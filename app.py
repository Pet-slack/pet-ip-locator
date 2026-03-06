from flask import Flask, render_template, jsonify, request
import requests
import json

app = Flask(__name__)

def get_ip_info(ip: str) -> dict:
    """Fetch geolocation data for a given IP address."""
    try:
        # Using ip-api.com free tier (no API key needed)
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
            timeout=5
        )
        data = response.json()

        if data.get("status") == "fail":
            return {"error": data.get("message", "Lookup failed"), "ip": ip}

        return {
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "region_code": data.get("region"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "as": data.get("as"),
        }
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "ip": ip}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error", "ip": ip}
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

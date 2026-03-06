# 🌐 IP Locator

[![Build & Deploy to GitHub Pages](https://github.com/Pet-slack/pet-ip-locator/actions/workflows/deploy.yml/badge.svg)](https://github.com/Pet-slack/pet-ip-locator/actions/workflows/deploy.yml)

A Python-powered IP geolocation tool with a dark-mode UI — deployable to **GitHub Pages** in seconds using GitHub Actions.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Architecture

```
ip-locator/
├── app.py                        # Flask backend (local dev & server deploy)
├── build_static.py               # Generates dist/ for GitHub Pages
├── requirements.txt
├── pytest.ini
├── templates/
│   └── index.html                # Jinja2 template (Flask version)
├── tests/
│   └── test_app.py               # Pytest unit + integration tests
└── .github/
    └── workflows/
        └── deploy.yml            # CI/CD: test → build → deploy
```

### Two deployment modes

| Mode | Command | Notes |
|------|---------|-------|
| **Local Flask** | `python app.py` | Full Python backend, proxies ip-api.com |
| **GitHub Pages** | push to `main` | Static HTML, calls ip-api.com directly from browser |

---

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ip-locator.git
cd ip-locator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Flask server
python app.py
# → http://localhost:5000
```

### API Endpoints (Flask mode)

```
GET /api/lookup?ip=8.8.8.8   # Lookup any IP
GET /api/lookup               # Lookup your own IP
GET /api/my-ip                # Just return your IP address
```

---

## Deploy to GitHub Pages

### Step 1 — Create a GitHub repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ip-locator.git
git push -u origin main
```

### Step 2 — Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. Save

### Step 3 — Push & watch it deploy!

Every push to `main` will:
1. ✅ Run Python tests (`pytest`)
2. 🏗️ Build the static site (`python build_static.py`)
3. 🚀 Deploy `dist/` to GitHub Pages

Your site will be live at:
```
https://YOUR_USERNAME.github.io/ip-locator/
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest
```

Test coverage:
- `get_ip_info()` — success, failure, timeout, connection error
- Flask routes — `/`, `/api/lookup`, `/api/my-ip`
- `build_static.py` — generates correct `dist/` output

---

## How It Works

### GitHub Actions Pipeline (`.github/workflows/deploy.yml`)

```
Push to main
     │
     ▼
┌─────────┐    ┌───────────┐    ┌──────────┐
│  Test   │───▶│   Build   │───▶│  Deploy  │
│ pytest  │    │ build_    │    │ Pages    │
│         │    │ static.py │    │ Action   │
└─────────┘    └───────────┘    └──────────┘
```

### Data Flow

```
Browser → ip-api.com (free tier, no key needed) → JSON → Rendered UI
                                                       ↓
                                              OpenStreetMap iframe
```

---

## Customization

### Use a different geo API

Edit the fetch URL in `build_static.py` and `app.py`. Popular alternatives:
- [ipinfo.io](https://ipinfo.io) — free tier, 50k/month
- [ipgeolocation.io](https://ipgeolocation.io) — more fields
- [abstractapi.com](https://www.abstractapi.com/ip-geolocation-api) — SSL on free tier

### Run on a server (not Pages)

```bash
gunicorn app:app --bind 0.0.0.0:8000 --workers 2
```

---

## License

MIT — use freely, attribution appreciated.

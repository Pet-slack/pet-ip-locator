#!/usr/bin/env python3
"""
build_static.py
Generates a fully self-contained static site (index.html) for GitHub Pages.
The static site uses ip-api.com directly from the browser (no Python backend needed).
"""

import os
import shutil

DIST_DIR = "dist"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IP Locator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #060810;
      --surface: #0d1117;
      --border: #1e2533;
      --accent: #00e5ff;
      --accent2: #7b61ff;
      --warn: #ff4d6d;
      --text: #e2e8f0;
      --muted: #64748b;
      --card: #111827;
    }

    html, body {
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: 'Syne', sans-serif;
      overflow-x: hidden;
    }

    /* ── Grid background ── */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(0,229,255,.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,255,.04) 1px, transparent 1px);
      background-size: 48px 48px;
      pointer-events: none;
      z-index: 0;
    }

    /* ── Glow orbs ── */
    .orb {
      position: fixed;
      border-radius: 50%;
      filter: blur(120px);
      opacity: .25;
      pointer-events: none;
      z-index: 0;
    }
    .orb-1 { width: 600px; height: 600px; background: var(--accent2); top: -200px; right: -100px; }
    .orb-2 { width: 500px; height: 500px; background: var(--accent);  bottom: -150px; left: -100px; }

    /* ── Layout ── */
    .container {
      position: relative;
      z-index: 1;
      max-width: 780px;
      margin: 0 auto;
      padding: 48px 24px 80px;
    }

    /* ── Header ── */
    header {
      text-align: center;
      margin-bottom: 52px;
    }
    .logo {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .logo-icon {
      width: 44px; height: 44px;
      border: 2px solid var(--accent);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 22px;
      box-shadow: 0 0 20px rgba(0,229,255,.3);
    }
    h1 {
      font-size: clamp(2rem, 5vw, 3.2rem);
      font-weight: 800;
      letter-spacing: -1px;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .tagline {
      color: var(--muted);
      font-family: 'Space Mono', monospace;
      font-size: .85rem;
      margin-top: 8px;
      letter-spacing: .5px;
    }

    /* ── Search bar ── */
    .search-wrap {
      display: flex;
      gap: 12px;
      margin-bottom: 36px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 8px;
      transition: border-color .2s;
    }
    .search-wrap:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(0,229,255,.1);
    }
    #ip-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text);
      font-family: 'Space Mono', monospace;
      font-size: 1rem;
      padding: 10px 14px;
      letter-spacing: 1px;
    }
    #ip-input::placeholder { color: var(--muted); }
    #lookup-btn {
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #060810;
      font-family: 'Syne', sans-serif;
      font-weight: 700;
      font-size: .9rem;
      border: none;
      border-radius: 10px;
      padding: 12px 28px;
      cursor: pointer;
      transition: opacity .2s, transform .1s;
      white-space: nowrap;
      letter-spacing: .5px;
    }
    #lookup-btn:hover { opacity: .88; }
    #lookup-btn:active { transform: scale(.97); }
    #lookup-btn:disabled { opacity: .4; cursor: default; }

    /* ── My IP pill ── */
    .my-ip-bar {
      text-align: center;
      margin-bottom: 32px;
      font-family: 'Space Mono', monospace;
      font-size: .85rem;
      color: var(--muted);
    }
    .my-ip-bar span {
      color: var(--accent);
      cursor: pointer;
      text-decoration: underline dotted;
      font-weight: 700;
    }

    /* ── Result card ── */
    #result {
      opacity: 0;
      transform: translateY(16px);
      transition: opacity .4s ease, transform .4s ease;
    }
    #result.visible {
      opacity: 1;
      transform: translateY(0);
    }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
    }

    .card-header {
      padding: 24px 28px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .ip-badge {
      font-family: 'Space Mono', monospace;
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: 1px;
    }
    .flag {
      font-size: 2rem;
      line-height: 1;
    }
    .location-line {
      color: var(--muted);
      font-size: .9rem;
      margin-top: 4px;
    }

    /* ── Grid of fields ── */
    .fields {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1px;
      background: var(--border);
    }
    .field {
      background: var(--card);
      padding: 20px 24px;
      transition: background .2s;
    }
    .field:hover { background: #161d2b; }
    .field-label {
      font-family: 'Space Mono', monospace;
      font-size: .7rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-bottom: 6px;
    }
    .field-value {
      font-size: .95rem;
      font-weight: 600;
      color: var(--text);
      word-break: break-all;
    }
    .field-value.mono {
      font-family: 'Space Mono', monospace;
      font-size: .85rem;
    }

    /* ── Map ── */
    #map-wrap {
      border-top: 1px solid var(--border);
      position: relative;
      height: 280px;
      overflow: hidden;
    }
    #map-wrap iframe {
      width: 100%; height: 100%; border: none;
      filter: invert(90%) hue-rotate(180deg) brightness(0.85) saturate(1.3);
    }
    .map-pin {
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -100%);
      font-size: 2.2rem;
      pointer-events: none;
      filter: drop-shadow(0 4px 8px rgba(0,0,0,.6));
      animation: bounce .6s ease infinite alternate;
    }
    @keyframes bounce {
      from { transform: translate(-50%, -100%); }
      to   { transform: translate(-50%, -120%); }
    }

    /* ── Error ── */
    .error-card {
      background: rgba(255,77,109,.08);
      border: 1px solid rgba(255,77,109,.3);
      border-radius: 14px;
      padding: 24px;
      display: flex;
      align-items: center;
      gap: 14px;
      color: var(--warn);
      font-weight: 600;
    }

    /* ── Loader ── */
    .loader {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 40px;
      color: var(--muted);
      font-family: 'Space Mono', monospace;
      font-size: .85rem;
    }
    .dot {
      width: 8px; height: 8px;
      background: var(--accent);
      border-radius: 50%;
      animation: pulse 1.2s ease infinite;
    }
    .dot:nth-child(2) { animation-delay: .2s; }
    .dot:nth-child(3) { animation-delay: .4s; }
    @keyframes pulse {
      0%,100% { opacity: .2; transform: scale(.8); }
      50%      { opacity: 1;  transform: scale(1.2); }
    }

    /* ── Footer ── */
    footer {
      text-align: center;
      margin-top: 52px;
      color: var(--muted);
      font-size: .8rem;
      font-family: 'Space Mono', monospace;
    }
    footer a { color: var(--accent2); text-decoration: none; }
  </style>
</head>
<body>
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>

  <div class="container">
    <header>
      <div class="logo">
        <div class="logo-icon">🌐</div>
        <h1>IP Locator</h1>
      </div>
      <p class="tagline">// geolocate any IPv4 or IPv6 address instantly</p>
    </header>

    <div class="search-wrap">
      <input id="ip-input" type="text" placeholder="Enter IP address  e.g. 8.8.8.8" autocomplete="off" spellcheck="false" />
      <button id="lookup-btn" onclick="lookupIP()">Locate →</button>
    </div>

    <div class="my-ip-bar">
      Your IP: <span id="my-ip-label" onclick="lookupMyIP()">detecting…</span>
    </div>

    <div id="result"></div>

    <footer>
      powered by <a href="https://ip-api.com" target="_blank">ip-api.com</a> &nbsp;·&nbsp;
      built with Python + GitHub Actions
    </footer>
  </div>

  <script>
    const resultEl = document.getElementById('result');
    const inputEl  = document.getElementById('ip-input');
    const btnEl    = document.getElementById('lookup-btn');

    // ── Detect visitor's own IP on load ──────────────────────────────────────
    async function detectMyIP() {
      try {
        const r = await fetch('https://api.ipify.org?format=json');
        const d = await r.json();
        document.getElementById('my-ip-label').textContent = d.ip;
        return d.ip;
      } catch {
        document.getElementById('my-ip-label').textContent = 'unknown';
      }
    }

    async function lookupMyIP() {
      const label = document.getElementById('my-ip-label').textContent;
      if (label && label !== 'detecting…' && label !== 'unknown') {
        inputEl.value = label;
        await lookupIP();
      }
    }

    // ── Country code → emoji flag ─────────────────────────────────────────────
    function flagEmoji(cc) {
      if (!cc) return '🌍';
      return [...cc.toUpperCase()]
        .map(c => String.fromCodePoint(0x1F1E6 - 65 + c.charCodeAt(0)))
        .join('');
    }

    // ── Show loading state ────────────────────────────────────────────────────
    function showLoader() {
      resultEl.innerHTML = `
        <div class="loader">
          <div class="dot"></div><div class="dot"></div><div class="dot"></div>
          &nbsp; Locating…
        </div>`;
      resultEl.classList.add('visible');
    }

    // ── Main lookup ───────────────────────────────────────────────────────────
    async function lookupIP() {
      const ip = inputEl.value.trim();
      btnEl.disabled = true;
      showLoader();

      try {
        const target = ip || '';
        const url = `https://ip-api.com/json/${target}?fields=status,message,country,countryCode,regionName,region,city,zip,lat,lon,timezone,isp,org,as,query`;
        const r = await fetch(url);
        const d = await r.json();

        if (d.status === 'fail') {
          showError(d.message || 'Lookup failed', ip);
        } else {
          showResult(d);
        }
      } catch (err) {
        showError('Network error – please try again.', ip);
      } finally {
        btnEl.disabled = false;
      }
    }

    // ── Render result ─────────────────────────────────────────────────────────
    function showResult(d) {
      const fields = [
        { label: 'Country',   value: d.country,     },
        { label: 'Region',    value: d.regionName,  },
        { label: 'City',      value: d.city,        },
        { label: 'ZIP Code',  value: d.zip || '—',  },
        { label: 'Timezone',  value: d.timezone,    mono: true },
        { label: 'Latitude',  value: d.lat,         mono: true },
        { label: 'Longitude', value: d.lon,         mono: true },
        { label: 'ISP',       value: d.isp,         },
        { label: 'Org',       value: d.org,         },
        { label: 'AS',        value: d.as,          mono: true },
      ];

      const fieldsHTML = fields.map(f => `
        <div class="field">
          <div class="field-label">${f.label}</div>
          <div class="field-value ${f.mono ? 'mono' : ''}">${f.value || '—'}</div>
        </div>`).join('');

      const mapSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${d.lon-1},${d.lat-1},${d.lon+1},${d.lat+1}&layer=mapnik&marker=${d.lat},${d.lon}`;

      resultEl.classList.remove('visible');
      resultEl.innerHTML = `
        <div class="card">
          <div class="card-header">
            <div>
              <div class="ip-badge">${d.query}</div>
              <div class="location-line">${[d.city, d.regionName, d.country].filter(Boolean).join(', ')}</div>
            </div>
            <div class="flag">${flagEmoji(d.countryCode)}</div>
          </div>
          <div class="fields">${fieldsHTML}</div>
          <div id="map-wrap">
            <iframe src="${mapSrc}" loading="lazy"></iframe>
          </div>
        </div>`;

      requestAnimationFrame(() => resultEl.classList.add('visible'));
    }

    // ── Render error ──────────────────────────────────────────────────────────
    function showError(msg, ip) {
      resultEl.classList.remove('visible');
      resultEl.innerHTML = `
        <div class="error-card">
          <span style="font-size:1.6rem">⚠️</span>
          <div>
            <div>${msg}</div>
            ${ip ? `<div style="font-family:monospace;font-size:.8rem;opacity:.7;margin-top:4px">${ip}</div>` : ''}
          </div>
        </div>`;
      requestAnimationFrame(() => resultEl.classList.add('visible'));
    }

    // ── Enter key ─────────────────────────────────────────────────────────────
    inputEl.addEventListener('keydown', e => { if (e.key === 'Enter') lookupIP(); });

    // ── Init ──────────────────────────────────────────────────────────────────
    (async () => {
      const ip = await detectMyIP();
      if (ip) { inputEl.value = ip; await lookupIP(); }
    })();
  </script>
</body>
</html>
"""


def build():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)

    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(HTML)

    # GitHub Pages needs a .nojekyll file to serve files correctly
    open(os.path.join(DIST_DIR, ".nojekyll"), "w").close()

    print(f"✅  Static site built → ./{DIST_DIR}/index.html")


if __name__ == "__main__":
    build()

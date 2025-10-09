import os
import ssl
import json
import random
import time
import sys
"""
import tempfile
import threading
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from typing import Any, Deque
from botocore.exceptions import ClientError

# Build metadata injected at image build time via Dockerfile args
APP_BUILD = os.getenv("APP_BUILD", "dev")
APP_BUILD_DATE = os.getenv("APP_BUILD_DATE", "")

# ── OpenAPI spec --------------------------------------------------------
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "VOLTTRON VEN Agent", "version": "1.0.0"},
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {"200": {"description": "Service healthy"}}
            }
        },
        "/config": {
            "get": {
                "summary": "Get current VEN configuration",
                "responses": {"200": {"description": "Current settings"}}
            },
            "post": {
                "summary": "Update VEN behaviour (interval/target)",
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "report_interval_seconds": {"type": "integer", "minimum": 1},
                                    "target_power_kw": {"type": "number"},
                                    "enabled": {"type": "boolean"},
                                    "meter_base_min_kw": {"type": "number", "minimum": 0},
                                    "meter_base_max_kw": {"type": "number", "minimum": 0},
                                    "meter_jitter_pct": {"type": "number", "minimum": 0, "maximum": 1},
                                    "voltage_enabled": {"type": "boolean"},
                                    "voltage_nominal": {"type": "number", "minimum": 1},
                                    "voltage_jitter_pct": {"type": "number", "minimum": 0, "maximum": 1},
                                    "current_enabled": {"type": "boolean"},
                                    "power_factor": {"type": "number", "minimum": 0.05, "maximum": 1}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Applied and published"}}
            }
        },
        "/live": {
            "get": {
                "summary": "Live panel snapshot (status+config+metering)",
                "responses": {"200": {"description": "Live snapshot"}}
            }
        },
        "/circuits": {
            "get": {
                "summary": "List circuits",
                "responses": {"200": {"description": "Circuits list"}}
            }
        },
        "/circuits/{id}": {
            "get": {
                "summary": "Get a circuit by id",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Circuit detail"}, "404": {"description": "Not found"}}
            },
            "post": {
                "summary": "Update a circuit (enabled, rated_kw)",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {"required": False, "content": {"application/json": {"schema": {"type": "object", "properties": {"enabled": {"type": "boolean"}, "rated_kw": {"type": "number", "minimum": 0}}}}}},
                "responses": {"200": {"description": "Updated"}, "404": {"description": "Not found"}}
            }
        }
    },
}

SWAGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css">
</head>
<body>
  <div style="position:fixed;top:0;left:0;right:0;background:#0b5;color:#fff;padding:8px 12px;z-index:99;">
    <strong>VOLTTRON VEN</strong>
    <a href="/ui" style="color:#fff;margin-left:12px;text-decoration:underline;">Control UI</a>
    <a href="/config" style="color:#fff;margin-left:12px;text-decoration:underline;">Current Config (JSON)</a>
  </div>
  <div id="swagger-ui" style="margin-top:48px;"></div>
  <script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => { SwaggerUIBundle({ url: '/openapi.json', dom_id: '#swagger-ui' }); };
  </script>
</body>
</html>
"""

CONFIG_UI_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\"/>
  <title>VEN Control</title>
  <style>
    :root { --bg:#0b5; --card:#fff; --muted:#666; --accent:#0b5; }
    body { font-family: system-ui, sans-serif; margin: 0; line-height: 1.4; background:#f6f8fa; }
    header { background: var(--bg); color:#fff; padding:12px 16px; position:sticky; top:0; display:flex; align-items:center; gap:12px; }
    header a { color:#fff; margin-left: 12px; text-decoration: underline; }
    main { max-width: 960px; margin: 24px auto; padding: 0 16px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
    .card { background: var(--card); border-radius: 10px; padding:16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    .card h2 { margin:0 0 8px; font-size:1.1rem; }
    .field { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:8px 0; }
    .field label { color: var(--muted); }
    .field input[type=\"number\"] { width: 140px; padding: 6px 8px; border:1px solid #ddd; border-radius:8px; }
    .field input[type=\"checkbox\"] { transform: scale(1.2); }
    .actions { display:flex; gap:12px; margin-top:12px; }
    button { background: var(--accent); color:#fff; border:0; border-radius:8px; padding:8px 14px; cursor:pointer; }
    button.secondary { background:#222; }
    .status { margin-top: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space:pre-wrap; }
    /* Live panel styles */
    .panelbox { background:#111; color:#fff; border-radius:12px; padding:16px; box-shadow:inset 0 0 0 2px #000, 0 10px 24px rgba(0,0,0,.25); }
    .led { display:inline-block; width:12px; height:12px; border-radius:50%; box-shadow:0 0 6px rgba(0,0,0,.5); margin-right:6px; vertical-align:middle; }
    .ok { background:#2ecc71; }
    .bad { background:#e74c3c; }
    .meter { display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .big { font-size:2.2rem; font-weight:700; letter-spacing: .5px; }
    .muted { color:#bbb; }
    .kv { display:flex; gap:12px; flex-wrap:wrap; }
    .kv div { background:rgba(255,255,255,.05); padding:8px 10px; border-radius:8px; min-width: 120px; text-align:center; }
    .eventbar { background:#222; color:#eee; border-radius:8px; padding:10px 12px; display:flex; gap:16px; align-items:center; margin-top:10px; }
    .pill { background:#0b5; color:#fff; padding:4px 8px; border-radius:999px; font-size:.8rem; }
    .badge { background:#e67e22; color:#fff; padding:2px 6px; border-radius:6px; font-size:.75rem; margin-left:8px; }
    .build { margin-left:auto; font-size:.8rem; opacity:.9; }
    .gauge { margin-top:10px; width:100%; height:14px; background:#333; border-radius:7px; overflow:hidden; box-shadow: inset 0 0 4px rgba(0,0,0,.5); }
    .bar { height:100%; background: linear-gradient(90deg,#2ecc71,#f1c40f,#e74c3c); width:0%; transition: width .4s ease; }
  </style>
  <script>
    async function loadCurrent(){
      const r = await fetch('/config');
      if(!r.ok) return;
      const j = await r.json();
      document.getElementById('interval').value = j.report_interval_seconds ?? '';
      document.getElementById('target').value   = j.target_power_kw ?? '';
      document.getElementById('enabled').checked = !!j.enabled;
      // Metering knobs
      document.getElementById('base_min').value = j.meter_base_min_kw ?? 0.5;
      document.getElementById('base_max').value = j.meter_base_max_kw ?? 2.0;
      document.getElementById('jitter').value   = (j.meter_jitter_pct ?? 0.05);
      // Voltage
      document.getElementById('v_enabled').checked = !!j.voltage_enabled;
      document.getElementById('v_nom').value = j.voltage_nominal ?? 120.0;
      document.getElementById('v_jitter').value = (j.voltage_jitter_pct ?? 0.02);
      // Current
      document.getElementById('i_enabled').checked = !!j.current_enabled;
      document.getElementById('pf').value = j.power_factor ?? 1.0;
      document.getElementById('status').textContent = 'Current: ' + JSON.stringify(j, null, 2);
    }
    async function applyChanges(){
      const interval = document.getElementById('interval').value;
      const target   = document.getElementById('target').value;
      const enabled  = document.getElementById('enabled').checked;
      const body = {};
      if(interval) body.report_interval_seconds = Number(interval);
      if(target)   body.target_power_kw = Number(target);
      body.enabled = enabled;
      // Metering knobs
      body.meter_base_min_kw = Number(document.getElementById('base_min').value);
      body.meter_base_max_kw = Number(document.getElementById('base_max').value);
      body.meter_jitter_pct  = Number(document.getElementById('jitter').value);
      // Voltage knobs
      body.voltage_enabled   = document.getElementById('v_enabled').checked;
      body.voltage_nominal   = Number(document.getElementById('v_nom').value);
      body.voltage_jitter_pct= Number(document.getElementById('v_jitter').value);
      // Current knobs
      body.current_enabled   = document.getElementById('i_enabled').checked;
      body.power_factor      = Number(document.getElementById('pf').value);
      const r = await fetch('/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)});
      const j = await r.json().catch(()=>({}));
      document.getElementById('status').textContent = 'Response: ' + JSON.stringify(j, null, 2);
    }
    function applyPreset(){
      const name = document.getElementById('preset').value;
      fetch('/presets/apply', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name}) })
        .then(()=>{ loadCurrent(); refreshLive(); })
        .catch(()=>{});
    }
    function startVen(){ fetch('/config', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({enabled:true})}).then(()=>refreshLive()).catch(()=>{}); }
    function stopVen(){ fetch('/config', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({enabled:false})}).then(()=>refreshLive()).catch(()=>{}); }
    async function refreshLive(){
      try {
        const r = await fetch('/live');
        if(!r.ok) return;
        const j = await r.json();
        const enabled = !!(j.config && j.config.enabled);
        const connected = !!(j.status && j.status.ok);
        document.getElementById('led-enabled').className = 'led ' + (enabled? 'ok':'bad');
        document.getElementById('led-mqtt').className = 'led ' + (connected? 'ok':'bad');
        document.getElementById('live-power').textContent = j.metering && j.metering.power_kw != null ? j.metering.power_kw.toFixed(2) : '--';
        document.getElementById('live-voltage').textContent = j.metering && j.metering.voltage_v != null ? j.metering.voltage_v.toFixed(1) : '--';
        document.getElementById('live-current').textContent = j.metering && j.metering.current_a != null ? j.metering.current_a.toFixed(2) : '--';
        document.getElementById('live-target').textContent = (j.config && j.config.target_power_kw != null) ? j.config.target_power_kw : '--';
        document.getElementById('live-interval').textContent = (j.config && j.config.report_interval_seconds) ? j.config.report_interval_seconds : '--';
        const last = (j.events && j.events.event_id) ? `${j.events.event_id}` : '—';
        document.getElementById('live-event').textContent = last;
        document.getElementById('live-last-publish').textContent = j.status && j.status.last_publish_at ? j.status.last_publish_at : '—';
      } catch(e){ /* ignore */ }
    }
    function toggleCircuit(id, enabled){
      fetch('/circuits/'+encodeURIComponent(id), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({enabled}) })
        .then(()=>refreshLive()).catch(()=>{});
    }
    function toggleCritical(id, critical){
      fetch('/circuits/'+encodeURIComponent(id), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({critical}) })
        .then(()=>refreshLive()).catch(()=>{});
    }
    function toggleConnected(id, connected){
      fetch('/circuits/'+encodeURIComponent(id), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({connected}) })
        .then(()=>refreshLive()).catch(()=>{});
    }
    function setMode(id, mode){
      fetch('/circuits/'+encodeURIComponent(id), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode}) })
        .then(()=>refreshLive()).catch(()=>{});
    }
    function setFixedKw(id, v){
      const fixed_kw = Number(v||0);
      fetch('/circuits/'+encodeURIComponent(id), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({fixed_kw}) })
        .then(()=>refreshLive()).catch(()=>{});
    }
    function renderCircuits(list){
      const box = document.getElementById('circuits');
      if(!box) return;
      box.innerHTML = '';
      const shedding = new Set((window.__sheddingIds||[]));
      (list||[]).forEach(c => {
        const el = document.createElement('div');
        el.className = 'card';
        const shed = shedding.has(c.id) ? '<span class="badge">Shed</span>' : '';
        el.innerHTML = `
          <h2>${c.name} <span class="muted" style="font-weight:400">(${c.type||''})</span> ${shed}</h2>
          <div class="field"><label>Connected</label><input type="checkbox" ${c.connected!==false? 'checked':''} onchange="toggleConnected('${c.id}', this.checked)"></div>
          <div class="field"><label>Mode</label>
            <div>
              <select onchange="setMode('${c.id}', this.value)">
                <option value="dynamic" ${c.mode==='dynamic'?'selected':''}>Dynamic</option>
                <option value="fixed" ${c.mode==='fixed'?'selected':''}>Fixed</option>
              </select>
              <input type="number" step="0.01" min="0" value="${(c.fixedKw??0)}" onblur="setFixedKw('${c.id}', this.value)" style="width:100px; margin-left:8px;" />
            </div>
          </div>
          <div class="field"><label>Status</label><input type="checkbox" ${c.enabled? 'checked':''} onchange="toggleCircuit('${c.id}', this.checked)"></div>
          <div class="field"><label>Critical</label><input type="checkbox" ${c.critical? 'checked':''} onchange="toggleCritical('${c.id}', this.checked)"></div>
          <div class="field"><label>Rated</label><div>${(c.rated_kw??0).toFixed ? c.rated_kw.toFixed(2) : c.rated_kw} kW</div></div>
          <div class="field"><label>Now</label><div><strong>${(c.current_kw??0).toFixed ? c.current_kw.toFixed(2) : c.current_kw}</strong> kW</div></div>
        `;
        box.appendChild(el);
      });
    }
    async function refreshLive(){
      try {
        const r = await fetch('/live');
        if(!r.ok) return;
        const j = await r.json();
        const enabled = !!(j.config && j.config.enabled);
        const connected = !!(j.status && j.status.ok);
        document.getElementById('led-enabled').className = 'led ' + (enabled? 'ok':'bad');
        document.getElementById('led-mqtt').className = 'led ' + (connected? 'ok':'bad');
        document.getElementById('live-power').textContent = j.metering && j.metering.power_kw != null ? j.metering.power_kw.toFixed(2) : '--';
        document.getElementById('live-voltage').textContent = j.metering && j.metering.voltage_v != null ? j.metering.voltage_v.toFixed(1) : '--';
        document.getElementById('live-current').textContent = j.metering && j.metering.current_a != null ? j.metering.current_a.toFixed(2) : '--';
        document.getElementById('live-target').textContent = (j.config && j.config.target_power_kw != null) ? j.config.target_power_kw : '--';
        document.getElementById('live-interval').textContent = (j.config && j.config.report_interval_seconds) ? j.config.report_interval_seconds : '--';
        const last = (j.events && j.events.event_id) ? `${j.events.event_id}` : '—';
        document.getElementById('live-event').textContent = last;
        document.getElementById('live-last-publish').textContent = j.status && j.status.last_publish_at ? j.status.last_publish_at : '—';
        if(document.getElementById('live-batt-soc')){
          const soc = j.metering && j.metering.battery_soc != null ? (j.metering.battery_soc*100).toFixed(0) : '--';
          document.getElementById('live-batt-soc').textContent = soc + '%';
        }
        window.__sheddingIds = j.sheddingLoadIds || [];
        // Prefer circuits from /live.metering, but fall back to /circuits so
        // the panel always renders even before the first publish.
        const liveCircuits = (j.metering && j.metering.circuits) || [];
        if(Array.isArray(liveCircuits) && liveCircuits.length > 0){
          window.__lastCircuits = liveCircuits;
          renderCircuits(liveCircuits);
        } else {
          try {
            const rc = await fetch('/circuits');
            if (rc.ok) {
              const list = await rc.json();
              window.__lastCircuits = list;
              renderCircuits(list);
            } else {
              renderCircuits([]);
            }
          } catch(e){ renderCircuits([]); }
        }
        // Update overall draw gauge
        try{
          const list = window.__lastCircuits || [];
          const cap = list.filter(x=>x.connected!==false).reduce((s,c)=> s + (Number(c.rated_kw||0) || 0), 0) || 1;
          const p = (j.metering && j.metering.power_kw!=null) ? Number(j.metering.power_kw) : 0;
          const pct = Math.min(100, Math.max(0, (p/cap)*100));
          const bar = document.getElementById('gauge-bar'); if(bar) bar.style.width = pct.toFixed(0)+'%';
        }catch(e){}
        // Update event banners
        const eb = document.getElementById('eventbar');
        if(eb){
          const ae = j.activeEvent;
          if(ae && ae.eventId){
            const mins = Math.floor((ae.remainingS||0)/60), secs = (ae.remainingS||0)%60;
            const req = ae.requestedReductionKw != null ? ae.requestedReductionKw : '--';
            const shed = j.metering && j.metering.shedPowerKw != null ? j.metering.shedPowerKw.toFixed(2) : '--';
            eb.innerHTML = `<span class="pill">Event ${ae.eventId}</span>
                            <span>Time left: <strong>${mins}:${secs.toString().padStart(2,'0')}</strong></span>
                            <span>Requested: <strong>${req} kW</strong></span>
                            <span>Current shed: <strong>${shed} kW</strong></span>`;
          } else {
            eb.innerHTML = '<span class="muted">No active event</span>';
          }
        }
        const ed = document.getElementById('eventdone');
        if(ed){
          const s = j.lastEventSummary;
          if(s && s.eventId){
            ed.innerHTML = `<span class="pill">Event ${s.eventId} complete</span>
                            <span>Actual reduction: <strong>${s.actualReductionKw ?? '--'} kW</strong></span>
                            <span>Delivered: <strong>${s.deliveredKwh ?? '--'} kWh</strong></span>`;
          } else {
            ed.innerHTML = '<span class="muted">No recent event summary</span>';
          }
        }
      } catch(e){ /* ignore */ }
    }
    async function showBuild(){
      try{
        const r = await fetch('/openapi.json');
        const j = await r.json();
        const v = (j && j.info && (j.info["x-build"] || j.info.version)) || '';
        const el = document.getElementById('build-id'); if(el) el.textContent = v;
      }catch(e){ const el = document.getElementById('build-id'); if(el) el.textContent = 'n/a'; }
    }
    window.addEventListener('DOMContentLoaded', ()=>{
      showBuild();
      loadCurrent();
      // Eagerly render circuits once from /circuits so the panel shows loads
      // immediately, then let /live keep it fresh.
      fetch('/circuits').then(r=>r.ok?r.json():[]).then(list=>{ try{ renderCircuits(list||[]); }catch(e){} });
      refreshLive();
      setInterval(refreshLive, 2000);
    });
  </script>
  </head>
  <body>
    <header>
      <strong>VOLTTRON VEN Control</strong>
      <a href="/docs">API Docs</a>
      <a href="/config">Current Config</a>
      <span class="build">Build: <span id="build-id">(loading)</span></span>
    </header>
    <main>
      <div class="grid">
        <section class="card panelbox">
          <h2 style="color:#ddd; margin-bottom:12px;">Virtual Panel</h2>
          <div class="meter">
            <div>
              <div class="muted">Total Power</div>
              <div class="big"><span id="live-power">--</span> kW</div>
            </div>
            <div class="kv">
              <div><span class="muted">Voltage</span><br/><strong><span id="live-voltage">--</span> V</strong></div>
              <div><span class="muted">Current</span><br/><strong><span id="live-current">--</span> A</strong></div>
              <div><span class="muted">Target</span><br/><strong><span id="live-target">--</span> kW</strong></div>
              <div><span class="muted">Interval</span><br/><strong><span id="live-interval">--</span> s</strong></div>
              <div><span class="muted">Battery SOC</span><br/><strong><span id="live-batt-soc">--</span></strong></div>
            </div>
          </div>
          <div class="gauge"><div id="gauge-bar" class="bar"></div></div>
          <div style="margin-top:10px; color:#ccc; display:flex; align-items:center; gap:16px;">
            <div><span id="led-enabled" class="led bad"></span> Enabled</div>
            <div><span id="led-mqtt" class="led bad"></span> MQTT</div>
            <div>Last event: <strong id="live-event">—</strong></div>
            <div>Last publish: <span id="live-last-publish">—</span></div>
            <div class="actions"><button onclick="startVen()">Start</button><button class="secondary" onclick="stopVen()">Stop</button></div>
          </div>
        </section>

        <section class="card">
          <h2>Circuits</h2>
          <div id="circuits" class="grid"></div>
        </section>

        <section class="card">
          <h2>Event</h2>
          <div id="eventbar" class="eventbar"><span class="muted">No active event</span></div>
        </section>
        <section class="card">
          <h2>General</h2>
          <div class="field"><label>Preset</label>
            <div>
              <select id="preset">
                <option value="normal">Normal</option>
                <option value="dr_aggressive">DR Aggressive</option>
                <option value="pv_self_use">PV Self-Use</option>
              </select>
              <button onclick="applyPreset()">Apply Preset</button>
            </div>
          </div>
          <div class="field"><label>Enabled</label><input id="enabled" type="checkbox"/></div>
          <div class="field"><label>Report interval (s)</label><input id="interval" type="number" min="1" step="1" /></div>
          <div class="field"><label>Target power (kW)</label><input id="target" type="number" step="0.01" /></div>
        </section>

        <section class="card">
          <h2>Power Generation</h2>
          <div class="field"><label>Base min (kW)</label><input id="base_min" type="number" step="0.01" min="0" /></div>
          <div class="field"><label>Base max (kW)</label><input id="base_max" type="number" step="0.01" min="0" /></div>
          <div class="field"><label>Jitter (%) [0..1]</label><input id="jitter" type="number" step="0.005" min="0" max="1" /></div>
        </section>

        <section class="card">
          <h2>Voltage (optional)</h2>
          <div class="field"><label>Include voltage</label><input id="v_enabled" type="checkbox"/></div>
          <div class="field"><label>Nominal (V)</label><input id="v_nom" type="number" step="0.1" min="1" /></div>
          <div class="field"><label>Jitter (%) [0..1]</label><input id="v_jitter" type="number" step="0.005" min="0" max="1" /></div>
        </section>

        <section class="card">
          <h2>Current (optional)</h2>
          <div class="field"><label>Include current</label><input id="i_enabled" type="checkbox"/></div>
          <div class="field"><label>Power factor</label><input id="pf" type="number" step="0.01" min="0.05" max="1" /></div>
        </section>
      </div>
      <div class="actions">
        <button onclick="applyChanges()">Apply</button>
        <button class="secondary" onclick="loadCurrent()">Reload</button>
      </div>
      <div id="status" class="status"></div>
    </main>
  </body>
  </html>
"""

# ── Static assets loader ------------------------------------------------------
def _load_static_html(filename: str, default_html: str) -> str:
    """Load an HTML asset from a static directory if present.

    Search order:
      1) Directory pointed by env VEN_STATIC_DIR
      2) ./static relative to this file
    Falls back to the provided default_html if no file is found.
    """
    try:
        base = os.getenv("VEN_STATIC_DIR")
        paths: list[pathlib.Path] = []
        if base:
            paths.append(pathlib.Path(base) / filename)
        paths.append(pathlib.Path(__file__).resolve().parent / "static" / filename)
        for p in paths:
            if p.exists() and p.is_file():
                try:
                    return p.read_text(encoding="utf-8")
                except Exception:
                    continue
    except Exception:
        pass
    return default_html

# ── helpers ────────────────────────────────────────────────────────────
def fetch_tls_creds_from_secrets(secret_name: str, region_name="us-west-2") -> dict | None:
    """Fetch TLS PEM contents from AWS Secrets Manager and write them to temp files.
    Returns a dict of file paths for ca_cert, client_cert, and private_key.
    """
    """Fetch TLS PEM contents from AWS Secrets Manager and write them to temp files."""
    try:
        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        cert_files = {}
        tmp_dir = pathlib.Path(tempfile.gettempdir())

        for key, filename in {
            "ca_cert": "ca_cert.pem",
            "client_cert": "client_cert.pem",
            "private_key": "private_key.pem"
        }.items():
            if key in secret:
                path = tmp_dir / filename
                path.write_text(secret[key])
                cert_files[key] = str(path)
        print("✅ Fetched TLS secrets from AWS Secrets Manager")
        return cert_files
    except ClientError as e:
        print(f"❌ Error fetching TLS secrets: {e}", file=sys.stderr)
        return None

def _materialise_pem(*var_names: str) -> str | None:
    """Materialize PEM string from env var to a temp file, return its path."""
    """Return a file-path ready for paho.tls_set()."""
    for var_name in var_names:
        val = os.getenv(var_name)
        if not val:
            continue
        if val.startswith("-----BEGIN"):
            pem_path = pathlib.Path(tempfile.gettempdir()) / f"{var_name.lower()}.pem"
            pem_path.write_text(val)
            os.environ[var_name] = str(pem_path)
            return str(pem_path)
        return val
    return None


def _format_timestamp(timestamp: float | None) -> str | None:
    """Format a UNIX timestamp as ISO8601 string in UTC."""
    if timestamp is None:
        return None

    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _dnsname_matches(pattern: str, hostname: str) -> bool:
    """Check if a DNS pattern matches a hostname (supports wildcard)."""
    pattern = pattern.lower()
    hostname = hostname.lower()

    if pattern.startswith("*."):
        suffix = pattern[1:]
        if not suffix or not hostname.endswith(suffix):
            return False
        prefix = hostname[: -len(suffix)]
        return bool(prefix) and "." not in prefix

    return pattern == hostname


def _ensure_expected_server_hostname(mqtt_client: mqtt.Client, expected: str) -> None:
    """Verify MQTT TLS peer certificate matches expected hostname."""
    """Perform hostname verification manually when connect and TLS hosts differ."""
    hostname = expected.strip()
    if not hostname:
        raise ssl.SSLError("Expected TLS server hostname not provided")

    sock = mqtt_client.socket()
    if sock is None:
        raise ssl.SSLError("TLS socket not available for hostname verification")

    cert = sock.getpeercert()
    if not cert:
        raise ssl.SSLError("TLS peer certificate missing")

    dns_names = [value for key, value in cert.get("subjectAltName", ()) if key == "DNS"]
    if not dns_names:
        for subject in cert.get("subject", ()):  # fall back to CN when SAN absent
            for key, value in subject:
                if key.lower() == "commonname":
                    dns_names.append(value)

    if not dns_names:
        raise ssl.CertificateError("TLS certificate does not present any DNS names")

    for pattern in dns_names:
        if _dnsname_matches(pattern, hostname):
            return

    raise ssl.CertificateError(
        f"Hostname '{hostname}' does not match certificate names: {dns_names}"
    )

# ── env / config ───────────────────────────────────────────────────────
MQTT_TOPIC_STATUS     = os.getenv("MQTT_TOPIC_STATUS", "volttron/dev")
MQTT_TOPIC_EVENTS     = os.getenv("MQTT_TOPIC_EVENTS", "openadr/event")
MQTT_TOPIC_RESPONSES  = os.getenv("MQTT_TOPIC_RESPONSES", "openadr/response")
MQTT_TOPIC_METERING   = os.getenv("MQTT_TOPIC_METERING", "volttron/metering")
DEFAULT_IOT_ENDPOINT  = "a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com"
IOT_ENDPOINT          = os.getenv("IOT_ENDPOINT", DEFAULT_IOT_ENDPOINT)
MQTT_CONNECT_HOST     = os.getenv("IOT_CONNECT_HOST") or os.getenv("MQTT_CONNECT_HOST") or IOT_ENDPOINT
TLS_SERVER_HOSTNAME   = os.getenv("IOT_TLS_SERVER_NAME") or os.getenv("MQTT_TLS_SERVER_NAME") or IOT_ENDPOINT
try:
    MQTT_MAX_CONNECT_ATTEMPTS = int(os.getenv("MQTT_MAX_CONNECT_ATTEMPTS", "5"))
except ValueError:
    MQTT_MAX_CONNECT_ATTEMPTS = 5
MQTT_MAX_CONNECT_ATTEMPTS = max(1, MQTT_MAX_CONNECT_ATTEMPTS)
HEALTH_PORT           = int(os.getenv("HEALTH_PORT", "8000"))
TLS_SECRET_NAME       = os.getenv("TLS_SECRET_NAME","dev-volttron-tls")
AWS_REGION            = os.getenv("AWS_REGION", "us-west-2")
MQTT_PORT             = int(os.getenv("MQTT_PORT", "8883"))
IOT_THING_NAME        = os.getenv("IOT_THING_NAME") or os.getenv("AWS_IOT_THING_NAME")
try:
    REPORT_INTERVAL_SECONDS = int(os.getenv("VEN_REPORT_INTERVAL_SECONDS", "60"))
except ValueError:
    REPORT_INTERVAL_SECONDS = 60
REPORT_INTERVAL_SECONDS = max(1, REPORT_INTERVAL_SECONDS)

# Compute client identity early so it is available for VEN_ID
CLIENT_ID             = (
    os.getenv("IOT_CLIENT_ID")
    or os.getenv("CLIENT_ID")
    or os.getenv("AWS_IOT_THING_NAME")
    or os.getenv("THING_NAME")
    or "volttron_thing"
)

SCHEMA_VERSION = "1.0"
VEN_ID = IOT_THING_NAME or CLIENT_ID

if IOT_THING_NAME:
    SHADOW_TOPIC_UPDATE = f"$aws/things/{IOT_THING_NAME}/shadow/update"
    SHADOW_TOPIC_DELTA = f"{SHADOW_TOPIC_UPDATE}/delta"
    SHADOW_TOPIC_GET = f"$aws/things/{IOT_THING_NAME}/shadow/get"
    SHADOW_TOPIC_GET_ACCEPTED = f"{SHADOW_TOPIC_GET}/accepted"
    SHADOW_TOPIC_GET_REJECTED = f"{SHADOW_TOPIC_GET}/rejected"
    # Backend control plane topics (custom messaging via IoT Core)
    BACKEND_CMD_TOPIC = os.getenv("BACKEND_CMD_TOPIC", f"ven/cmd/{IOT_THING_NAME}")
    BACKEND_ACK_TOPIC = os.getenv("BACKEND_ACK_TOPIC", f"ven/ack/{IOT_THING_NAME}")
else:
    SHADOW_TOPIC_UPDATE = None
    SHADOW_TOPIC_DELTA = None
    SHADOW_TOPIC_GET = None
    SHADOW_TOPIC_GET_ACCEPTED = None
    SHADOW_TOPIC_GET_REJECTED = None
    BACKEND_CMD_TOPIC = os.getenv("BACKEND_CMD_TOPIC")
    BACKEND_ACK_TOPIC = os.getenv("BACKEND_ACK_TOPIC")

# ── TLS setup ──────────────────────────────────────────────────────────
CA_CERT = CLIENT_CERT = PRIVATE_KEY = None

if TLS_SECRET_NAME:
    creds = fetch_tls_creds_from_secrets(TLS_SECRET_NAME, AWS_REGION)
    if creds:
        CA_CERT     = creds.get("ca_cert")
        CLIENT_CERT = creds.get("client_cert")
        PRIVATE_KEY = creds.get("private_key")

if not all([CA_CERT, CLIENT_CERT, PRIVATE_KEY]):
    CA_CERT     = _materialise_pem("CA_CERT", "CA_CERT_PEM")
    CLIENT_CERT = _materialise_pem("CLIENT_CERT", "CLIENT_CERT_PEM")
    PRIVATE_KEY = _materialise_pem("PRIVATE_KEY", "PRIVATE_KEY_PEM")

if not all([CA_CERT, CLIENT_CERT, PRIVATE_KEY]):
    print(
        "❌ TLS credentials are required for AWS IoT Core but were not provided",
        file=sys.stderr,
    )
    sys.exit(1)

def _build_tls_context(
    """Create an SSLContext for MQTT with SNI and hostname verification."""
    ca_path: str, cert_path: str, key_path: str, expected_sni: str | None, connect_host: str
) -> ssl.SSLContext:
    """Create an SSLContext that always sends SNI=expected_sni when set.

    - Verifies the server certificate chain against the provided CA.
    - Keeps hostname verification enabled; when an SNI override is provided
      it causes Python to validate the certificate against that SNI value.
    - Ensures AWS IoT PrivateLink works by sending SNI for the public ATS host
      even when connecting to a VPCE DNS name.
    """
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)

    # Enforce TLS 1.2+
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # type: ignore[attr-defined]
    except Exception:
        pass

    manual_override = bool(expected_sni) and expected_sni != connect_host
    if manual_override and hasattr(ctx, "wrap_socket"):
        # Monkey‑patch wrap_socket to force server_hostname to expected_sni
        orig_wrap = ctx.wrap_socket  # bound method

        def _wrap_socket_with_sni(sock, *args, **kwargs):  # type: ignore[override]
            kwargs["server_hostname"] = expected_sni
            return orig_wrap(sock, *args, **kwargs)

        ctx.wrap_socket = _wrap_socket_with_sni  # type: ignore[assignment]

    # Leave check_hostname=True so Python validates against server_hostname (SNI)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx

# ── MQTT setup ─────────────────────────────────────────────────────────
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)

manual_hostname_override = TLS_SERVER_HOSTNAME != MQTT_CONNECT_HOST
if manual_hostname_override:
    print(
        "🔐 TLS SNI override enabled: "
        f"connecting to {MQTT_CONNECT_HOST} but sending SNI/cert validation for {TLS_SERVER_HOSTNAME}"
    )
elif ".vpce." in MQTT_CONNECT_HOST:
    print(
        "⚠️ Connecting to an AWS IoT VPC endpoint without a TLS SNI override. "
        "Set IOT_TLS_SERVER_NAME to your IoT data endpoint to enable certificate checks.",
        file=sys.stderr,
    )

_tls_ctx = None
try:
    _tls_ctx = _build_tls_context(CA_CERT, CLIENT_CERT, PRIVATE_KEY, TLS_SERVER_HOSTNAME, MQTT_CONNECT_HOST)
    client.tls_set_context(_tls_ctx)
except Exception as tls_err:
    print(f"⚠️ Falling back to insecure TLS due to context error: {tls_err}", file=sys.stderr)
    if hasattr(client, "tls_insecure_set"):
        try:
            client.tls_insecure_set(True)
        except Exception:
            pass
# When overriding SNI/hostname, disable Paho's built-in hostname verification and
# perform our own check post-connect. This aligns with existing tests and allows
# connecting to IoT PrivateLink endpoints while validating against the public ATS name.
if manual_hostname_override and hasattr(client, "tls_insecure_set"):
    try:
        client.tls_insecure_set(True)
    except Exception:
        pass
client.reconnect_delay_set(min_delay=1, max_delay=60)
# Keep publish queue bounded to avoid unbounded memory use if the broker is unreachable.
try:
    client.max_inflight_messages_set(20)
    client.max_queued_messages_set(200)
except Exception:
    pass
try:
    client.enable_logger()
except Exception:
    pass

# Last Will: mark the VEN as offline if the client disconnects unexpectedly.
try:
    client.will_set(
        MQTT_TOPIC_STATUS,
        json.dumps({"ven": "offline", "venId": VEN_ID, "ts": int(time.time())}),
        qos=1,
        retain=False,
    )
except Exception:
    pass

connected = False
_last_connect_time: float | None = None
_last_disconnect_time: float | None = None
_last_publish_time: float | None = None
_reconnect_lock = threading.Lock()
_reconnect_in_progress = False
# Use an RLock to avoid deadlocks when helper functions that also acquire the
# same lock are called from within a locked section (e.g., /live assembling a
# snapshot while holding the state lock).
_shadow_state_lock = threading.RLock()
_shadow_reported_state: dict[str, Any] = {
    "status": {"ven": "starting", "mqtt_connected": False},
    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
    "shadow_errors": {}
}
_shadow_target_power_kw: float | None = None
_ven_enabled: bool = True
_last_enable_change: dict[str, Any] | None = None  # {ts, to, source}
ENABLE_DEBOUNCE_SECONDS = 5

# Update context (tracks source of config/shadow changes for logging)
_UPDATE_SOURCE: str | None = None

def _with_update_source(source: str):
    class _Ctx:
        def __enter__(self_inner):
            global _UPDATE_SOURCE
            self_inner.prev = _UPDATE_SOURCE
            _UPDATE_SOURCE = source
        def __exit__(self_inner, exc_type, exc, tb):
            global _UPDATE_SOURCE
            _UPDATE_SOURCE = self_inner.prev
    return _Ctx()

# ── Metering configuration knobs (tunable at runtime) -----------------------
_meter_base_min_kw: float = 0.5
_meter_base_max_kw: float = 2.0
_meter_jitter_pct: float = 0.05  # ±5% around target when set

_voltage_enabled: bool = False
_voltage_nominal: float = 120.0
_voltage_jitter_pct: float = 0.02  # ±2%

_current_enabled: bool = False
_power_factor: float = 1.0  # 0 < pf <= 1

# latest metering snapshot for UI/live endpoint
_last_metering_sample: dict[str, Any] | None = None

# ── Simple circuit model (placeholder) --------------------------------------
# Default circuits with types. These are displayed on the UI and can be
# toggled on/off. For now, metered total power is split among enabled circuits
# in proportion to their rated_kw to provide a plausible per-circuit breakdown.
_circuits: list[dict[str, Any]] = [
    {"id": "hvac1",    "name": "HVAC",       "type": "hvac",    "enabled": True,  "connected": True, "rated_kw": 3.5, "current_kw": 0.0, "critical": True,  "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "heater1",  "name": "Heater",     "type": "heater",  "enabled": True,  "connected": True, "rated_kw": 1.5, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "ev1",      "name": "EV Charger", "type": "ev",      "enabled": False, "connected": True, "rated_kw": 7.2, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "batt1",    "name": "Battery",    "type": "battery", "enabled": False, "connected": True, "rated_kw": 5.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "pv1",      "name": "Solar PV",   "type": "pv",      "enabled": False, "connected": True, "rated_kw": 6.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "lights1",  "name": "Lights",     "type": "lights",  "enabled": True,  "connected": True, "rated_kw": 0.4, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "fridge1",  "name": "Fridge",     "type": "fridge",  "enabled": True,  "connected": True, "rated_kw": 0.2, "current_kw": 0.0, "critical": True,  "mode": "dynamic", "fixed_kw": 0.0},
    {"id": "misc1",    "name": "House",      "type": "misc",    "enabled": True,  "connected": True, "rated_kw": 1.0, "current_kw": 0.0, "critical": False, "mode": "dynamic", "fixed_kw": 0.0},
]

# Per-load priority (lower number = more critical, shed later). Defaults:
_circuit_priority: dict[str, int] = {"hvac": 1, "misc": 1, "heater": 2, "ev": 3, "battery": 2, "pv": 0}

# Optional per-load limit (kW) until timestamp for shed commands
_load_limits: dict[str, dict[str, float]] = {}  # {id: {"limit_kw": float, "until": ts}}

# Optional panel temp target during shedPanel (kW) with expiry
_panel_temp_target_kw: float | None = None
_panel_temp_until_ts: int | None = None

_circuit_model_enabled: bool = True
_battery_capacity_kwh: float = 13.5
_battery_soc: float = 0.5  # 0..1

# Event tracking and baseline history
_power_history: Deque[tuple[int, float]] = deque(maxlen=360)
_active_event: dict[str, Any] | None = None  # {event_id,start_ts,end_ts,requested_kw,baseline_kw,delivered_kwh,summary_done}

# Optional richer loads publish channel for backend (less frequent than metering)
BACKEND_LOADS_TOPIC = os.getenv("BACKEND_LOADS_TOPIC") or (f"ven/loads/{IOT_THING_NAME}" if IOT_THING_NAME else None)
try:
    LOADS_PUBLISH_EVERY = int(os.getenv("LOADS_PUBLISH_EVERY", "6"))
except ValueError:
    LOADS_PUBLISH_EVERY = 6
_loads_pub_counter = 0


def _circuits_snapshot() -> list[dict[str, Any]]:
    """Return a snapshot of all circuits with current state and shed capability."""
    with _shadow_state_lock:
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "type": c.get("type"),
                "enabled": bool(c.get("enabled", True)),
                "rated_kw": float(c.get("rated_kw", 0.0)),
                "capacityKw": float(c.get("rated_kw", 0.0)),
                "current_kw": float(c.get("current_kw", 0.0)),
                "currentPowerKw": float(c.get("current_kw", 0.0)),
                "shedCapabilityKw": _shed_capability_for(c),
                "priority": int(c.get("priority", _circuit_priority.get(c.get("type", "misc"), 5))),
                "critical": bool(c.get("critical", False)),
                "connected": bool(c.get("connected", True)),
                "mode": c.get("mode", "dynamic"),
                "fixedKw": float(c.get("fixed_kw", 0.0)),
            }
            for c in _circuits
        ]

def _shed_capability_for(c: dict[str, Any]) -> float:
    """Estimate shed capability for a circuit based on type and state."""
    try:
        typ = c.get("type")
        kw = float(c.get("current_kw", 0.0))
        rated = float(c.get("rated_kw", 0.0))
        crit = bool(c.get("critical", False))
        if not c.get("enabled", True):
            return 0.0
        # Critical loads have a higher non-shed floor
        crit_floor_factor = 0.8 if crit else None
        if typ == "hvac":
            floor = (crit_floor_factor or 0.2) * rated
            return round(max(0.0, kw - floor), 2)
        if typ == "heater":
            return round(kw, 2)
        if typ == "ev":
            return round(kw, 2)
        if typ == "misc":
            floor = (crit_floor_factor or 0.3) * rated
            return round(max(0.0, kw - floor), 2)
        if typ == "pv":
            return 0.0
        if typ == "battery":
            return round(rated, 2)
        if typ in ("lights", "fridge"):
            floor = (crit_floor_factor or 0.5) * rated
            return round(max(0.0, kw - floor), 2)
    except Exception:
        return 0.0
    return 0.0

def _distribute_power_to_circuits(total_kw: float) -> list[dict[str, Any]]:
    """Distribute total power among enabled circuits by rated_kw proportion."""
    """Proportionally split total_kw across enabled circuits by rated_kw.

    Updates _circuits current_kw and returns a snapshot for reporting.
    """
    with _shadow_state_lock:
        enabled = [c for c in _circuits if c.get("enabled", True) and c.get("rated_kw", 0.0) > 0]
        if not enabled or total_kw <= 0:
            for c in _circuits:
                c["current_kw"] = 0.0
            return _circuits_snapshot()

        weight_sum = sum(float(c.get("rated_kw", 0.0)) for c in enabled)
        for c in enabled:
            share = float(c.get("rated_kw", 0.0)) / weight_sum if weight_sum > 0 else 0.0
            c["current_kw"] = round(max(0.0, total_kw * share), 2)
        for c in _circuits:
            if c not in enabled:
                c["current_kw"] = 0.0
        return _circuits_snapshot()


def _pv_curve_factor(ts_utc: int) -> float:
    """Simulate a diurnal PV output curve (bell-shaped, peaks at midday)."""
    """Simple diurnal PV factor based on UTC time; peaks at 12:00 local-ish.
    This is a placeholder bell-shaped curve in [0,1]."""
    # Use hour of day in UTC; approximate local midday by shifting -8h (Pacific)
    hour = (ts_utc // 3600) % 24
    local_hour = (hour - 8) % 24
    # Bell curve centered at 12:00 with width ~6 hours
    x = (local_hour - 12) / 6.0
    import math
    val = math.exp(-x * x)
    return float(max(0.0, min(1.0, val)))


def _compute_panel_step(now_ts: int) -> dict[str, Any]:
    """Compute per-circuit kW and aggregate net power for this step.
    Returns dict with power_kw, circuits, battery_soc.
    """
    """Compute per-circuit kW and aggregate net power for this step.

    Returns a dict with keys: power_kw, circuits, battery_soc.
    """
    global _battery_soc
    if not _circuit_model_enabled:
        # Fallback: keep previous behavior
        total = _next_power_reading()
        circuits = _distribute_power_to_circuits(total)
        return {"power_kw": total, "circuits": circuits, "battery_soc": _battery_soc}

    # Gather references
    with _shadow_state_lock:
        target = _shadow_target_power_kw
        batt = next((c for c in _circuits if c["type"] == "battery"), None)
        pv = next((c for c in _circuits if c["type"] == "pv"), None)
        ev = next((c for c in _circuits if c["type"] == "ev"), None)
        hvac = next((c for c in _circuits if c["type"] == "hvac"), None)
        heater = next((c for c in _circuits if c["type"] == "heater"), None)
        house = next((c for c in _circuits if c["type"] == "misc"), None)
        lights = next((c for c in _circuits if c["type"] == "lights"), None)
        fridge = next((c for c in _circuits if c["type"] == "fridge"), None)

    # Base: zero out current_kw
    for c in _circuits:
        c["current_kw"] = 0.0

    # Determine active per-load limit
    def effective_limit(load_id: str, default: float) -> float:
        entry = _load_limits.get(load_id)
        if not entry:
            return default
        if now_ts >= int(entry.get("until", 0)):
            # expired
            _load_limits.pop(load_id, None)
            return default
        return min(default, float(entry.get("limit_kw", default)))

    # Helper for fixed/dynamic per-load
    import random as _r
    def _apply_mode(c: dict[str, Any], dyn_kw: float) -> float:
        if not c or not c.get("connected", True) or not c.get("enabled", True):
            return 0.0
        mode = str(c.get("mode") or "dynamic").lower()
        if mode == "fixed":
            try:
                return max(0.0, min(float(c.get("rated_kw", 0.0)), float(c.get("fixed_kw", 0.0))))
            except Exception:
                return 0.0
        return max(0.0, dyn_kw)

    # House load (misc): between base min/max with jitter
    base_low, base_high = _meter_base_min_kw, max(_meter_base_min_kw, _meter_base_max_kw)
    house_kw = 0.0
    if house and house.get("connected", True):
        dyn = round(_r.uniform(base_low, base_high), 2)
        house_kw = _apply_mode(house, dyn)
        house_kw = min(house_kw, effective_limit(house["id"], house_kw))
        house["current_kw"] = house_kw

    # HVAC: duty between 0.2..0.8 of rated
    hvac_kw = 0.0
    if hvac and hvac.get("connected", True):
        duty = max(0.0, min(1.0, 0.5 + _r.uniform(-0.3, 0.3)))
        hvac_kw = _apply_mode(hvac, round(hvac.get("rated_kw", 0.0) * duty, 2))
        hvac_kw = min(hvac_kw, effective_limit(hvac["id"], hvac_kw))
        hvac["current_kw"] = hvac_kw

    # Heater: bursty low duty 0..0.5
    heater_kw = 0.0
    if heater and heater.get("connected", True):
        duty = max(0.0, min(0.5, _r.uniform(0.0, 0.5)))
        heater_kw = _apply_mode(heater, round(heater.get("rated_kw", 0.0) * duty, 2))
        heater_kw = min(heater_kw, effective_limit(heater["id"], heater_kw))
        heater["current_kw"] = heater_kw

    # EV: simple on/off at rated when enabled
    ev_kw = 0.0
    if ev and ev.get("connected", True):
        ev_kw = _apply_mode(ev, round(ev.get("rated_kw", 0.0), 2))
        ev_kw = min(ev_kw, effective_limit(ev["id"], ev_kw))
        ev["current_kw"] = ev_kw

    # Lights: modest variable draw up to rated
    if lights and lights.get("connected", True):
        lk = _apply_mode(lights, round(max(0.0, min(lights.get("rated_kw", 0.0), _r.uniform(0.05, lights.get("rated_kw", 0.0)))), 2))
        lk = min(lk, effective_limit(lights["id"], lk))
        lights["current_kw"] = lk
    else:
        lk = 0.0

    # Fridge: quasi-constant duty with small jitter
    if fridge and fridge.get("connected", True):
        fk = _apply_mode(fridge, round(max(0.0, min(fridge.get("rated_kw", 0.0), 0.5 * fridge.get("rated_kw", 0.0) + _r.uniform(-0.02, 0.02))), 2))
        fk = min(fk, effective_limit(fridge["id"], fk))
        fridge["current_kw"] = fk
    else:
        fk = 0.0

    # PV generation: rated * curve factor
    pv_gen = 0.0
    if pv and pv.get("connected", True) and pv.get("enabled", False):
        pv_gen = round(pv.get("rated_kw", 0.0) * _pv_curve_factor(now_ts), 2)
        pv["current_kw"] = -pv_gen  # represent as negative load (generation)

    # Pre-battery net load
    load_kw = house_kw + hvac_kw + heater_kw + ev_kw + lk + fk
    net_kw_before_batt = max(0.0, load_kw - pv_gen)

    # Battery action: attempt to move net toward effective target
    batt_flow = 0.0  # positive=discharge (reduce grid draw), negative=charge
    if batt and batt.get("enabled", False):
        batt_max = float(batt.get("rated_kw", 0.0))
        # Temporary target during panel shed may override configured target
        eff_target = target
        if _panel_temp_target_kw is not None and _panel_temp_until_ts and now_ts < _panel_temp_until_ts:
            eff_target = _panel_temp_target_kw
        else:
            # clear expired
            if _panel_temp_until_ts and now_ts >= _panel_temp_until_ts:
                globals()["_panel_temp_target_kw"] = None
                globals()["_panel_temp_until_ts"] = None

        if eff_target is not None:
            # If above target, discharge; if below target, (optionally) charge
            diff = net_kw_before_batt - float(eff_target)
            if diff > 0.05:  # above target: discharge up to diff
                batt_flow = min(batt_max, diff)
            elif diff < -0.5:  # well below target: charge up to -diff/2
                batt_flow = -min(batt_max, (-diff) * 0.5)
        else:
            # Idle or mild smoothing (optional): do nothing
            batt_flow = 0.0

        # Update SOC (simple integrator)
        step_h = max(1.0, REPORT_INTERVAL_SECONDS) / 3600.0
        energy_delta_kwh = batt_flow * step_h
        _battery_soc = max(0.0, min(1.0, _battery_soc + (energy_delta_kwh / max(0.1, _battery_capacity_kwh))))

        # Clamp by available energy
        if batt_flow > 0 and _battery_soc <= 0.01:
            batt_flow = 0.0
        if batt_flow < 0 and _battery_soc >= 0.99:
            batt_flow = 0.0

        batt["current_kw"] = -batt_flow  # negative means discharging reduces grid draw

    # Final net grid power (kW)
    power_kw = round(max(0.0, net_kw_before_batt - max(0.0, batt_flow)), 2)

    return {"power_kw": power_kw, "circuits": _circuits_snapshot(), "battery_soc": _battery_soc}


def _compute_shed_availability() -> float:
    """Estimate instantaneous shed availability across loads and storage."""
    """Estimate instantaneous shed availability across loads and storage."""
    avail = 0.0
    for c in _circuits:
        if not c.get("enabled", True):
            continue
        typ = c.get("type")
        kw = float(c.get("current_kw", 0.0))
        rated = float(c.get("rated_kw", 0.0))
        if typ == "hvac":
            floor = 0.2 * rated
            avail += max(0.0, kw - floor)
        elif typ == "heater":
            avail += kw
        elif typ == "ev":
            avail += kw
        elif typ == "misc":
            floor = 0.3 * rated
            avail += max(0.0, kw - floor)
        elif typ == "pv":
            # cannot shed generation here
            continue
        elif typ == "battery":
            # battery can contribute up to discharge headroom (rated)
            avail += rated
    return round(avail, 2)


def _maybe_finalize_event(now_ts: int) -> dict[str, Any] | None:
    """If an active event has ended, compute and return a summary."""
    """If an active event has ended and no summary yet, compute and return a summary.

    Returns a dict with summary fields or None if not applicable.
    """
    global _active_event
    ev = _active_event
    if not ev:
        return None
    et = int(ev.get("end_ts", 0))
    if now_ts < et:
        return None
    if ev.get("summary_done"):
        return None
    st = int(ev.get("start_ts", et))
    duration_h = max(1e-6, (et - st) / 3600.0)
    delivered_kwh = float(ev.get("delivered_kwh") or 0.0)
    actual_reduction_kw = delivered_kwh / duration_h
    summary = {
        "eventId": ev.get("event_id"),
        "requestedReductionKw": ev.get("requested_kw"),
        "actualReductionKw": round(actual_reduction_kw, 3),
        "deliveredKwh": round(delivered_kwh, 3),
        "baselineKw": ev.get("baseline_kw"),
        "startTs": st,
        "endTs": et,
    }
    ev["summary_done"] = True
    return summary


def _merge_dict(target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge updates into target dict."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_dict(target[key], value)
        else:
            target[key] = value
    return target


def _shadow_merge_report(updates: dict[str, Any]) -> None:
    """Merge updates into reported shadow state and publish to MQTT."""
    if not SHADOW_TOPIC_UPDATE or not updates:
        return

    with _shadow_state_lock:
        _merge_dict(_shadow_reported_state, updates)
        snapshot = deepcopy(_shadow_reported_state)

    payload = json.dumps({"state": {"reported": snapshot}})
    client.publish(SHADOW_TOPIC_UPDATE, payload, qos=1)
    print(f"Published thing shadow update: {payload}")


def _shadow_publish_desired(desired: dict[str, Any]) -> None:
    """Publish desired state to device shadow via MQTT."""
    if not SHADOW_TOPIC_UPDATE or not desired:
        return
    payload = json.dumps({"state": {"desired": desired}})
    client.publish(SHADOW_TOPIC_UPDATE, payload, qos=1)
    print(f"Published desired shadow update: {desired}")


def _manual_hostname_verification(mqtt_client: mqtt.Client) -> None:
    """Perform manual TLS hostname verification if SNI override is used."""
    # With the SNI-forcing TLS context, Python already validated the
    # certificate against TLS_SERVER_HOSTNAME. Keep this as a belt‑and‑braces
    # check, but it should never fail unless the broker rotates certs mid‑session.
    if not manual_hostname_override:
        return
    try:
        _ensure_expected_server_hostname(mqtt_client, TLS_SERVER_HOSTNAME)
    except ssl.CertificateError as err:
        raise ssl.SSLError(str(err)) from err


def _on_connect(_client, _userdata, _flags, rc, *_args):
    """MQTT on_connect callback: handle TLS verification and state update."""
    global connected, _last_connect_time
    if rc == 0:
        try:
            _manual_hostname_verification(_client)
        except ssl.SSLError as err:
            connected = False
            print(f"MQTT connection failed TLS hostname check: {err}", file=sys.stderr)
            _client.disconnect()
            _shadow_merge_report({
                "status": {"mqtt_connected": False},
                "shadow_errors": {"tls_hostname": str(err)}
            })
            return
        connected = True
        _last_connect_time = time.time()
        _shadow_merge_report({"status": {"mqtt_connected": True}})
    else:
        connected = False
        _shadow_merge_report({
            "status": {"mqtt_connected": False, "last_connect_code": rc}
        })

    status = "established" if connected else f"failed (code {rc})"
    print(f"MQTT connection {status} as client_id='{CLIENT_ID}'")


def _on_disconnect(_client, _userdata, rc):
    """MQTT on_disconnect callback: handle reconnect logic."""
    global connected, _reconnect_in_progress, _last_disconnect_time
    connected = False
    _last_disconnect_time = time.time()
    reason = "graceful" if rc == mqtt.MQTT_ERR_SUCCESS else f"unexpected (code {rc})"
    print(f"MQTT disconnected: {reason}", file=sys.stderr)
    _shadow_merge_report({
        "status": {"mqtt_connected": False, "last_disconnect_code": rc}
    })

    if rc == mqtt.MQTT_ERR_SUCCESS or not _ven_enabled:
        return

    def _attempt_reconnect():
        global _reconnect_in_progress
        with _reconnect_lock:
            if _reconnect_in_progress:
                return
            _reconnect_in_progress = True

        try:
            delay = 1
            for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
                try:
                    _client.reconnect()
                    return
                except Exception as err:  # pragma: no cover - informational
                    print(
                        f"MQTT reconnect failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {err}",
                        file=sys.stderr,
                    )
                    time.sleep(min(delay, 30))
                    delay *= 2
            print("❌ Could not reconnect to MQTT broker", file=sys.stderr)
        finally:
            with _reconnect_lock:
                _reconnect_in_progress = False

    threading.Thread(target=_attempt_reconnect, daemon=True).start()


def _subscribe_topics() -> None:
    """Subscribe to required MQTT topics for events and shadow sync."""
    client.message_callback_add(MQTT_TOPIC_EVENTS, on_event)
    client.subscribe(MQTT_TOPIC_EVENTS)

    if SHADOW_TOPIC_DELTA:
        client.message_callback_add(SHADOW_TOPIC_DELTA, on_shadow_delta)
        client.subscribe(SHADOW_TOPIC_DELTA)

        if SHADOW_TOPIC_GET_ACCEPTED:
            client.message_callback_add(SHADOW_TOPIC_GET_ACCEPTED, on_shadow_get_accepted)
            client.subscribe(SHADOW_TOPIC_GET_ACCEPTED)

        if SHADOW_TOPIC_GET_REJECTED:
            client.message_callback_add(SHADOW_TOPIC_GET_REJECTED, on_shadow_get_rejected)
            client.subscribe(SHADOW_TOPIC_GET_REJECTED)

        _shadow_request_sync()
    else:
        if not IOT_THING_NAME:
            print("⚠️ IOT_THING_NAME not set; device shadow sync disabled.")


def _ven_disable() -> None:
    """Disable VEN agent and disconnect MQTT client."""
    global _ven_enabled, connected
    _ven_enabled = False
    try:
        client.loop_stop()
    except Exception:
        pass
    try:
        client.disconnect()
    except Exception:
        pass
    connected = False


def _ven_enable() -> None:
    """Enable VEN agent and connect MQTT client."""
    global _ven_enabled
    if _ven_enabled:
        return
    _ven_enabled = True
    # Try to connect and start loop, then resubscribe
    for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
        try:
            client.connect(MQTT_CONNECT_HOST, MQTT_PORT, 60)
            break
        except Exception as e:
            print(
                f"MQTT connect (re-enable) failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {e}",
                file=sys.stderr,
            )
            time.sleep(min(2 ** attempt, 30))
    client.loop_start()
    _subscribe_topics()


def _shadow_request_sync() -> None:
    """Request device shadow sync from AWS IoT Core."""
    if not SHADOW_TOPIC_GET:
        return
    print(f"Requesting device shadow state for thing '{IOT_THING_NAME}'")
    client.publish(SHADOW_TOPIC_GET, json.dumps({}), qos=0)


def _sync_reported_state(reported: dict[str, Any]) -> None:
    """Apply reported shadow state to local config and runtime knobs."""
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw, _ven_enabled
    global _meter_base_min_kw, _meter_base_max_kw, _meter_jitter_pct
    global _voltage_enabled, _voltage_nominal, _voltage_jitter_pct
    global _current_enabled, _power_factor
    if not isinstance(reported, dict):
        return

    if "report_interval_seconds" in reported:
        try:
            REPORT_INTERVAL_SECONDS = max(1, int(reported["report_interval_seconds"]))
        except (TypeError, ValueError):
            pass

    if "target_power_kw" in reported:
        try:
            _shadow_target_power_kw = float(reported["target_power_kw"])
        except (TypeError, ValueError):
            pass

    if "enabled" in reported:
        try:
            desired_enabled = bool(reported["enabled"])
            if desired_enabled and not _ven_enabled:
                _ven_enable()
            elif not desired_enabled and _ven_enabled:
                _ven_disable()
        except Exception:
            pass

    # Metering knobs
    try:
        if "meter_base_min_kw" in reported:
            _meter_base_min_kw = max(0.0, float(reported["meter_base_min_kw"]))
        if "meter_base_max_kw" in reported:
            _meter_base_max_kw = max(_meter_base_min_kw, float(reported["meter_base_max_kw"]))
        if "meter_jitter_pct" in reported:
            val = float(reported["meter_jitter_pct"])  # e.g., 0.05 = 5%
            _meter_jitter_pct = max(0.0, min(1.0, val))
    except (TypeError, ValueError):
        pass

    try:
        if "voltage_enabled" in reported:
            _voltage_enabled = bool(reported["voltage_enabled"])
        if "voltage_nominal" in reported:
            _voltage_nominal = max(1.0, float(reported["voltage_nominal"]))
        if "voltage_jitter_pct" in reported:
            val = float(reported["voltage_jitter_pct"])  # 0..1
            _voltage_jitter_pct = max(0.0, min(1.0, val))
    except (TypeError, ValueError):
        pass

    try:
        if "current_enabled" in reported:
            _current_enabled = bool(reported["current_enabled"])
        if "power_factor" in reported:
            val = float(reported["power_factor"])  # 0 < pf <= 1
            _power_factor = max(0.05, min(1.0, val))
    except (TypeError, ValueError):
        pass


def _apply_shadow_delta(delta: dict[str, Any]) -> dict[str, Any]:
    """Apply shadow delta to config and runtime state, return applied updates."""
    global REPORT_INTERVAL_SECONDS, _shadow_target_power_kw, _ven_enabled
    global _meter_base_min_kw, _meter_base_max_kw, _meter_jitter_pct
    global _voltage_enabled, _voltage_nominal, _voltage_jitter_pct
    global _current_enabled, _power_factor

    updates: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for key, value in delta.items():
        if key == "report_interval_seconds":
            try:
                interval = max(1, int(value))
                REPORT_INTERVAL_SECONDS = interval
                updates[key] = interval
            except (TypeError, ValueError):
                errors[key] = f"invalid interval: {value}"
                updates[key] = REPORT_INTERVAL_SECONDS
        elif key == "target_power_kw":
            try:
                _shadow_target_power_kw = float(value)
                updates[key] = _shadow_target_power_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid target_power_kw: {value}"
        elif key == "enabled":
            try:
                desired_enabled = bool(value)
                # Debounce rapid flaps
                now_ts = int(time.time())
                if desired_enabled != _ven_enabled:
                    allow = True
                    if _last_enable_change and isinstance(_last_enable_change.get("ts"), (int, float)):
                        if (now_ts - int(_last_enable_change["ts"])) < ENABLE_DEBOUNCE_SECONDS:
                            allow = False
                    if allow:
                        source = _UPDATE_SOURCE or "unknown"
                        print(f"VEN enable -> {desired_enabled} (source={source})")
                        if desired_enabled:
                            _ven_enable()
                        else:
                            _ven_disable()
                        _last_enable_change = {"ts": now_ts, "to": desired_enabled, "source": source}
                    else:
                        print("Debounced rapid enable/disable toggle; ignoring")
                updates[key] = desired_enabled
            except Exception:
                errors[key] = f"invalid enabled: {value}"
        elif key == "meter_base_min_kw":
            try:
                _meter_base_min_kw = max(0.0, float(value))
                if _meter_base_max_kw < _meter_base_min_kw:
                    _meter_base_max_kw = _meter_base_min_kw
                updates[key] = _meter_base_min_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_base_min_kw: {value}"
        elif key == "meter_base_max_kw":
            try:
                _meter_base_max_kw = max(_meter_base_min_kw, float(value))
                updates[key] = _meter_base_max_kw
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_base_max_kw: {value}"
        elif key == "meter_jitter_pct":
            try:
                val = float(value)
                _meter_jitter_pct = max(0.0, min(1.0, val))
                updates[key] = _meter_jitter_pct
            except (TypeError, ValueError):
                errors[key] = f"invalid meter_jitter_pct: {value}"
        elif key == "voltage_enabled":
            try:
                _voltage_enabled = bool(value)
                updates[key] = _voltage_enabled
            except Exception:
                errors[key] = f"invalid voltage_enabled: {value}"
        elif key == "voltage_nominal":
            try:
                _voltage_nominal = max(1.0, float(value))
                updates[key] = _voltage_nominal
            except (TypeError, ValueError):
                errors[key] = f"invalid voltage_nominal: {value}"
        elif key == "voltage_jitter_pct":
            try:
                val = float(value)
                _voltage_jitter_pct = max(0.0, min(1.0, val))
                updates[key] = _voltage_jitter_pct
            except (TypeError, ValueError):
                errors[key] = f"invalid voltage_jitter_pct: {value}"
        elif key == "current_enabled":
            try:
                _current_enabled = bool(value)
                updates[key] = _current_enabled
            except Exception:
                errors[key] = f"invalid current_enabled: {value}"
        elif key == "power_factor":
            try:
                val = float(value)
                _power_factor = max(0.05, min(1.0, val))
                updates[key] = _power_factor
            except (TypeError, ValueError):
                errors[key] = f"invalid power_factor: {value}"
        else:
            updates[key] = value

    if errors:
        updates.setdefault("shadow_errors", {}).update(errors)

    status_updates = updates.setdefault("status", {})
    status_updates["last_shadow_delta_ts"] = int(time.time())
    status_updates["last_shadow_delta"] = deepcopy(delta)
    return updates


def on_shadow_delta(_client, _userdata, msg):
    """MQTT callback for device shadow delta updates."""
    if not SHADOW_TOPIC_DELTA:
        return

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError as err:
        print(f"Invalid thing shadow delta payload: {err}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"delta_decode": str(err)}})
        return

    delta = payload.get("state") or {}
    if not isinstance(delta, dict):
        print(f"Unexpected thing shadow delta structure: {delta}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"delta_type": str(type(delta))}})
        return

    print(f"Received desired shadow state delta: {delta}")
    with _with_update_source("shadow_delta"):
        updates = _apply_shadow_delta(delta)
    if updates:
        _shadow_merge_report(updates)


def on_shadow_get_accepted(_client, _userdata, msg):
    """MQTT callback for device shadow get accepted."""
    if not SHADOW_TOPIC_GET_ACCEPTED:
        return

    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError as err:
        print(f"Invalid thing shadow document: {err}", file=sys.stderr)
        _shadow_merge_report({"shadow_errors": {"shadow_get": str(err)}})
        return

    state = payload.get("state") or {}
    desired = state.get("desired") or {}
    reported = state.get("reported") or {}
    print(f"Thing shadow get accepted: desired={desired}, reported={reported}")

    updates: dict[str, Any] = {"status": {"shadow_version": payload.get("version")}}

    if isinstance(desired, dict) and desired:
        with _with_update_source("shadow_get"):
            desired_updates = _apply_shadow_delta(desired)
        _merge_dict(updates, desired_updates)
    elif isinstance(reported, dict) and reported:
        _sync_reported_state(reported)
        _merge_dict(updates, reported)

    _shadow_merge_report(updates)


def on_shadow_get_rejected(_client, _userdata, msg):
    """MQTT callback for device shadow get rejected."""
    if not SHADOW_TOPIC_GET_REJECTED:
        return

    try:
        error_payload = msg.payload.decode()
    except Exception:
        error_payload = repr(msg.payload)

    print(f"Thing shadow get rejected: {error_payload}", file=sys.stderr)
    _shadow_merge_report({"shadow_errors": {"shadow_get": error_payload}})


def _log_unhandled_message(_client, _userdata, msg):
    """Default MQTT callback for unhandled messages."""
    try:
        payload = msg.payload.decode()
    except Exception:
        payload = repr(msg.payload)
    print(f"Unhandled MQTT message on {msg.topic}: {payload}")


def _publish_ack(op: str, ok: bool, data: dict | None = None, error: str | None = None, correlation_id: str | None = None) -> None:
    """Publish an acknowledgment message to backend ACK topic."""
    if not BACKEND_ACK_TOPIC:
        return
    ack = {
        "op": op,
        "ok": ok,
        "ts": int(time.time()),
        "venId": VEN_ID,
    }
    if correlation_id:
        ack["correlationId"] = correlation_id
    if data is not None:
        ack["data"] = data
    if error is not None:
        ack["error"] = error
    client.publish(BACKEND_ACK_TOPIC, json.dumps(ack), qos=1)


def _apply_config_payload(obj: dict[str, Any]) -> dict[str, Any]:
    """Apply config dict using /config semantics and shadow delta logic."""
    """Apply a config dict using the same semantics as /config and shadow deltas.

    Returns the updates that were applied (for echo/ack) and merges them to the
    reported shadow state.
    """
    desired: dict[str, Any] = {}
    if not isinstance(obj, dict):
        return {}

    # Accept known keys only; pass-through values are validated in _apply_shadow_delta
    for fld in (
        "report_interval_seconds",
        "target_power_kw",
        "enabled",
        "meter_base_min_kw",
        "meter_base_max_kw",
        "meter_jitter_pct",
        "voltage_enabled",
        "voltage_nominal",
        "voltage_jitter_pct",
        "current_enabled",
        "power_factor",
    ):
        if fld in obj:
            desired[fld] = obj[fld]

    with _with_update_source(_UPDATE_SOURCE or "config"):
        updates = _apply_shadow_delta(desired)
    if updates:
        _shadow_merge_report(updates)
        _shadow_publish_desired(desired)
    return updates or {}


def _apply_preset(name: str) -> dict[str, Any]:
    """Apply a named preset to config and circuit toggles."""
    """Apply a named preset: adjust config and circuit toggles.

    Returns a summary of changes.
    """
    name = (name or "").lower()
    changes: dict[str, Any] = {}
    # Default: normal
    if name in ("", "normal"):
        desired = {
            "enabled": True,
            "report_interval_seconds": max(5, REPORT_INTERVAL_SECONDS),
            "meter_jitter_pct": _meter_jitter_pct,
        }
        changes["config"] = _apply_config_payload(desired)
        # circuits
        with _shadow_state_lock:
            for c in _circuits:
                if c["type"] in ("hvac", "heater", "misc", "pv"):
                    c["enabled"] = True
                else:
                    c["enabled"] = False
        changes["circuits"] = _circuits_snapshot()
        return changes

    if name in ("dr", "dr_aggressive"):
        desired = {
            "enabled": True,
            "report_interval_seconds": 10,
            "target_power_kw": 1.0,
            "meter_jitter_pct": 0.02,
        }
        changes["config"] = _apply_config_payload(desired)
        with _shadow_state_lock:
            for c in _circuits:
                if c["type"] in ("ev", "heater"):
                    c["enabled"] = False
                elif c["type"] in ("hvac", "misc"):
                    c["enabled"] = True
                elif c["type"] == "battery":
                    c["enabled"] = True
                elif c["type"] == "pv":
                    c["enabled"] = True
        changes["circuits"] = _circuits_snapshot()
        return changes

    if name in ("pv", "pv_self_use"):
        desired = {
            "enabled": True,
            "report_interval_seconds": 30,
            "meter_jitter_pct": 0.03,
        }
        changes["config"] = _apply_config_payload(desired)
        with _shadow_state_lock:
            for c in _circuits:
                if c["type"] == "pv":
                    c["enabled"] = True
                elif c["type"] == "battery":
                    c["enabled"] = True
                else:
                    c["enabled"] = True if c["type"] in ("misc", "hvac") else False
        changes["circuits"] = _circuits_snapshot()
        return changes

    # Unknown preset: no-op
    return {"error": f"unknown preset: {name}"}


def on_backend_cmd(_client, _userdata, msg):
    """Handle control-plane commands from backend via MQTT."""
    """Handle control-plane commands published by the backend over IoT Core.

    Expected JSON structure (flexible):
      - { "op": "set", "data": { ... same fields as /config ... } }
      - { "op": "enable" } or { "op": "disable" }
      - { "op": "get", "what": "status|config" }
      - { "op": "ping" }
      - { "op": "event", "data": { "event_id": "...", "shed_kw": 1.2, "start_ts": 123, "duration_s": 900 } }
    """
    global _shadow_target_power_kw
    op = "unknown"
    corr = None
    try:
        payload = json.loads(msg.payload.decode())
        op = str(payload.get("op") or "set").lower()
        corr = payload.get("correlationId")
        data = payload.get("data")

        if op in ("set", "setconfig"):
            with _with_update_source("backend_cmd"):
                updates = _apply_config_payload(data if isinstance(data, dict) else payload)
            _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
            return
        if op == "enable":
            with _with_update_source("backend_cmd"):
                updates = _apply_config_payload({"enabled": True})
            _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
            return
        if op == "disable":
            with _with_update_source("backend_cmd"):
                updates = _apply_config_payload({"enabled": False})
            _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
            return
        if op == "get":
            what = str(payload.get("what") or "status").lower()
            if what == "config":
                with _shadow_state_lock:
                    cfg = {
                        "report_interval_seconds": REPORT_INTERVAL_SECONDS,
                        "target_power_kw": _shadow_target_power_kw,
                        "enabled": _ven_enabled,
                        "meter_base_min_kw": _meter_base_min_kw,
                        "meter_base_max_kw": _meter_base_max_kw,
                        "meter_jitter_pct": _meter_jitter_pct,
                        "voltage_enabled": _voltage_enabled,
                        "voltage_nominal": _voltage_nominal,
                        "voltage_jitter_pct": _voltage_jitter_pct,
                        "current_enabled": _current_enabled,
                        "power_factor": _power_factor,
                    }
                _publish_ack(op, True, {"config": cfg}, correlation_id=corr)
            else:
                _code, status = health_snapshot()
                _publish_ack(op, True, {"status": status}, correlation_id=corr)
            return
        if op == "ping":
            _publish_ack(op, True, {"pong": True, "ts": int(time.time())}, correlation_id=corr)
            return
        if op == "shedload":
            # Handle load shedding command
            shed_amount = None
            if isinstance(data, dict):
                shed_amount = data.get("amountKw") or data.get("shed_kw")
            # Simulate load shedding by adjusting target power
            if shed_amount is not None:
                with _shadow_state_lock:
                    _shadow_target_power_kw = max(0.0, float(shed_amount))
                _publish_ack(op, True, {"shedAmount": shed_amount}, correlation_id=corr)
            else:
                _publish_ack(op, False, {"error": "No shed amount provided"}, correlation_id=corr)
            return
        if op == "event":
            ev = data if isinstance(data, dict) else {}
            # Record event in shadow and optionally adjust target
            ev_id = ev.get("event_id") or f"backend_{int(time.time())}"
            shed_kw = ev.get("shed_kw")
            start_ts = int(ev.get("start_ts") or int(time.time()))
            duration_s = int(ev.get("duration_s") or 0)
            end_ts = int(ev.get("end_ts") or (start_ts + duration_s if duration_s > 0 else start_ts))
            req_kw = ev.get("requestedReductionKw") or ev.get("requested_kw")
            updates: dict[str, Any] = {
                "status": {"last_backend_event_ts": int(time.time())},
                "events": {"last_backend": {"event_id": ev_id, **ev}},
            }
            if isinstance(shed_kw, (int, float)):
                # For a simple demo, interpret shed_kw as a target power cap
                updates["target_power_kw"] = max(0.0, float(shed_kw))
                with _shadow_state_lock:
                    try:
                        _shadow_target_power_kw = float(updates["target_power_kw"])
                    except Exception:
                        pass
            # Track active event window
            globals()["_active_event"] = {
                "event_id": ev_id,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "requested_kw": float(req_kw) if isinstance(req_kw, (int, float)) else None,
                "baseline_kw": None,
                "delivered_kwh": 0.0,
            }
            _shadow_merge_report(updates)
            _publish_ack(op, True, {"event_id": ev_id}, correlation_id=corr)
            return
        if op == "setload":
            d = data if isinstance(data, dict) else {}
            load_id = str(d.get("loadId") or "")
            if not load_id:
                _publish_ack(op, False, error="missing loadId", correlation_id=corr)
                return
            updated = None
            with _shadow_state_lock:
                for c in _circuits:
                    if c["id"] == load_id:
                        if "enabled" in d:
                            c["enabled"] = bool(d.get("enabled"))
                        if "capacityKw" in d or "rated_kw" in d:
                            cap = d.get("capacityKw", d.get("rated_kw"))
                            try:
                                c["rated_kw"] = max(0.0, float(cap))
                            except Exception:
                                pass
                        if "priority" in d:
                            try:
                                _circuit_priority[c.get("type", "misc")] = int(d.get("priority"))
                            except Exception:
                                pass
                        updated = {k: c[k] for k in ("id","name","type","enabled","rated_kw")}
                        break
            if updated is None:
                _publish_ack(op, False, error=f"unknown loadId: {load_id}", correlation_id=corr)
                return
            _publish_ack(op, True, {"updated": updated}, correlation_id=corr)
            return
        if op == "shedload":
            d = data if isinstance(data, dict) else {}
            load_id = str(d.get("loadId") or "")
            reduce_kw = float(d.get("reduceKw") or 0.0)
            duration_s = int(d.get("durationS") or 0)
            if not load_id or reduce_kw <= 0 or duration_s <= 0:
                _publish_ack(op, False, error="require loadId, reduceKw>0, durationS>0", correlation_id=corr)
                return
            now = int(time.time())
            with _shadow_state_lock:
                # Determine current expected power and set a limit
                base_limit = None
                for c in _circuits:
                    if c["id"] == load_id and c.get("enabled", True):
                        cur = float(c.get("current_kw", 0.0))
                        base_limit = max(0.0, cur - reduce_kw)
                        _load_limits[load_id] = {"limit_kw": base_limit, "until": now + duration_s}
                        break
            if base_limit is None:
                _publish_ack(op, False, error="load not found or disabled", correlation_id=corr)
                return
            _publish_ack(op, True, {"limitKw": base_limit, "until": now + duration_s}, correlation_id=corr)
            return
        if op == "shedpanel":
            d = data if isinstance(data, dict) else {}
            req = float(d.get("requestedReductionKw") or 0.0)
            duration_s = int(d.get("durationS") or 0)
            if req <= 0 or duration_s <= 0:
                _publish_ack(op, False, error="require requestedReductionKw>0 and durationS>0", correlation_id=corr)
                return
            now = int(time.time())
            # Set temporary panel target based on last metered power
            eff_target = None
            if _last_metering_sample and isinstance(_last_metering_sample.get("power_kw"), (int, float)):
                eff_target = max(0.0, float(_last_metering_sample["power_kw"]) - req)
            else:
                eff_target = max(0.0, req)  # fallback
            globals()["_panel_temp_target_kw"] = eff_target
            globals()["_panel_temp_until_ts"] = now + duration_s
            # Simple allocation: impose per-load limits starting with lowest priority (highest number)
            remaining = req
            with _shadow_state_lock:
                loads_sorted = sorted(
                    [c for c in _circuits if c.get("enabled", True) and c.get("type") not in ("pv",)],
                    key=lambda c: _circuit_priority.get(c.get("type", "misc"), 5),
                    reverse=True,
                )
                for c in loads_sorted:
                    if remaining <= 0:
                        break
                    cur = float(c.get("current_kw", 0.0))
                    shed = min(cur, remaining)
                    new_limit = max(0.0, cur - shed)
                    _load_limits[c["id"]] = {"limit_kw": new_limit, "until": now + duration_s}
                    remaining -= shed
            accepted = req - max(0.0, remaining)
            _publish_ack(op, True, {"targetKw": eff_target, "acceptedReduceKw": round(accepted,2), "until": now + duration_s}, correlation_id=corr)
            return

        _publish_ack(op, False, error=f"unknown op: {op}", correlation_id=corr)
    except Exception as e:
        _publish_ack(op, False, error=str(e), correlation_id=corr)

client.on_connect = _on_connect
client.on_disconnect = _on_disconnect
client.on_message = _log_unhandled_message

for attempt in range(1, MQTT_MAX_CONNECT_ATTEMPTS + 1):
    try:
        client.connect(MQTT_CONNECT_HOST, MQTT_PORT, 60)
        break
    except Exception as e:
        if client.is_connected():
            try:
                client.disconnect()
            except Exception:
                pass
        print(
            f"MQTT connect failed (try {attempt}/{MQTT_MAX_CONNECT_ATTEMPTS}): {e}",
            file=sys.stderr,
        )
        time.sleep(min(2 ** attempt, 30))
else:
    print("❌ Could not connect to MQTT broker", file=sys.stderr)
    sys.exit(1)

# ── graceful shutdown ─────────────────────────────────────────────────
def _shutdown(signo, _frame):
    print("Received SIGTERM, disconnecting cleanly…")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown)
try:
    signal.signal(signal.SIGINT, _shutdown)
except Exception:
    pass

client.loop_start()

# ── simple /health endpoint -------------------------------------------
def health_snapshot() -> tuple[int, dict]:
    """Return a status code and JSON payload describing service health."""
    """Return a status code and JSON payload describing service health."""
    payload = {
        "ok": connected,
        "status": "connected" if connected else "disconnected",
        "detail": (
            "MQTT connection established"
            if connected
            else "MQTT client disconnected; background reconnect active"
        ),
        "reconnect_in_progress": _reconnect_in_progress,
        "manual_tls_hostname_override": manual_hostname_override,
        "mqtt_connect_host": MQTT_CONNECT_HOST,
        "mqtt_port": MQTT_PORT,
        "tls_server_hostname": TLS_SERVER_HOSTNAME,
        "enabled": _ven_enabled,
    }

    if _last_enable_change:
        payload["last_enable_change"] = _last_enable_change

    if _last_connect_time is not None:
        payload["last_connected_at"] = _format_timestamp(_last_connect_time)
    if _last_disconnect_time is not None:
        payload["last_disconnect_at"] = _format_timestamp(_last_disconnect_time)
    if _last_publish_time is not None:
        payload["last_publish_at"] = _format_timestamp(_last_publish_time)

    return 200, payload


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health, config, live, and control UI endpoints."""
    def do_HEAD(self):
        path = urlparse(self.path).path
        while "//" in path:
            path = path.replace("//", "/")
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Minimal HEAD handling for common endpoints.
        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        if path in ("/", "/ui"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return
        if path == "/health":
            code, _ = health_snapshot()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return
        if path == "/circuits":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return
        # Default: 404 for unknown paths
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        # Normalize duplicate slashes and trailing slashes (except root)
        while "//" in path:
            path = path.replace("//", "/")
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-App-Build", APP_BUILD)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            spec = deepcopy(OPENAPI_SPEC)
            try:
                spec.setdefault("info", {})
                spec["info"]["x-build"] = APP_BUILD
                if spec["info"].get("version") and APP_BUILD:
                    spec["info"]["version"] = f"{spec['info']['version']}+{APP_BUILD}"
            except Exception:
                pass
            self.wfile.write(json.dumps(spec).encode())
            return

        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("X-App-Build", APP_BUILD)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            html = _load_static_html("docs.html", SWAGGER_HTML)
            self.wfile.write(html.encode("utf-8"))
            return

        if path in ("/", "/ui"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("X-App-Build", APP_BUILD)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            html = _load_static_html("ui.html", CONFIG_UI_HTML)
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/config":
            with _shadow_state_lock:
                current = {
                    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
                    "target_power_kw": _shadow_target_power_kw,
                    "enabled": _ven_enabled,
                    "meter_base_min_kw": _meter_base_min_kw,
                    "meter_base_max_kw": _meter_base_max_kw,
                    "meter_jitter_pct": _meter_jitter_pct,
                    "voltage_enabled": _voltage_enabled,
                    "voltage_nominal": _voltage_nominal,
                    "voltage_jitter_pct": _voltage_jitter_pct,
                    "current_enabled": _current_enabled,
                    "power_factor": _power_factor,
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(current).encode())
            return

        if path == "/live":
            code, status = health_snapshot()
            # Read basic config and shadow-derived bits under the lock, but
            # take the (potentially slower) circuits snapshot outside to avoid
            # holding the lock during nested calls.
            with _shadow_state_lock:
                cfg = {
                    "report_interval_seconds": REPORT_INTERVAL_SECONDS,
                    "target_power_kw": _shadow_target_power_kw,
                    "enabled": _ven_enabled,
                }
                events = None
                try:
                    evs = _shadow_reported_state.get("events") if isinstance(_shadow_reported_state, dict) else None
                    if isinstance(evs, dict):
                        # prefer backend event if present
                        events = evs.get("last_backend") or evs.get("last")
                except Exception:
                    events = None
                # Active event info for UI banner
                active_event = None
                if _active_event:
                    ae = _active_event
                    rem = max(0, int(ae.get("end_ts", 0)) - int(time.time()))
                    active_event = {
                        "eventId": ae.get("event_id"),
                        "requestedReductionKw": ae.get("requested_kw"),
                        "baselineKw": ae.get("baseline_kw"),
                        "deliveredKwh": ae.get("delivered_kwh"),
                        "startTs": ae.get("start_ts"),
                        "endTs": ae.get("end_ts"),
                        "remainingS": rem,
                    }
                # Last event summary for end-of-event banner
                last_event_summary = None
                try:
                    mets = _shadow_reported_state.get("metrics") if isinstance(_shadow_reported_state, dict) else None
                    if isinstance(mets, dict):
                        last_event_summary = mets.get("lastEventSummary")
                except Exception:
                    last_event_summary = None
            # Take circuits snapshot outside the lock to avoid re-entrancy.
            loads_live = _circuits_snapshot()
            # Ensure the UI can render circuits even before the first publish.
            metering_for_ui = _last_metering_sample if _last_metering_sample else {}
            try:
                if not isinstance(metering_for_ui, dict):
                    metering_for_ui = {}
                if "circuits" not in metering_for_ui:
                    metering_for_ui = dict(metering_for_ui)
                    metering_for_ui["circuits"] = loads_live
            except Exception:
                metering_for_ui = {"circuits": loads_live}

            live = {
                "status": status,
                "config": cfg,
                "metering": metering_for_ui,
                "events": events,
                "loads": loads_live,
                "activeEvent": active_event,
                "sheddingLoadIds": [lid for lid, lim in _load_limits.items() if int(lim.get("until", 0)) > int(time.time())],
                "lastEventSummary": last_event_summary,
            }
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(live).encode())
            return

        if path == "/circuits":
            data = _circuits_snapshot()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            return

        if path == "/presets":
            presets = [
                {"name": "normal", "title": "Normal", "desc": "Balanced defaults"},
                {"name": "dr_aggressive", "title": "DR Aggressive", "desc": "Minimize grid draw"},
                {"name": "pv_self_use", "title": "PV Self-Use", "desc": "Prefer charging battery"},
            ]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"presets": presets}).encode())
            return

        # /circuits/{id}
        if path.startswith("/circuits/"):
            cid = path.split("/", 2)[2]
            snap = _circuits_snapshot()
            for c in snap:
                if c["id"] == cid:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(c).encode())
                    return
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Circuit not found")
            return

        status, payload = health_snapshot()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_POST(self):
        path = urlparse(self.path).path
        while "//" in path:
            path = path.replace("//", "/")
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        if path == "/config":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON")
                return

            # Accept only known keys
            desired: dict[str, Any] = {}
            if isinstance(body, dict):
                if "report_interval_seconds" in body:
                    try:
                        desired["report_interval_seconds"] = max(1, int(body["report_interval_seconds"]))
                    except (TypeError, ValueError):
                        pass
                if "target_power_kw" in body:
                    try:
                        desired["target_power_kw"] = float(body["target_power_kw"])
                    except (TypeError, ValueError):
                        pass
                if "enabled" in body:
                    try:
                        desired["enabled"] = bool(body["enabled"])
                    except Exception:
                        pass
                for fld in (
                    "meter_base_min_kw", "meter_base_max_kw", "meter_jitter_pct",
                    "voltage_enabled", "voltage_nominal", "voltage_jitter_pct",
                    "current_enabled", "power_factor",
                ):
                    if fld in body:
                        desired[fld] = body[fld]

            updates = _apply_shadow_delta(desired)
            if updates:
                _shadow_merge_report(updates)
            _shadow_publish_desired(desired)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with _shadow_state_lock:
                now_enabled = _ven_enabled
            resp = {"applied": desired, "current_interval": REPORT_INTERVAL_SECONDS, "enabled": now_enabled}
            self.wfile.write(json.dumps(resp).encode())
            return

        # /circuits/{id} update (supports enabled, rated_kw)
        if path.startswith("/circuits/"):
            cid = path.split("/", 2)[2]
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON")
                return
            updated = None
            with _shadow_state_lock:
                for c in _circuits:
                    if c["id"] == cid:
                        if isinstance(body, dict) and "enabled" in body:
                            try:
                                c["enabled"] = bool(body["enabled"])
                            except Exception:
                                pass
                        if isinstance(body, dict) and "rated_kw" in body:
                            try:
                                c["rated_kw"] = max(0.0, float(body["rated_kw"]))
                            except Exception:
                                pass
                        if isinstance(body, dict) and "critical" in body:
                            try:
                                c["critical"] = bool(body["critical"])
                            except Exception:
                                pass
                        if isinstance(body, dict) and "priority" in body:
                            try:
                                c["priority"] = int(body["priority"])
                            except Exception:
                                pass
                        if isinstance(body, dict) and "connected" in body:
                            try:
                                c["connected"] = bool(body["connected"])
                            except Exception:
                                pass
                        if isinstance(body, dict) and "mode" in body:
                            try:
                                m = str(body["mode"]).lower()
                                if m in ("dynamic","fixed"):
                                    c["mode"] = m
                            except Exception:
                                pass
                        if isinstance(body, dict) and "fixed_kw" in body:
                            try:
                                c["fixed_kw"] = max(0.0, float(body["fixed_kw"]))
                            except Exception:
                                pass
                        updated = {
                            "id": c["id"],
                            "name": c["name"],
                            "type": c.get("type"),
                            "enabled": bool(c.get("enabled", True)),
                            "rated_kw": float(c.get("rated_kw", 0.0)),
                            "current_kw": float(c.get("current_kw", 0.0)),
                            "critical": bool(c.get("critical", False)),
                            "priority": int(c.get("priority", _circuit_priority.get(c.get("type", "misc"), 5))),
                            "connected": bool(c.get("connected", True)),
                            "mode": c.get("mode", "dynamic"),
                            "fixedKw": float(c.get("fixed_kw", 0.0)),
                        }
                        break
            if updated is None:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Circuit not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"circuit": updated}).encode())
            return

        if path == "/presets/apply":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
                name = str(body.get("name") or "").lower()
            except Exception:
                name = ""

            applied = _apply_preset(name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"applied": applied, "preset": name}).encode())
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")

        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Accept only known keys
        desired: dict[str, Any] = {}
        if isinstance(body, dict):
            if "report_interval_seconds" in body:
                try:
                    desired["report_interval_seconds"] = max(1, int(body["report_interval_seconds"]))
                except (TypeError, ValueError):
                    pass
            if "target_power_kw" in body:
                try:
                    desired["target_power_kw"] = float(body["target_power_kw"])
                except (TypeError, ValueError):
                    pass
            if "enabled" in body:
                try:
                    desired["enabled"] = bool(body["enabled"])
                except Exception:
                    pass
            for fld in (
                "meter_base_min_kw",
                "meter_base_max_kw",
                "meter_jitter_pct",
                "voltage_enabled",
                "voltage_nominal",
                "voltage_jitter_pct",
                "current_enabled",
                "power_factor",
            ):
                if fld in body:
                    desired[fld] = body[fld]

        # Apply locally via the same code-path as IoT shadow deltas
        updates = _apply_shadow_delta(desired)
        if updates:
            _shadow_merge_report(updates)
        # And publish desired so remote shadow reflects the change
        _shadow_publish_desired(desired)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        with _shadow_state_lock:
            now_enabled = _ven_enabled
        resp = {"applied": desired, "current_interval": REPORT_INTERVAL_SECONDS, "enabled": now_enabled}
        self.wfile.write(json.dumps(resp).encode())

def _start_health_server():
    """Start the HTTP health/config/control server in a background thread."""
    _srv_cls = _ThreadingHTTPServer or HTTPServer
    server = _srv_cls(("0.0.0.0", HEALTH_PORT), HealthHandler)
    try:
        # For ThreadingMixIn-based servers, make threads daemonic so they don't block shutdown
        if hasattr(server, "daemon_threads"):
            setattr(server, "daemon_threads", True)
    except Exception:
        pass
    server.serve_forever()

threading.Thread(target=_start_health_server, daemon=True).start()
print(f"🩺 Health server running on port {HEALTH_PORT}")

# ── message handler ────────────────────────────────────────────────────
def _next_power_reading() -> float:
    """Simulate next power reading based on config and target."""
    with _shadow_state_lock:
        target = _shadow_target_power_kw

    if target is None:
        # Base range when no target provided
        low, high = _meter_base_min_kw, _meter_base_max_kw
        if high < low:
            high = low
        return round(random.uniform(low, high), 2)

    # Jitter as a percentage of target (+/-)
    jitter = random.uniform(-_meter_jitter_pct, _meter_jitter_pct)
    return round(max(0.0, target * (1.0 + jitter)), 2)


def _next_voltage_reading() -> float:
    """Simulate next voltage reading based on config and jitter."""
    with _shadow_state_lock:
        nominal = _voltage_nominal
        jit = _voltage_jitter_pct
    jitter = random.uniform(-jit, jit)
    return round(max(1.0, nominal * (1.0 + jitter)), 1)


def on_event(_client, _userdata, msg):
    """MQTT callback for event messages; publish response and update shadow."""
    payload = json.loads(msg.payload.decode())
    print(f"Received event via MQTT: {payload}")
    response = {"ven_id": payload.get("ven_id", "ven123"), "response": "ack"}
    client.publish(MQTT_TOPIC_RESPONSES, json.dumps(response), qos=1)
    _shadow_merge_report({
        "status": {"last_event_ts": int(time.time())},
        "events": {"last": payload}
    })

# ── main loop ──────────────────────────────────────────────────────────
def main(iterations: int | None = None) -> None:
    """Main VEN agent loop: publish telemetry, handle events, update shadow."""
    global _last_publish_time
    client.message_callback_add(MQTT_TOPIC_EVENTS, on_event)
    client.subscribe(MQTT_TOPIC_EVENTS)
    print("✅ MQTT setup complete, starting VEN agent loop")
    # Subscribe to backend control plane topic if configured
    if BACKEND_CMD_TOPIC:
        client.message_callback_add(BACKEND_CMD_TOPIC, on_backend_cmd)
        client.subscribe(BACKEND_CMD_TOPIC)

    if SHADOW_TOPIC_DELTA:
        client.message_callback_add(SHADOW_TOPIC_DELTA, on_shadow_delta)
        client.subscribe(SHADOW_TOPIC_DELTA)

        if SHADOW_TOPIC_GET_ACCEPTED:
            client.message_callback_add(SHADOW_TOPIC_GET_ACCEPTED, on_shadow_get_accepted)
            client.subscribe(SHADOW_TOPIC_GET_ACCEPTED)

        if SHADOW_TOPIC_GET_REJECTED:
            client.message_callback_add(SHADOW_TOPIC_GET_REJECTED, on_shadow_get_rejected)
            client.subscribe(SHADOW_TOPIC_GET_REJECTED)

        _shadow_request_sync()
    else:
        if not IOT_THING_NAME:
            print("⚠️ IOT_THING_NAME not set; device shadow sync disabled.")

    count = 0
    while True:
        # If VEN is disabled, do not publish or interact with MQTT.
        # Sleep briefly to keep CPU low, and allow /config UI to re-enable.
        if not _ven_enabled:
            time.sleep(1)
            continue
        try:
            now = int(time.time())
            status_payload = {"ven": "ready"}
            # Build metering payload with optional fields
            # Compute panel step via circuit model
            step = _compute_panel_step(now)
            power_kw = step["power_kw"]
            metering_payload = {"timestamp": now, "power_kw": power_kw}
            with _shadow_state_lock:
                include_v = _voltage_enabled
                include_i = _current_enabled
                v_nom = _voltage_nominal
                pf = _power_factor

            if include_v:
                metering_payload["voltage_v"] = _next_voltage_reading()
                v_for_current = metering_payload["voltage_v"]
            else:
                v_for_current = v_nom

            if include_i and v_for_current > 0 and pf > 0:
                # P(kW) = V(V) * I(A) * PF / 1000  => I = P*1000/(V*PF)
                amps = (power_kw * 1000.0) / (v_for_current * pf)
                metering_payload["current_a"] = round(max(0.0, amps), 2)

            # Attach per-circuit snapshot and battery SOC
            metering_payload["circuits"] = step.get("circuits")
            metering_payload["battery_soc"] = step.get("battery_soc")

            # Update history and event-derived metrics
            try:
                _power_history.append((now, float(power_kw)))
            except Exception:
                pass

            # Determine if within active event window
            shed_power_kw = 0.0
            requested_kw = None
            event_id = None
            if _active_event:
                event_id = _active_event.get("event_id")
                st = int(_active_event.get("start_ts", 0))
                et = int(_active_event.get("end_ts", 0))
                if now >= et:
                    # Event ended
                    _active_event["ended_at"] = now
                if st <= now <= et:
                    requested_kw = _active_event.get("requested_kw")
                    # Compute baseline if missing: avg of last 5 samples before start
                    if _active_event.get("baseline_kw") is None:
                        prev = [v for (ts, v) in list(_power_history) if ts < st][-5:]
                        if prev:
                            _active_event["baseline_kw"] = sum(prev) / len(prev)
                    base = _active_event.get("baseline_kw")
                    if isinstance(base, (int, float)):
                        shed_power_kw = max(0.0, float(base) - float(power_kw))
                        # accumulate delivered kWh
                        step_h = max(1.0, REPORT_INTERVAL_SECONDS) / 3600.0
                        _active_event["delivered_kwh"] = float(_active_event.get("delivered_kwh") or 0.0) + shed_power_kw * step_h

            # Enrich telemetry
            telem = {
                "schemaVersion": SCHEMA_VERSION,
                "venId": VEN_ID,
                "timestamp": now,
                "usedPowerKw": power_kw,
                "shedPowerKw": round(shed_power_kw, 3),
            }
            if requested_kw is not None:
                telem["requestedReductionKw"] = float(requested_kw)
            if event_id is not None:
                telem["eventId"] = str(event_id)
            telem["loads"] = [
                {"id": c["id"], "currentPowerKw": float(c.get("current_kw", 0.0))}
                for c in (step.get("circuits") or [])
            ]
            if "battery_soc" in step:
                telem["batterySoc"] = step["battery_soc"]

            # Validate telemetry payload before publishing
            def validate_telem_payload(payload):
                required_fields = [
                    "schemaVersion", "venId", "timestamp", "usedPowerKw", "shedPowerKw", "loads"
                ]
                if payload.get("schemaVersion") != "1.0":
                    raise ValueError(f"Telemetry schemaVersion must be '1.0', got {payload.get('schemaVersion')}")
                for field in required_fields:
                    if field not in payload:
                        raise ValueError(f"Missing required telemetry field: {field}")
                if not isinstance(payload["loads"], list):
                    raise TypeError("Telemetry 'loads' must be a list")
                for load in payload["loads"]:
                    if "id" not in load or "currentPowerKw" not in load:
                        raise ValueError("Each load must have 'id' and 'currentPowerKw'")
            try:
                validate_telem_payload(telem)
            except Exception as err:
                import logging
                logging.basicConfig(level=logging.ERROR)
                logging.error(f"Telemetry validation error: {err}", exc_info=True)
                # Optionally: skip publish or send error telemetry
                # Publish error telemetry for observability
                error_payload = {
                    "schemaVersion": SCHEMA_VERSION,
                    "venId": VEN_ID,
                    "timestamp": now,
                    "error": str(err)
                }
                try:
                    client.publish(MQTT_TOPIC_METERING, json.dumps(error_payload), qos=1)
                except Exception as pub_err:
                    logging.error(f"Publish error telemetry failed: {pub_err}", exc_info=True)
                return

            # Back-compat: keep previous topic payload plus enriched telem keys
            import logging
            logging.basicConfig(level=logging.ERROR)
            try:
                payload = json.loads(msg.payload.decode())
                op = str(payload.get("op") or "set").lower()
                corr = payload.get("correlationId")
                data = payload.get("data")

                if op in ("set", "setconfig"):
                    with _with_update_source("backend_cmd"):
                        updates = _apply_config_payload(data if isinstance(data, dict) else payload)
                    _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
                    return
                if op == "enable":
                    with _with_update_source("backend_cmd"):
                        updates = _apply_config_payload({"enabled": True})
                    _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
                    return
                if op == "disable":
                    with _with_update_source("backend_cmd"):
                        updates = _apply_config_payload({"enabled": False})
                    _publish_ack(op, True, {"applied": updates}, correlation_id=corr)
                    return
                if op == "get":
                    what = str(payload.get("what") or "status").lower()
                    if what == "config":
                        with _shadow_state_lock:
                            cfg = {
                                "report_interval_seconds": REPORT_INTERVAL_SECONDS,
                                "target_power_kw": _shadow_target_power_kw,
                                "enabled": _ven_enabled,
                                "meter_base_min_kw": _meter_base_min_kw,
                                "meter_base_max_kw": _meter_base_max_kw,
                                "meter_jitter_pct": _meter_jitter_pct,
                                "voltage_enabled": _voltage_enabled,
                                "voltage_nominal": _voltage_nominal,
                                "voltage_jitter_pct": _voltage_jitter_pct,
                                "current_enabled": _current_enabled,
                                "power_factor": _power_factor,
                            }
                        _publish_ack(op, True, {"config": cfg}, correlation_id=corr)
                    else:
                        _code, status = health_snapshot()
                        _publish_ack(op, True, {"status": status}, correlation_id=corr)
                    return
                if op == "ping":
                    _publish_ack(op, True, {"pong": True, "ts": int(time.time())}, correlation_id=corr)
                    return
                if op == "shedload":
                    # Handle load shedding command
                    shed_amount = None
                    if isinstance(data, dict):
                        shed_amount = data.get("amountKw") or data.get("shed_kw")
                    # Simulate load shedding by adjusting target power
                    if shed_amount is not None:
                        with _shadow_state_lock:
                            _shadow_target_power_kw = max(0.0, float(shed_amount))
                        _publish_ack(op, True, {"shedAmount": shed_amount}, correlation_id=corr)
                    else:
                        logging.error("No shed amount provided in shedLoad command", exc_info=True)
                        _publish_ack(op, False, {"error": "No shed amount provided"}, correlation_id=corr)
                    return
                if op == "event":
                    ev = data if isinstance(data, dict) else {}
                    # Record event in shadow and optionally adjust target
                    ev_id = ev.get("event_id") or f"backend_{int(time.time())}"
                    shed_kw = ev.get("shed_kw")
                    start_ts = int(ev.get("start_ts") or int(time.time()))
                    duration_s = int(ev.get("duration_s") or 0)
                    end_ts = int(ev.get("end_ts") or (start_ts + duration_s if duration_s > 0 else start_ts))
                    req_kw = ev.get("requestedReductionKw") or ev.get("requested_kw")
                    updates: dict[str, Any] = {
                        "status": {"last_backend_event_ts": int(time.time())},
                        "events": {"last_backend": {"event_id": ev_id, **ev}},
                    }
                    if isinstance(shed_kw, (int, float)):
                        # For a simple demo, interpret shed_kw as a target power cap
                        updates["target_power_kw"] = max(0.0, float(shed_kw))
                        with _shadow_state_lock:
                            try:
                                _shadow_target_power_kw = float(updates["target_power_kw"])
                            except Exception as e:
                                logging.error(f"Failed to set target_power_kw: {e}", exc_info=True)
                    return
            except Exception as err:
                logging.error(f"Error handling backend command: {err}", exc_info=True)

            count += 1
            if iterations is not None and count >= iterations:
                break
        except Exception as loop_err:
            print(f"Loop error (continuing): {loop_err}", file=sys.stderr)
        # Add slight jitter to reduce thundering herd across instances
        sleep_s = REPORT_INTERVAL_SECONDS
        try:
            jitter = max(0.0, min(0.25 * REPORT_INTERVAL_SECONDS, random.uniform(0, 0.1 * REPORT_INTERVAL_SECONDS)))
            sleep_s = REPORT_INTERVAL_SECONDS + jitter
        except Exception:
            pass
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()

// SVP — Sandbox Vulnerability Pi
// Frontend logic: scan → fingerprint → CVE lookup

// ── Scan ─────────────────────────────────────────────────────────────────────
async function runScan() {
  const btn    = document.getElementById('btn-scan');
  const status = document.getElementById('scan-status');
  const list   = document.getElementById('host-list');

  btn.disabled = true;
  btn.textContent = '▶ SCANNING...';
  status.textContent = 'Running host discovery... this may take 10-30 seconds.';
  list.innerHTML = '';

  try {
    const res  = await fetch('/api/scan', { method: 'POST' });
    const data = await res.json();

    if (!data.ok) { status.textContent = 'Error: ' + data.error; return; }

    const hosts = data.hosts;
    status.textContent = `${hosts.length} host${hosts.length !== 1 ? 's' : ''} discovered.`;

    if (hosts.length === 0) {
      list.innerHTML = '<div class="msg-box">No hosts found on the network.</div>';
      return;
    }

    list.innerHTML = `<div class="host-grid">${hosts.map(hostCard).join('')}</div>`;
  } catch(e) {
    status.textContent = 'Connection error. Is the SVP server running?';
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ RUN SCAN';
  }
}

function hostCard(h) {
  const vendor = h.vendor || 'Unknown vendor';
  const mac    = h.mac    || 'N/A';
  const query  = encodeURIComponent(vendor);
  return `
  <div class="host-card">
    <div class="host-ip">${h.ip}</div>
    <div class="host-meta">
      ${h.hostname !== 'unknown' ? `hostname: ${h.hostname}<br>` : ''}
      mac: ${mac}<br>
      vendor: ${vendor}<br>
      status: <span style="color:var(--green)">${h.status}</span>
    </div>
    <div class="host-actions">
      <button class="btn-fp"  onclick="runFingerprint('${h.ip}')">FINGERPRINT</button>
      <button class="btn-cve" onclick="openCVE('${vendor}')">CVE LOOKUP</button>
    </div>
  </div>`;
}

// ── Fingerprint ───────────────────────────────────────────────────────────────
async function runFingerprint(ip) {
  const panel  = document.getElementById('panel-fp');
  const target = document.getElementById('fp-target');
  const status = document.getElementById('fp-status');
  const result = document.getElementById('fp-result');

  panel.style.display = 'block';
  panel.scrollIntoView({ behavior: 'smooth' });
  target.textContent = ip;
  status.textContent = `Probing ${ip} — OS detection + service versions (may take 30-60s)...`;
  result.innerHTML   = '';

  try {
    const res  = await fetch('/api/fingerprint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    const data = await res.json();
    if (!data.ok) { status.textContent = 'Error: ' + data.error; return; }

    const fp = data.result;
    status.textContent = `Done. ${fp.ports.length} open port${fp.ports.length !== 1 ? 's' : ''} found.`;

    const portRows = fp.services.map(s => `
      <div class="port-row">
        <span class="port-num">${s.port}/${s.proto}</span>
        <span class="port-svc">${s.service}</span>
        <span class="port-ver">${s.version || ''}</span>
      </div>`).join('') || '<div class="port-row" style="color:var(--dim)">No open ports detected</div>';

    result.innerHTML = `
      <div class="fp-grid">
        <div class="fp-box">
          <h3>OS DETECTION</h3>
          <div class="fp-os">${fp.os}</div>
        </div>
        <div class="fp-box">
          <h3>OPEN PORTS (${fp.ports.length})</h3>
          ${portRows}
        </div>
      </div>`;

    // Pre-fill CVE search with most useful keyword from fingerprint
    const topService = fp.services[0];
    if (topService) {
      const kw = `${topService.service} ${topService.version}`.trim();
      document.getElementById('cve-query').value = kw;
    }

    // Show CVE panel
    openCVE('');

  } catch(e) {
    status.textContent = 'Error connecting to server.';
  }
}

// ── CVE Lookup ────────────────────────────────────────────────────────────────
function openCVE(prefill) {
  const panel = document.getElementById('panel-cve');
  panel.style.display = 'block';
  panel.scrollIntoView({ behavior: 'smooth' });
  document.getElementById('cve-target').textContent = prefill || '';
  if (prefill) document.getElementById('cve-query').value = prefill;
}

async function runCVE() {
  const query   = document.getElementById('cve-query').value.trim();
  const status  = document.getElementById('cve-status');
  const results = document.getElementById('cve-results');

  if (!query) return;

  status.textContent  = `Querying NVD for: "${query}"...`;
  results.innerHTML   = '';
  document.getElementById('cve-target').textContent = query;

  try {
    const res  = await fetch('/api/cve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: query, count: 20 })
    });
    const data = await res.json();
    if (!data.ok) { status.textContent = 'Error: ' + data.error; return; }

    const cves = data.results;
    status.textContent = `${cves.length} CVE${cves.length !== 1 ? 's' : ''} found.`;

    if (cves.length === 0) {
      results.innerHTML = `<div class="msg-box">No CVEs found for "${query}".</div>`;
      return;
    }

    results.innerHTML = `<div class="cve-list">${cves.map(cveCard).join('')}</div>`;
  } catch(e) {
    status.textContent = 'Error connecting to server.';
  }
}

function cveCard(c) {
  const score = c.score !== null ? c.score.toFixed(1) : 'N/A';
  const sev   = c.severity || 'NA';
  const desc  = c.description.length > 350 ? c.description.slice(0, 350) + '...' : c.description;
  return `
  <div class="cve-card ${sev}">
    <div class="cve-header">
      <span class="cve-id" onclick="window.open('${c.url}','_blank')">${c.id}</span>
      <span class="cvss ${sev}">${sev} ${score}</span>
    </div>
    <div class="cve-desc">${desc}</div>
    <div class="cve-meta">
      <span>📅 ${c.published}</span>
      <span>🔄 ${c.modified}</span>
      <span>🔗 ${c.references} refs</span>
    </div>
  </div>`;
}

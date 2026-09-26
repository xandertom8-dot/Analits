// ============================================================
// static/js/utils.js
// Utilidades puras: formateo, API helpers, DOM helpers.
// Mientras migramos, se carga como <script> clásico.
// ============================================================

// ============================================================
// API HELPERS
// ============================================================
async function apiGet(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error en API: ' + url);
    return await response.json();
}

async function apiPost(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return await response.json();
}

async function apiPut(url, body) {
    const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return await response.json();
}

async function apiDelete(url) {
    const response = await fetch(url, { method: 'DELETE' });
    return await response.json();
}

// ============================================================
// FORMATEO
// ============================================================
function fmt(n, dec = 2) {
    if (n === null || n === undefined) return '—';
    return Number(n).toFixed(dec);
}

function fmtPct(n, dec = 1) {
    if (n === null || n === undefined) return '—';
    return Number(n * 100).toFixed(dec) + '%';
}

function fmtPctSigned(n, dec = 1) {
    if (n === null || n === undefined) return '—';
    const val = Number(n * 100).toFixed(dec);
    return (n > 0 ? '+' : '') + val + '%';
}

function fmtFecha(iso) {
    if (!iso) return '—';
    return iso.slice(0, 10);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ============================================================
// DOM HELPERS
// ============================================================
function llenarSelect(select, opciones, textoDefault) {
    select.innerHTML = `<option value="">${textoDefault}</option>`;
    for (const op of opciones) {
        const option = document.createElement('option');
        option.value = op;
        option.textContent = op;
        select.appendChild(option);
    }
}

function llenarSelectConId(select, items, textoDefault) {
    select.innerHTML = `<option value="">${textoDefault}</option>`;
    for (const item of items) {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = item.name;
        opt.dataset.name = item.name;
        select.appendChild(opt);
    }
}

function getSelectValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

function getSelectName(id) {
    const sel = document.getElementById(id);
    if (!sel) return '';
    const opt = sel.options[sel.selectedIndex];
    return opt?.dataset?.name || '';
}

// ============================================================
// COLORES / ESTILOS
// ============================================================
function colorPorCV(cv) {
    if (cv === null || cv === undefined) return '#8899aa';
    if (cv < 0.4) return '#00ff88';
    if (cv < 0.7) return '#ffaa00';
    return '#ff4455';
}

function colorPorProb(prob, umbralAlto = 0.6, umbralMedio = 0.45) {
    if (prob === null || prob === undefined) return '#8899aa';
    if (prob >= umbralAlto) return '#00ff88';
    if (prob >= umbralMedio) return '#ffaa00';
    return '#ff4455';
}

function colorPorEV(ev) {
    if (ev === null || ev === undefined) return '#8899aa';
    if (ev > 5) return '#00ff88';
    if (ev > 0) return '#ffaa00';
    return '#ff4455';
}
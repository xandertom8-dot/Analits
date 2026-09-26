// ============================================================
// static/js/pronostico/render/goles.js
// Secciones: 1X2, Doble Oportunidad, BTTS, Over/Under,
// Goles por Equipo, Top Marcadores.
// ============================================================

function mostrarSeccion1X2(data) {
    const m = data.mercados;
    if (!m || !m['1X2']) return '';

    const l = m['1X2'].local;
    const e = m['1X2'].empate;
    const v = m['1X2'].visitante;

    const ic = data.intervalos_confianza || {};
    const icL = ic.local, icE = ic.empate, icV = ic.visitante;

    const probMax = Math.max(l, e, v);
    const favorito = probMax === l ? 'local' : (probMax === e ? 'empate' : 'visitante');

    const colorFav = favorito === 'local' ? '#00d4ff' : (favorito === 'empate' ? '#ffaa00' : '#ff8844');

    return `
    <div class="result-card" style="border-left-color:${colorFav};">
        <div class="market" style="color:${colorFav};">🏆 1X2 — GANADOR DEL PARTIDO</div>
        <div class="comparison-row" style="margin-top:15px;">
            <div class="comparison-item" style="${favorito === 'local' ? 'border-color:#00d4ff; box-shadow:0 0 15px rgba(0,212,255,0.2);' : ''}">
                <div class="label">🏠 ${data.local}</div>
                <div class="value local-color" style="font-size:1.6em;">${fmtPct(l)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / l)}</div>
                ${icL ? `<div style="color:#8899aa; font-size:0.7em; margin-top:5px;">IC 90%: ${fmtPct(icL.min)} – ${fmtPct(icL.max)}</div>` : ''}
            </div>
            <div class="comparison-item" style="${favorito === 'empate' ? 'border-color:#ffaa00; box-shadow:0 0 15px rgba(255,170,0,0.2);' : ''}">
                <div class="label">🤝 Empate</div>
                <div class="value" style="color:#ffaa00; font-size:1.6em;">${fmtPct(e)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / e)}</div>
                ${icE ? `<div style="color:#8899aa; font-size:0.7em; margin-top:5px;">IC 90%: ${fmtPct(icE.min)} – ${fmtPct(icE.max)}</div>` : ''}
            </div>
            <div class="comparison-item" style="${favorito === 'visitante' ? 'border-color:#ff8844; box-shadow:0 0 15px rgba(255,136,68,0.2);' : ''}">
                <div class="label">✈️ ${data.visitante}</div>
                <div class="value visitante-color" style="font-size:1.6em;">${fmtPct(v)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / v)}</div>
                ${icV ? `<div style="color:#8899aa; font-size:0.7em; margin-top:5px;">IC 90%: ${fmtPct(icV.min)} – ${fmtPct(icV.max)}</div>` : ''}
            </div>
        </div>
        <p style="color:#8899aa; font-size:0.8em; margin-top:12px; text-align:center;">
            Favorito: <strong style="color:${colorFav};">${favorito === 'local' ? data.local : (favorito === 'empate' ? 'Empate' : data.visitante)}</strong>
            (${fmtPct(probMax)})
        </p>
    </div>`;
}

function mostrarSeccionDobleOportunidad(data) {
    const doble = data.mercados?.doble_oportunidad;
    if (!doble) return '';

    const x1 = doble['1X'];
    const x12 = doble['12'];
    const x2 = doble['X2'];

    return `
    <div class="result-card" style="border-left-color:#00ff88;">
        <div class="market" style="color:#00ff88;">🎯 DOBLE OPORTUNIDAD</div>
        <div class="comparison-row" style="margin-top:15px;">
            <div class="comparison-item">
                <div class="label">1X — ${data.local} o Empate</div>
                <div class="value" style="color:#00d4ff; font-size:1.5em;">${fmtPct(x1)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / x1)}</div>
            </div>
            <div class="comparison-item">
                <div class="label">12 — Sin empate</div>
                <div class="value" style="color:#ffaa00; font-size:1.5em;">${fmtPct(x12)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / x12)}</div>
            </div>
            <div class="comparison-item">
                <div class="label">X2 — Empate o ${data.visitante}</div>
                <div class="value" style="color:#ff8844; font-size:1.5em;">${fmtPct(x2)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / x2)}</div>
            </div>
        </div>
    </div>`;
}

function mostrarSeccionBTTS(data) {
    const m = data.mercados;
    if (!m || m.BTTS === undefined) return '';

    const btts = m.BTTS;
    const noBtts = 1 - btts;
    const ic = data.intervalos_confianza?.BTTS;

    const color = btts >= 0.6 ? '#00ff88' : (btts >= 0.45 ? '#ffaa00' : '#ff4455');

    return `
    <div class="result-card" style="border-left-color:${color};">
        <div class="market" style="color:${color};">⚽ BTTS — AMBOS EQUIPOS MARCAN</div>
        <div class="comparison-row" style="margin-top:15px;">
            <div class="comparison-item" style="border-color:${color};">
                <div class="label">✅ SÍ (ambos marcan)</div>
                <div class="value" style="color:${color}; font-size:1.6em;">${fmtPct(btts)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / btts)}</div>
                ${ic ? `<div style="color:#8899aa; font-size:0.7em; margin-top:5px;">IC 90%: ${fmtPct(ic.min)} – ${fmtPct(ic.max)}</div>` : ''}
            </div>
            <div class="comparison-item">
                <div class="label">❌ NO</div>
                <div class="value" style="color:#8899aa; font-size:1.6em;">${fmtPct(noBtts)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / noBtts)}</div>
            </div>
        </div>
    </div>`;
}

function mostrarSeccionOverUnder(data, lineaBase) {
    const m = data.mercados;
    if (!m || !m.over || m.over[lineaBase] === undefined) return '';

    const over = m.over[lineaBase];
    const under = m.under[lineaBase];

    const icKey = lineaBase === 2.5 ? 'Over_2_5' : null;
    const ic = icKey ? data.intervalos_confianza?.[icKey] : null;

    const lambdaTotal = data.lambdas?.total_esperado;

    const color = over >= 0.55 ? '#00ff88' : (over >= 0.45 ? '#ffaa00' : '#ff4455');

    // Lista de otras líneas
    let otrasLineas = '';
    for (const linea of [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]) {
        if (linea === lineaBase) continue;
        if (m.over[linea] === undefined) continue;
        otrasLineas += `
        <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a2a3a;font-size:0.85em;">
            <span style="color:#8899aa;">Over ${linea}</span>
            <strong style="color:#e0e0e0;">${fmtPct(m.over[linea])}</strong>
        </div>`;
    }

    return `
    <div class="result-card" style="border-left-color:${color};">
        <div class="market" style="color:${color};">📊 OVER / UNDER ${lineaBase} GOLES</div>
        <div class="comparison-row" style="margin-top:15px;">
            <div class="comparison-item" style="border-color:${color};">
                <div class="label">⬆️ Over ${lineaBase}</div>
                <div class="value" style="color:${color}; font-size:1.6em;">${fmtPct(over)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / over)}</div>
                ${ic ? `<div style="color:#8899aa; font-size:0.7em; margin-top:5px;">IC 90%: ${fmtPct(ic.min)} – ${fmtPct(ic.max)}</div>` : ''}
            </div>
            <div class="comparison-item">
                <div class="label">⬇️ Under ${lineaBase}</div>
                <div class="value" style="color:#8899aa; font-size:1.6em;">${fmtPct(under)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / under)}</div>
            </div>
        </div>
        <div style="margin-top:15px; padding-top:12px; border-top:1px solid #1a2a3a;">
            <p style="color:#8899aa; font-size:0.8em; margin-bottom:8px;">
                Goles esperados totales (λ): <strong style="color:#00d4ff;">${fmt(lambdaTotal)}</strong>
            </p>
            ${otrasLineas ? `<div style="margin-top:10px;">${otrasLineas}</div>` : ''}
        </div>
    </div>`;
}

function mostrarSeccionGolesEquipo(data, lado) {
    const goles = data.mercados?.[`goles_${lado}`];
    if (!goles) return '';

    const nombre = lado === 'local' ? data.local : data.visitante;
    const color = lado === 'local' ? '#00d4ff' : '#ff8844';
    const emoji = lado === 'local' ? '🏠' : '✈️';

    return `
    <div class="result-card" style="border-left-color:${color};">
        <div class="market" style="color:${color};">${emoji} GOLES DE ${nombre.toUpperCase()}</div>
        <div style="margin-top:15px;">
            <table style="width:100%; border-collapse:collapse; font-size:0.9em;">
                <thead>
                    <tr style="color:#8899aa; border-bottom:1px solid #1a2a3a;">
                        <th style="text-align:left; padding:8px 0;">Goles</th>
                        <th style="text-align:center;">Probabilidad</th>
                        <th style="text-align:center;">Cuota justa</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:8px 0;">0 goles</td>
                        <td style="text-align:center; font-weight:700;">${fmtPct(goles['0'])}</td>
                        <td style="text-align:center; color:#8899aa;">${fmt(1 / goles['0'])}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:8px 0;">1 gol</td>
                        <td style="text-align:center; font-weight:700;">${fmtPct(goles['1'])}</td>
                        <td style="text-align:center; color:#8899aa;">${fmt(1 / goles['1'])}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:8px 0;">2 goles</td>
                        <td style="text-align:center; font-weight:700;">${fmtPct(goles['2'])}</td>
                        <td style="text-align:center; color:#8899aa;">${fmt(1 / goles['2'])}</td>
                    </tr>
                    <tr>
                        <td style="padding:8px 0;">3+ goles</td>
                        <td style="text-align:center; font-weight:700; color:${color};">${fmtPct(goles['3+'])}</td>
                        <td style="text-align:center; color:#8899aa;">${fmt(1 / goles['3+'])}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`;
}

function mostrarSeccionTopMarcadores(data) {
    const top = data.mercados?.top_marcadores;
    if (!top || top.length === 0) return '';

    let filas = '';
    for (let i = 0; i < Math.min(10, top.length); i++) {
        const m = top[i];
        const prob = m.probabilidad;
        filas += `
        <tr style="border-bottom:1px solid #1a2a3a;">
            <td style="padding:6px 0; color:#8899aa;">#${i + 1}</td>
            <td style="padding:6px 0; font-weight:700; font-family:monospace; font-size:1.05em;">${m.marcador}</td>
            <td style="text-align:center; font-weight:700; color:#00d4ff;">${fmtPct(prob, 2)}</td>
            <td style="text-align:center; color:#8899aa;">${fmt(1 / prob)}</td>
        </tr>`;
    }

    return `
    <div class="result-card" style="border-left-color:#ffaa00;">
        <div class="market" style="color:#ffaa00;">🎲 TOP 10 MARCADORES MÁS PROBABLES</div>
        <div style="margin-top:15px;">
            <table style="width:100%; border-collapse:collapse; font-size:0.9em;">
                <thead>
                    <tr style="color:#8899aa; border-bottom:1px solid #1a2a3a;">
                        <th style="text-align:left; padding:8px 0;">#</th>
                        <th style="text-align:left;">Marcador</th>
                        <th style="text-align:center;">Probabilidad</th>
                        <th style="text-align:center;">Cuota justa</th>
                    </tr>
                </thead>
                <tbody>${filas}</tbody>
            </table>
        </div>
    </div>`;
}
// ============================================================
// static/js/pronostico/render/tarjetas.js
// Secciones: Tarjetas (vista completa + línea individual).
// ============================================================

function mostrarSeccionTarjetas(data) {
    const mt = data.mercados_tarjetas;
    if (!mt) return '';

    const localEsp = mt.local_esperado;
    const visitEsp = mt.visitante_esperado;
    const totalEsp = mt.total_esperado;

    let lineasHtml = '';
    for (const linea of [1.5, 2.5, 3.5, 4.5, 5.5]) {
        const over = mt.over?.[linea];
        const under = mt.under?.[linea];
        if (over === undefined) continue;

        const color = over >= 0.6 ? '#00ff88' : (over >= 0.45 ? '#ffaa00' : '#ff4455');
        lineasHtml += `
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;padding:8px 0;border-bottom:1px solid #1a2a3a;font-size:0.85em;">
            <span style="color:#8899aa;">Línea ${linea}</span>
            <span style="text-align:center;color:${color};font-weight:700;">O: ${fmtPct(over)}</span>
            <span style="text-align:center;color:#8899aa;">U: ${fmtPct(under)}</span>
        </div>`;
    }

    let topHtml = '';
    if (mt.top_totales && mt.top_totales.length > 0) {
        topHtml = '<div style="margin-top:12px;"><p style="color:#8899aa;font-size:0.8em;margin-bottom:6px;">Tarjetas totales más probables:</p>';
        for (const t of mt.top_totales.slice(0, 5)) {
            topHtml += `<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:0.8em;">
            <span>${t.tarjetas} tarjetas</span>
            <strong style="color:#ffaa00;">${fmtPct(t.probabilidad)}</strong>
        </div>`;
        }
        topHtml += '</div>';
    }

    return `
    <div class="result-card" style="border-left-color:#ffaa00;">
        <div class="market" style="color:#ffaa00;">🟨 TARJETAS</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:15px;text-align:center;">
            <div>
                <div style="color:#00d4ff;font-weight:700;font-size:0.85em;">${data.local}</div>
                <div style="font-size:1.5em;color:#00d4ff;font-weight:700;">${fmt(localEsp)}</div>
            </div>
            <div>
                <div style="color:#8899aa;font-size:0.75em;">TOTAL ESPERADO</div>
                <div style="font-size:1.5em;color:#ffffff;font-weight:700;">${fmt(totalEsp)}</div>
            </div>
            <div>
                <div style="color:#ff8844;font-weight:700;font-size:0.85em;">${data.visitante}</div>
                <div style="font-size:1.5em;color:#ff8844;font-weight:700;">${fmt(visitEsp)}</div>
            </div>
        </div>
        ${lineasHtml ? `<div style="margin-top:15px;padding-top:12px;border-top:1px solid #1a2a3a;">${lineasHtml}</div>` : ''}
        ${topHtml}
                ${mt.local?.factor_localia ? `<div style="margin-top:12px; padding-top:10px; border-top:1px dashed #1a2a3a;">
            <p style="color:#8899aa; font-size:0.75em; margin-bottom:6px;">🔬 Factores aplicados</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.8em;">
                <div>
                    <div style="color:#00d4ff; font-weight:700; font-size:0.75em; margin-bottom:4px;">${data.local}</div>
                    <div style="color:#8899aa;">Localía: <strong style="color:#ffaa00;">×${fmt(mt.local.factor_localia, 3)}</strong></div>
                    <div style="color:#8899aa;">Racha: <strong style="color:${(mt.local.factor_racha_tarjetas || 1) > 1 ? '#00ff88' : ((mt.local.factor_racha_tarjetas || 1) < 1 ? '#ff4455' : '#8899aa')};">×${fmt(mt.local.factor_racha_tarjetas, 3)}</strong> <span style="color:#8899aa; font-size:0.9em;">(${mt.local.tipo_racha_tarjetas || '—'})</span></div>
                    <div style="color:#8899aa;">Tendencia: <strong style="color:${(mt.local.factor_tendencia_tarjetas || 1) > 1 ? '#00ff88' : ((mt.local.factor_tendencia_tarjetas || 1) < 1 ? '#ff4455' : '#8899aa')};">×${fmt(mt.local.factor_tendencia_tarjetas, 3)}</strong> <span style="color:#8899aa; font-size:0.9em;">(${mt.local.tipo_tendencia_tarjetas || '—'})</span></div>
                </div>
                <div>
                    <div style="color:#ff8844; font-weight:700; font-size:0.75em; margin-bottom:4px;">${data.visitante}</div>
                    <div style="color:#8899aa;">Localía: <strong style="color:#ffaa00;">×${fmt(mt.visitante.factor_localia, 3)}</strong></div>
                    <div style="color:#8899aa;">Racha: <strong style="color:${(mt.visitante.factor_racha_tarjetas || 1) > 1 ? '#00ff88' : ((mt.visitante.factor_racha_tarjetas || 1) < 1 ? '#ff4455' : '#8899aa')};">×${fmt(mt.visitante.factor_racha_tarjetas, 3)}</strong> <span style="color:#8899aa; font-size:0.9em;">(${mt.visitante.tipo_racha_tarjetas || '—'})</span></div>
                    <div style="color:#8899aa;">Tendencia: <strong style="color:${(mt.visitante.factor_tendencia_tarjetas || 1) > 1 ? '#00ff88' : ((mt.visitante.factor_tendencia_tarjetas || 1) < 1 ? '#ff4455' : '#8899aa')};">×${fmt(mt.visitante.factor_tendencia_tarjetas, 3)}</strong> <span style="color:#8899aa; font-size:0.9em;">(${mt.visitante.tipo_tendencia_tarjetas || '—'})</span></div>
                </div>
            </div>
        </div>` : ''}
    </div>`;
}

function mostrarSeccionTarjetasLinea(data, linea) {
    const mt = data.mercados_tarjetas;
    if (!mt || !mt.over || mt.over[linea] === undefined) return '';

    const over = mt.over[linea];
    const under = mt.under[linea];
    const color = over >= 0.6 ? '#00ff88' : (over >= 0.45 ? '#ffaa00' : '#ff4455');

    return `
    <div class="result-card" style="border-left-color:${color};">
        <div class="market" style="color:${color};">🟨 TARJETAS — LÍNEA ${linea}</div>
        <div class="comparison-row" style="margin-top:15px;">
            <div class="comparison-item" style="border-color:${color};">
                <div class="label">⬆️ Over ${linea}</div>
                <div class="value" style="color:${color}; font-size:1.6em;">${fmtPct(over)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / over)}</div>
            </div>
            <div class="comparison-item">
                <div class="label">⬇️ Under ${linea}</div>
                <div class="value" style="color:#8899aa; font-size:1.6em;">${fmtPct(under)}</div>
                <div style="color:#8899aa; font-size:0.75em;">Cuota justa: ${fmt(1 / under)}</div>
            </div>
        </div>
        <div style="margin-top:15px; text-align:center;">
            <span style="color:#8899aa; font-size:0.85em;">
                Total esperado: <strong style="color:#ffaa00;">${fmt(mt.total_esperado)}</strong> tarjetas
                (${data.local}: ${fmt(mt.local_esperado)} · ${data.visitante}: ${fmt(mt.visitante_esperado)})
            </span>
        </div>
    </div>`;
}
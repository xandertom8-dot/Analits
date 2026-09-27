// ============================================================
// static/js/pronostico/render/valor.js
// Sección: Valor esperado (EV) + Kelly stake sugerido.
// ============================================================

function mostrarSeccionValor(data, mercadoFiltro = 'todos') {
    const valor = data.valor || [];
    if (valor.length === 0) return '';

    // Leer config de Kelly
    const kellyConfig = cargarKellyConfig();
    const fraccionLabel = kellyConfig.fraccionLabel || 'cuarto';

    // Filtrar por categoría según mercado
    let filtrados = valor;
    if (mercadoFiltro === '1X2') {
        filtrados = valor.filter(v => v.categoria === 'goles' && v.mercado.includes('1X2'));
    } else if (mercadoFiltro === 'BTTS') {
        filtrados = valor.filter(v => v.mercado.includes('BTTS'));
    } else if (mercadoFiltro === 'Over_2.5') {
        filtrados = valor.filter(v => v.mercado === 'Over 2.5');
    } else if (mercadoFiltro === 'Over_3.5') {
        filtrados = valor.filter(v => v.mercado === 'Over 3.5');
    } else if (mercadoFiltro === 'Corners') {
        filtrados = valor.filter(v => v.categoria === 'corners');
    } else if (mercadoFiltro === 'Tarjetas') {
        filtrados = valor.filter(v => v.categoria === 'tarjetas');
    }

    if (filtrados.length === 0) {
        return `
        <div class="result-card" style="border-left-color:#8899aa;">
            <div class="market" style="color:#8899aa;">💰 VALOR ESPERADO</div>
            <p style="color:#8899aa;font-size:0.9em;margin-top:10px;">No hay mercados de valor para este filtro. Introduce una cuota para calcular EV.</p>
        </div>`;
    }

    let filas = '';
    for (const v of filtrados) {
        const tieneCuota = v.tiene_cuota && v.cuota > 0;
        const ev = v.EV;
        const evClass = ev === null ? '' : (ev > 5 ? 'ev-positive' : (ev > 0 ? 'ev-neutral' : 'ev-negative'));

        // Decisión del edge ajustado
        let decisionHtml = '';
        if (v.decision) {
            const colores = {
                'VALUE_FUERTE': '#00ff88',
                'VALUE': '#00d4ff',
                'MARGINAL': '#ffaa00',
                'NO_BET': '#ff4455'
            };
            const color = colores[v.decision] || '#8899aa';
            decisionHtml = `<span style="background:${color}22; color:${color}; padding:2px 8px; border-radius:10px; font-size:0.7em; font-weight:700; margin-left:8px;">${v.decision}</span>`;
        }

        // ========== BLOQUE KELLY ==========
        let kellyHtml = '';
        if (v.kelly) {
            const kellyActiva = v.kelly[fraccionLabel];

            if (kellyActiva) {
                const stakePct = kellyActiva.stake_pct * 100;
                const stakeDinero = kellyActiva.stake_dinero;
                const esValue = kellyActiva.es_value;
                const colorStake = esValue ? (kellyActiva.recomendacion === 'VALUE_FUERTE' ? '#00ff88' : '#00d4ff') : '#ff4455';

                // Desglose de las 4 fracciones
                let desglose = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px;font-size:0.75em;">';
                for (const [key, label] of [['completo','Kelly'], ['medio','1/2 K'], ['cuarto','1/4 K'], ['octavo','1/8 K']]) {
                    const k = v.kelly[key];
                    if (!k) continue;
                    const activa = key === fraccionLabel;
                    const colorKey = activa ? '#00ff88' : '#8899aa';
                    const minimoAplicado = k.stake_minimo_aplicado === true;
                    desglose += `
                        <div style="background:${activa ? '#00ff8822' : '#0a121c'}; padding:6px; border-radius:6px; text-align:center; border:1px solid ${activa ? '#00ff8866' : '#1a2a3a'};">
                            <div style="color:${colorKey}; font-size:0.7em; font-weight:700;">${label}${activa ? ' ★' : ''}</div>
                            <div style="color:#e0e0e0; font-weight:700; font-size:0.9em;">${(k.stake_pct*100).toFixed(2)}%</div>
                            <div style="color:#8899aa; font-size:0.75em;">${k.stake_dinero.toFixed(0)} COP</div>
                            ${minimoAplicado ? `<div style="color:#ffaa00; font-size:0.65em; margin-top:2px;">⚠️ mín.</div>` : ''}
                        </div>`;
                }
                desglose += '</div>';

                kellyHtml = `
                    <div style="margin-top:10px; padding:10px; background:#0a121c; border-radius:6px; border:1px solid ${colorStake}44;">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                            <span style="color:#8899aa; font-size:0.8em;">💰 STAKE SUGERIDO (${fraccionLabel})</span>
                            <span style="color:${colorStake}; font-weight:700; font-size:1em;">
                                ${stakeDinero.toFixed(0)} COP · ${stakePct.toFixed(2)}%
                            </span>
                        </div>
                        ${desglose}
                        ${!esValue ? `<p style="color:#ff4455; font-size:0.75em; margin-top:6px;">⚠️ Kelly negativo: no apostar</p>` : ''}
                        ${kellyActiva.stake_minimo_aplicado ? `<p style="color:#ffaa00; font-size:0.75em; margin-top:6px;">⚠️ Stake subido al mínimo (${data.stake_minimo_usado?.toFixed(0) || '500'} COP)</p>` : ''}
                    </div>`;
                    }
        }

        filas += `
        <div style="padding:12px 0; border-bottom:1px solid #1a2a3a;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <strong style="color:#e0e0e0;">${v.mercado}</strong>
                    <span style="color:#8899aa;font-size:0.75em;margin-left:8px;">${v.categoria}</span>
                    ${decisionHtml}
                </div>
                <div style="text-align:right;">
                    ${tieneCuota
                        ? `<span class="${evClass}" style="font-size:1.1em;">EV: ${ev > 0 ? '+' : ''}${fmt(ev)}%</span>`
                        : `<span style="color:#8899aa;font-size:0.85em;">Sin cuota</span>`}
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;margin-top:8px;font-size:0.8em;">
                <div>
                    <span style="color:#8899aa;">Probabilidad</span><br>
                    <strong style="color:#00d4ff;">${fmtPct(v.probabilidad)}</strong>
                </div>
                <div>
                    <span style="color:#8899aa;">Cuota justa</span><br>
                    <strong>${fmt(v.cuota_justa)}</strong>
                </div>
                ${tieneCuota ? `
                <div>
                    <span style="color:#8899aa;">Cuota casa</span><br>
                    <strong style="color:#ffaa00;">${fmt(v.cuota)}</strong>
                </div>` : ''}
                ${v.edge_ajustado !== undefined ? `
                <div>
                    <span style="color:#8899aa;">Edge ajustado</span><br>
                    <strong style="color:${v.edge_ajustado > 2 ? '#00ff88' : (v.edge_ajustado > 0 ? '#ffaa00' : '#ff4455')};">${v.edge_ajustado > 0 ? '+' : ''}${fmt(v.edge_ajustado)}%</strong>
                </div>` : ''}
                ${v.ev_min !== undefined ? `
                <div>
                    <span style="color:#8899aa;">EV min / max</span><br>
                    <strong style="font-size:0.9em;"><span style="color:${v.ev_min > 0 ? '#00ff88' : '#ff4455'};">${fmt(v.ev_min)}%</span> / <span style="color:${v.ev_max > 0 ? '#00ff88' : '#ff4455'};">${fmt(v.ev_max)}%</span></strong>
                </div>` : ''}
            </div>
            ${v.razon ? `<p style="color:#8899aa;font-size:0.75em;margin-top:6px;">${v.razon}</p>` : ''}
            ${kellyHtml}
        </div>`;
    }

    // Resumen de value bets
    const valueBets = filtrados.filter(v => v.decision === 'VALUE_FUERTE' || v.decision === 'VALUE');
    const noBets = filtrados.filter(v => v.decision === 'NO_BET');

    let resumenHtml = '';
    if (valueBets.length > 0 || noBets.length > 0) {
        resumenHtml = `
        <div style="margin-top:15px;padding-top:12px;border-top:1px solid #1a2a3a;">
            <p style="color:#8899aa;font-size:0.85em;">
                📊 Resumen: 
                <strong style="color:#00ff88;">${valueBets.length} value bets</strong> · 
                <strong style="color:#ff4455;">${noBets.length} no-bets</strong>
            </p>
        </div>`;
    }

    return `
    <div class="result-card" style="border-left-color:#00ff88;">
        <div class="market" style="color:#00ff88;">💰 VALOR ESPERADO (EV) + KELLY</div>
        <p style="color:#8899aa;font-size:0.8em;margin-top:5px;">
            Ordenado por EV. El <strong>stake sugerido</strong> se calcula con Kelly ${fraccionLabel} sobre un bankroll de <strong style="color:#00d4ff;">${kellyConfig.bankroll.toLocaleString()} COP</strong>.
        </p>
        <div style="margin-top:15px;">${filas}</div>
        ${resumenHtml}
    </div>`;
}
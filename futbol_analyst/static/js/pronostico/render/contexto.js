// ============================================================
// static/js/pronostico/render/contexto.js
// Secciones: Contexto (λ, cómo se calculó, tendencias, H2H, top),
// Distribuciones y Anomalías.
// ============================================================

function mostrarSeccionContexto(data) {
    let html = '';

    html += `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #1a2a3a;">
        <h3 style="color:#00d4ff; margin-bottom:10px;">🎯 GOLES ESPERADOS (λ Poisson)</h3>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:15px; text-align:center;">
            <div>
                <div style="color:#00d4ff; font-weight:700;">${data.local}</div>
                <div style="font-size:2em; color:#00d4ff; font-weight:700;">${data.lambdas.local}</div>
            </div>
            <div>
                <div style="color:#8899aa; font-size:0.8em;">TOTAL</div>
                <div style="font-size:2em; color:#ffffff; font-weight:700;">${data.lambdas.total_esperado}</div>
            </div>
            <div>
                <div style="color:#ff8844; font-weight:700;">${data.visitante}</div>
                <div style="font-size:2em; color:#ff8844; font-weight:700;">${data.lambdas.visitante}</div>
            </div>
        </div>
    </div>`;

    const eqLocalM = data.estadisticas_equipo.local;
    const eqVisitM = data.estadisticas_equipo.visitante;

    html += `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #00d4ff44;">
        <h3 style="color:#00d4ff; margin-bottom:5px;">🧠 CÓMO SE CALCULÓ</h3>
        <p style="color:#8899aa; font-size:0.8em; margin-bottom:15px;">
            El modelo usa ATAQUE vs DEFENSA con suavizado (k=${eqLocalM.factor_suavizado_k || 5.0}) y ponderación por fuerza del rival.
        </p>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div style="background:#0a121c; padding:12px; border-radius:8px; border:1px solid #00d4ff44;">
                <p style="color:#00d4ff; font-weight:700; margin-bottom:10px;">🏠 ${data.local}</p>
                <table style="width:100%; font-size:0.85em; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:4px 0;">Ataque crudo</td>
                        <td style="text-align:right; color:#8899aa;">
                            ${fmt(eqLocalM.ataque_crudo)} goles/partido
                            ${eqLocalM.ataque_fuente === 'fallback_sin_datos' 
                                ? '<span style="color:#ff4455; font-size:0.7em; margin-left:4px;">⚠️ sin datos</span>' 
                                : ''}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Ataque suavizado</td><td style="text-align:right; color:#00ff88; font-weight:700;">${fmt(eqLocalM.ataque_suavizado)}</td></tr>
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:4px 0;">Defensa rival (crudo)</td>
                        <td style="text-align:right; color:#8899aa;">
                            ${fmt(eqLocalM.defensa_cruda)} goles recibidos
                            ${eqLocalM.defensa_fuente === 'fallback_sin_datos' 
                                ? '<span style="color:#ff4455; font-size:0.7em; margin-left:4px;">⚠️ sin datos</span>' 
                                : eqLocalM.defensa_fuente === 'observado_cero'
                                ? '<span style="color:#00ff88; font-size:0.7em; margin-left:4px;">✅ clean sheets</span>'
                                : ''}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Defensa rival (suav.)</td><td style="text-align:right; color:#00ff88; font-weight:700;">${fmt(eqLocalM.defensa_suavizada)}</td></tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Factor localía</td><td style="text-align:right; color:#ffaa00;">×${fmt(eqLocalM.factor_localia)}</td></tr>
                    ${eqLocalM.localia_liga && eqLocalM.localia_liga.fuente === 'empirico' ? `
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0; font-size:0.9em; color:#8899aa;">↳ Localía de liga</td><td style="text-align:right; color:#00d4ff; font-size:0.9em;">×${fmt(eqLocalM.localia_liga.factor)} <span style="color:#8899aa;">(${eqLocalM.localia_liga.partidos} part.)</span></td></tr>
                    ` : ''}
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Factor racha</td><td style="text-align:right; color:${(data.rachas?.local?.factor || 1) > 1 ? '#00ff88' : ((data.rachas?.local?.factor || 1) < 1 ? '#ff4455' : '#8899aa')};">×${(data.rachas?.local?.factor || 1).toFixed(3)}</td></tr>
                    <tr><td style="padding:4px 0;">λ (goles esperados)</td><td style="text-align:right; color:#ff8844; font-weight:700; font-size:1.1em;">${fmt(data.lambdas.local)}</td></tr>
                </table>
                <!-- ========== FEATURES AVANZADAS (FE-1/FE-2) ========== -->
                <div style="margin-top:10px; padding-top:8px; border-top:1px dashed #1a2a3a;">
                    <p style="color:#8899aa; font-size:0.75em; margin-bottom:6px;">🔬 Features avanzadas</p>
                    <table style="width:100%; font-size:0.8em; border-collapse:collapse;">
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Ratio ataque/defensa</td>
                            <td style="text-align:right; color:#ff8844;">${fmt(eqVisitM.ratio_valor)} <span style="color:${(eqVisitM.factor_ratio || 1) > 1 ? '#00ff88' : ((eqVisitM.factor_ratio || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqVisitM.factor_ratio, 3)})</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Diferencial goles</td>
                            <td style="text-align:right; color:#ff8844;">${eqVisitM.diferencial_valor !== null && eqVisitM.diferencial_valor !== undefined ? (eqVisitM.diferencial_valor > 0 ? '+' : '') + fmt(eqVisitM.diferencial_valor) : '—'} <span style="color:${(eqVisitM.factor_diferencial || 1) > 1 ? '#00ff88' : ((eqVisitM.factor_diferencial || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqVisitM.factor_diferencial, 3)})</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Racha (últ. 3)</td>
                            <td style="text-align:right; color:#ff8844;">${eqVisitM.racha_v2_tipo || '—'} <span style="color:${(eqVisitM.factor_racha_v2 || 1) > 1 ? '#00ff88' : ((eqVisitM.factor_racha_v2 || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqVisitM.factor_racha_v2, 3)})</span></td>
                        </tr>
                        ${eqVisitM.contexto ? `
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Clean Sheets %</td>
                            <td style="text-align:right; color:#00ff88;">${eqVisitM.contexto.clean_sheets_pct !== null ? eqVisitM.contexto.clean_sheets_pct + '%' : '—'}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Failed to Score %</td>
                            <td style="text-align:right; color:#ff8844;">${eqVisitM.contexto.failed_to_score_pct !== null ? eqVisitM.contexto.failed_to_score_pct + '%' : '—'}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">CV Goles</td>
                            <td style="text-align:right; color:${colorPorCV(eqVisitM.contexto.cv_goles)};">${fmt(eqVisitM.contexto.cv_goles)}</td>
                        </tr>
                        <tr>
                            <td style="padding:3px 0; color:#8899aa;">Fiabilidad</td>
                            <td style="text-align:right; color:${eqVisitM.contexto.interpretacion.fiabilidad === 'alta' ? '#00ff88' : (eqVisitM.contexto.interpretacion.fiabilidad === 'media' ? '#ffaa00' : '#ff4455')};">${eqVisitM.contexto.interpretacion.fiabilidad}</td>
                        </tr>
                        ` : ''}
                    </table>
                </div>
                ${data.rachas?.local?.tipo && data.rachas.local.tipo !== 'normal' && data.rachas.local.tipo !== 'sin_datos' ? `<p style="color:#ffaa00; font-size:0.8em; margin-top:8px; text-align:center;">${data.rachas.local.descripcion}</p>` : ''}
            </div>
            
            <div style="background:#0a121c; padding:12px; border-radius:8px; border:1px solid #ff884444;">
                <p style="color:#ff8844; font-weight:700; margin-bottom:10px;">✈️ ${data.visitante}</p>
                <table style="width:100%; font-size:0.85em; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:4px 0;">Ataque crudo</td>
                        <td style="text-align:right; color:#8899aa;">
                            ${fmt(eqVisitM.ataque_crudo)} goles/partido
                            ${eqVisitM.ataque_fuente === 'fallback_sin_datos' 
                                ? '<span style="color:#ff4455; font-size:0.7em; margin-left:4px;">⚠️ sin datos</span>' 
                                : ''}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Ataque suavizado</td><td style="text-align:right; color:#00ff88; font-weight:700;">${fmt(eqVisitM.ataque_suavizado)}</td></tr>
                    <tr style="border-bottom:1px solid #1a2a3a;">
                        <td style="padding:4px 0;">Defensa rival (crudo)</td>
                        <td style="text-align:right; color:#8899aa;">
                            ${fmt(eqVisitM.defensa_cruda)} goles recibidos
                            ${eqVisitM.defensa_fuente === 'fallback_sin_datos' 
                                ? '<span style="color:#ff4455; font-size:0.7em; margin-left:4px;">⚠️ sin datos</span>' 
                                : eqVisitM.defensa_fuente === 'observado_cero'
                                ? '<span style="color:#00ff88; font-size:0.7em; margin-left:4px;">✅ clean sheets</span>'
                                : ''}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Defensa rival (suav.)</td><td style="text-align:right; color:#00ff88; font-weight:700;">${fmt(eqVisitM.defensa_suavizada)}</td></tr>
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Factor localía</td><td style="text-align:right; color:#ffaa00;">×${fmt(eqVisitM.factor_localia)}</td></tr>
                    ${eqVisitM.localia_liga && eqVisitM.localia_liga.fuente === 'empirico' ? `
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0; font-size:0.9em; color:#8899aa;">↳ Localía de liga</td><td style="text-align:right; color:#00d4ff; font-size:0.9em;">×${fmt(eqVisitM.localia_liga.factor)} <span style="color:#8899aa;">(${eqVisitM.localia_liga.partidos} part.)</span></td></tr>
                    ` : ''}
                    <tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">Factor racha</td><td style="text-align:right; color:${(data.rachas?.visitante?.factor || 1) > 1 ? '#00ff88' : ((data.rachas?.visitante?.factor || 1) < 1 ? '#ff4455' : '#8899aa')};">×${(data.rachas?.visitante?.factor || 1).toFixed(3)}</td></tr>
                    <tr><td style="padding:4px 0;">λ (goles esperados)</td><td style="text-align:right; color:#00d4ff; font-weight:700; font-size:1.1em;">${fmt(data.lambdas.visitante)}</td></tr>
                </table>
                <!-- ========== FEATURES AVANZADAS (FE-1/FE-2) ========== -->
                <div style="margin-top:10px; padding-top:8px; border-top:1px dashed #1a2a3a;">
                    <p style="color:#8899aa; font-size:0.75em; margin-bottom:6px;">🔬 Features avanzadas</p>
                    <table style="width:100%; font-size:0.8em; border-collapse:collapse;">
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Ratio ataque/defensa</td>
                            <td style="text-align:right; color:#00d4ff;">${fmt(eqLocalM.ratio_valor)} <span style="color:${(eqLocalM.factor_ratio || 1) > 1 ? '#00ff88' : ((eqLocalM.factor_ratio || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqLocalM.factor_ratio, 3)})</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Diferencial goles</td>
                            <td style="text-align:right; color:#00d4ff;">${eqLocalM.diferencial_valor !== null && eqLocalM.diferencial_valor !== undefined ? (eqLocalM.diferencial_valor > 0 ? '+' : '') + fmt(eqLocalM.diferencial_valor) : '—'} <span style="color:${(eqLocalM.factor_diferencial || 1) > 1 ? '#00ff88' : ((eqLocalM.factor_diferencial || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqLocalM.factor_diferencial, 3)})</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Racha (últ. 3)</td>
                            <td style="text-align:right; color:#00d4ff;">${eqLocalM.racha_v2_tipo || '—'} <span style="color:${(eqLocalM.factor_racha_v2 || 1) > 1 ? '#00ff88' : ((eqLocalM.factor_racha_v2 || 1) < 1 ? '#ff4455' : '#8899aa')};">(×${fmt(eqLocalM.factor_racha_v2, 3)})</span></td>
                        </tr>
                        ${eqLocalM.contexto ? `
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Clean Sheets %</td>
                            <td style="text-align:right; color:#00ff88;">${eqLocalM.contexto.clean_sheets_pct !== null ? eqLocalM.contexto.clean_sheets_pct + '%' : '—'}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">Failed to Score %</td>
                            <td style="text-align:right; color:#ff8844;">${eqLocalM.contexto.failed_to_score_pct !== null ? eqLocalM.contexto.failed_to_score_pct + '%' : '—'}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #1a2a3a;">
                            <td style="padding:3px 0; color:#8899aa;">CV Goles</td>
                            <td style="text-align:right; color:${colorPorCV(eqLocalM.contexto.cv_goles)};">${fmt(eqLocalM.contexto.cv_goles)}</td>
                        </tr>
                        <tr>
                            <td style="padding:3px 0; color:#8899aa;">Fiabilidad</td>
                            <td style="text-align:right; color:${eqLocalM.contexto.interpretacion.fiabilidad === 'alta' ? '#00ff88' : (eqLocalM.contexto.interpretacion.fiabilidad === 'media' ? '#ffaa00' : '#ff4455')};">${eqLocalM.contexto.interpretacion.fiabilidad}</td>
                        </tr>
                        ` : ''}
                    </table>
                </div>
                ${data.rachas?.visitante?.tipo && data.rachas.visitante.tipo !== 'normal' && data.rachas.visitante.tipo !== 'sin_datos' ? `<p style="color:#ffaa00; font-size:0.8em; margin-top:8px; text-align:center;">${data.rachas.visitante.descripcion}</p>` : ''}
            </div>
        </div>
        
        <div style="margin-top:12px; padding:10px; background:#0a121c; border-radius:6px; border:1px solid #1a2a3a; text-align:center;">
            <span style="color:#8899aa; font-size:0.85em;">
                Promedio de liga: <strong style="color:#e0e0e0;">${fmt(eqLocalM.promedio_liga)} goles</strong>
                ${eqLocalM.promedio_liga_fuente === 'observado' 
                    ? `<span style="color:#00ff88; font-size:0.75em;">(observado · ${eqLocalM.promedio_liga_partidos || 0} part.)</span>` 
                    : eqLocalM.promedio_liga_fuente === 'estimado'
                    ? `<span style="color:#ffaa00; font-size:0.75em;">(estimado · ${eqLocalM.promedio_liga_partidos || 0} part.)</span>`
                    : `<span style="color:#ff4455; font-size:0.75em;">(fallback · sin datos)</span>`}
                · Fórmula: <strong style="color:#00d4ff;">λ = (ataque_suav × defensa_suav) / prom_liga × localía</strong>
            </span>
        </div>
    </div>`;

    const tLocal = data.tendencias.local;
    const tVisit = data.tendencias.visitante;
    html += `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #1a2a3a;">
        <h3 style="color:#00d4ff; margin-bottom:10px;">📊 TENDENCIAS</h3>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div>
                <div style="color:#00d4ff; font-weight:700;">${data.local}</div>
                <div style="font-size:1.1em;">${tLocal.descripcion || 'Sin datos'}</div>
            </div>
            <div>
                <div style="color:#ff8844; font-weight:700;">${data.visitante}</div>
                <div style="font-size:1.1em;">${tVisit.descripcion || 'Sin datos'}</div>
            </div>
        </div>
    </div>`;

    if (data.h2h && data.h2h.total > 0) {
        html += `
        <div class="result-card" style="border-left-color:#ffaa00;">
            <div class="market" style="color:#ffaa00;">⚔️ H2H - Últimos ${data.h2h.total} enfrentamientos</div>
            <div style="margin-top:10px;">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;text-align:center;">
                    <div><span style="color:#00d4ff;font-weight:700;">${data.local}</span><br><strong>${data.h2h.victorias_equipo1}</strong> victorias</div>
                    <div><span style="color:#8899aa;">Empates</span><br><strong>${data.h2h.empates}</strong></div>
                    <div><span style="color:#ff8844;font-weight:700;">${data.visitante}</span><br><strong>${data.h2h.victorias_equipo2}</strong> victorias</div>
                </div>
            </div>
        </div>`;
    }

    if (data.mercados && data.mercados.top_marcadores) {
        html += `<div class="result-card"><div class="market">🎲 TOP 5 MARCADORES MÁS PROBABLES</div><div style="margin-top:10px;">`;
        for (const m of data.mercados.top_marcadores.slice(0, 5)) {
            html += `
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1a2a3a;font-size:0.9em;">
                <span>${m.marcador}</span>
                <strong>${(m.probabilidad * 100).toFixed(2)}%</strong>
            </div>`;
        }
        html += `</div></div>`;
    }

    return html;
}

function mostrarSeccionDistribuciones(data) {
    const distL = data.distribuciones?.local;
    const distV = data.distribuciones?.visitante;
    if (!distL || !distV) return '';

    const metricas = [
        { key: 'goles', label: '⚽ Goles' },
        { key: 'tiros', label: '🎯 Tiros' },
        { key: 'tiros_puerta', label: '🎯 T.Puerta' },
        { key: 'corners', label: '🚩 Córners' },
        { key: 'faltas', label: '⚔️ Faltas' },
        { key: 'tarjetas_amarillas', label: '🟨 Amarillas' },
    ];

    let html = `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #ffaa0044;">
        <h3 style="color:#ffaa00; margin-bottom:5px;">📊 DISTRIBUCIONES Y VARIABILIDAD</h3>
        <p style="color:#8899aa; font-size:0.8em; margin-bottom:15px;">CV bajo (🟢) = regular · CV medio (🟡) = normal · CV alto (🔴) = irregular</p>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
            <div style="background:#0a121c; padding:12px; border-radius:8px; border:1px solid #00d4ff44;">
                <p style="color:#00d4ff; font-weight:700; margin-bottom:10px;">🏠 ${data.local} (${distL.partidos} partidos)</p>
                <table style="width:100%; font-size:0.8em; border-collapse:collapse;">
                    <thead><tr style="color:#8899aa; border-bottom:1px solid #1a2a3a;"><th style="text-align:left;">Métrica</th><th>Media</th><th>Mediana</th><th>CV</th><th>Rango</th></tr></thead>
                    <tbody>`;

    for (const m of metricas) {
        const met = distL.metricas?.[m.key];
        if (!met || met.n === 0) continue;
        html += `<tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">${m.label}</td><td style="text-align:center;font-weight:700;">${fmt(met.media)}</td><td style="text-align:center;color:#8899aa;">${fmt(met.mediana)}</td><td style="text-align:center;color:${colorPorCV(met.cv)};font-weight:700;">${fmt(met.cv)}</td><td style="text-align:center;color:#8899aa;">${fmt(met.min, 1)}-${fmt(met.max, 1)}</td></tr>`;
    }

    html += `</tbody></table></div>
            <div style="background:#0a121c; padding:12px; border-radius:8px; border:1px solid #ff884444;">
                <p style="color:#ff8844; font-weight:700; margin-bottom:10px;">✈️ ${data.visitante} (${distV.partidos} partidos)</p>
                <table style="width:100%; font-size:0.8em; border-collapse:collapse;">
                    <thead><tr style="color:#8899aa; border-bottom:1px solid #1a2a3a;"><th style="text-align:left;">Métrica</th><th>Media</th><th>Mediana</th><th>CV</th><th>Rango</th></tr></thead>
                    <tbody>`;

    for (const m of metricas) {
        const met = distV.metricas?.[m.key];
        if (!met || met.n === 0) continue;
        html += `<tr style="border-bottom:1px solid #1a2a3a;"><td style="padding:4px 0;">${m.label}</td><td style="text-align:center;font-weight:700;">${fmt(met.media)}</td><td style="text-align:center;color:#8899aa;">${fmt(met.mediana)}</td><td style="text-align:center;color:${colorPorCV(met.cv)};font-weight:700;">${fmt(met.cv)}</td><td style="text-align:center;color:#8899aa;">${fmt(met.min, 1)}-${fmt(met.max, 1)}</td></tr>`;
    }

    html += `</tbody></table></div></div></div>`;
    return html;
}

function mostrarSeccionAnomalias(data) {
    const anom = data.anomalias;
    if (!anom) return '';

    let html = `<div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #ff445544;">`;
    html += `<h3 style="color:#ff4455; margin-bottom:10px;">⚠️ ANOMALÍAS</h3>`;

    if (anom.nivel_global === 'pocos_datos') {
        html += `<p style="color:#ffaa00; font-size:0.9em;">${anom.mensaje || 'Pocos datos para detectar anomalías'}</p>`;
    } else if (!anom.anomalias || anom.anomalias.length === 0) {
        html += `<p style="color:#00ff88; font-size:0.9em;">✅ Sin anomalías detectadas. Modelo y datos históricos coinciden.</p>`;
    } else {
        for (const a of anom.anomalias) {
            const color = a.nivel === 'alto' ? '#ff4455' : '#ffaa00';
            html += `
            <div style="background:#0a121c; padding:10px; border-radius:6px; margin-bottom:8px; border-left:3px solid ${color};">
                <div style="color:${color}; font-weight:700; font-size:0.9em;">${a.mercado}</div>
                <div style="margin-top:6px; font-size:0.85em; color:#8899aa;">
                    Modelo: <strong>${(a.poisson * 100).toFixed(0)}%</strong> · Histórico: <strong>${(a.historico * 100).toFixed(0)}%</strong>
                </div>
            </div>`;
        }
    }

    html += `</div>`;
    return html;
}
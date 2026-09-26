// ============================================================
// static/js/backtesting/metricas.js
// Carga y renderiza métricas generales + calibración + tablas.
// ============================================================

async function cargarBacktesting() {
    try {
        const [metricas, calib, porMotor, porLiga, porConfianza, porMercado, maeRmse] = await Promise.all([
            fetch('/api/backtesting/metricas').then(r => r.json()),
            fetch('/api/backtesting/calibracion').then(r => r.json()),
            fetch('/api/backtesting/por-motor').then(r => r.json()),
            fetch('/api/backtesting/por-liga').then(r => r.json()),
            fetch('/api/backtesting/por-confianza').then(r => r.json()),
            fetch('/api/backtesting/por-mercado').then(r => r.json()),
            fetch('/api/backtesting/mae-rmse').then(r => r.json())
        ]);

        renderMetricas(metricas);
        renderCalibracion(calib);
        renderPorMotor(porMotor);
        renderPorLiga(porLiga);
        renderPorConfianza(porConfianza);
        renderPorMercado(porMercado);
        renderMaeRmse(maeRmse);

    } catch (e) {
        console.error('Error backtesting:', e);
    }
}

// ============================================================
// MAE / RMSE DE GOLES (FASE 10.5)
// ============================================================
function renderMaeRmse(data) {
    const container = document.getElementById('tablaMaeRmse');
    if (!container) return;

    if (!data || !data.global || data.global.total === 0) {
        container.innerHTML = `<p style="color:#8899aa;">${data?.mensaje || 'No hay datos de λ todavía.'}</p>`;
        return;
    }

    const g = data.global;
    const interp = g.interpretacion || { nivel: 'sin_datos', color: '#8899aa' };

    let html = `
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-bottom:15px;">
        <div class="stat-item">
            <span class="label">Partidos evaluados</span><br>
            <span class="value" style="font-size:1.3em;">${g.total}</span>
        </div>
        <div class="stat-item">
            <span class="label">MAE Local</span><br>
            <span class="value" style="font-size:1.3em;color:${interp.color};">${g.mae_local !== null ? g.mae_local.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">MAE Visitante</span><br>
            <span class="value" style="font-size:1.3em;color:${interp.color};">${g.mae_visitante !== null ? g.mae_visitante.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">MAE Total</span><br>
            <span class="value" style="font-size:1.3em;color:${interp.color};">${g.mae_total !== null ? g.mae_total.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">RMSE Local</span><br>
            <span class="value" style="font-size:1.3em;">${g.rmse_local !== null ? g.rmse_local.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">RMSE Visitante</span><br>
            <span class="value" style="font-size:1.3em;">${g.rmse_visitante !== null ? g.rmse_visitante.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">RMSE Total</span><br>
            <span class="value" style="font-size:1.3em;">${g.rmse_total !== null ? g.rmse_total.toFixed(3) : '—'}</span>
        </div>
        <div class="stat-item">
            <span class="label">Sesgo Local</span><br>
            <span class="value" style="font-size:1.3em;color:${g.sesgo_local > 0 ? '#ffaa00' : (g.sesgo_local < 0 ? '#ff8844' : '#8899aa')};">${g.sesgo_local !== null ? (g.sesgo_local > 0 ? '+' : '') + g.sesgo_local.toFixed(3) : '—'}</span>
            <div style="font-size:0.65em;color:#8899aa;">${g.sesgo_local > 0.1 ? 'Sobreestima' : (g.sesgo_local < -0.1 ? 'Subestima' : 'Neutro')}</div>
        </div>
        <div class="stat-item">
            <span class="label">Sesgo Visitante</span><br>
            <span class="value" style="font-size:1.3em;color:${g.sesgo_visitante > 0 ? '#ffaa00' : (g.sesgo_visitante < 0 ? '#ff8844' : '#8899aa')};">${g.sesgo_visitante !== null ? (g.sesgo_visitante > 0 ? '+' : '') + g.sesgo_visitante.toFixed(3) : '—'}</span>
            <div style="font-size:0.65em;color:#8899aa;">${g.sesgo_visitante > 0.1 ? 'Sobreestima' : (g.sesgo_visitante < -0.1 ? 'Subestima' : 'Neutro')}</div>
        </div>
    </div>
    <div style="margin-bottom:15px; padding:10px; background:#0a121c; border-radius:6px; border:1px solid ${interp.color}44;">
        <span style="color:${interp.color}; font-weight:700;">Interpretación: ${interp.nivel.toUpperCase()}</span>
        <span style="color:#8899aa; font-size:0.85em; margin-left:10px;">
            MAE < 0.5 = excelente · MAE < 0.7 = bueno · MAE < 0.9 = aceptable
        </span>
    </div>
    `;

    // ========== Por liga ==========
    if (data.por_liga && data.por_liga.length > 0) {
        html += `
        <h5 style="color:#00d4ff; margin-bottom:10px; font-size:0.95em;">📊 Desglose por liga</h5>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
                <thead>
                    <tr style="background:#0a121c;color:#8899aa;">
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Liga</th>
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Partidos</th>
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">MAE Local</th>
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">MAE Visit.</th>
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">MAE Total</th>
                        <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">RMSE Total</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const l of data.por_liga) {
            const color = l.mae_total < 0.6 ? '#00ff88' : (l.mae_total < 0.8 ? '#ffaa00' : '#ff4455');
            html += `
                <tr>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;">${l.liga}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:#8899aa;">${l.total}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.mae_local.toFixed(3)}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.mae_visitante.toFixed(3)}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:${color};font-weight:700;">${l.mae_total.toFixed(3)}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.rmse_total.toFixed(3)}</td>
                </tr>
            `;
        }

        html += `</tbody></table></div>`;
    }

    container.innerHTML = html;
}

function renderMetricas(m) {
    const container = document.getElementById('metricasGenerales');

    if (!m || m.total_pronosticos === 0) {
        container.innerHTML = '<p style="color:#8899aa;">Aún no hay pronósticos guardados.</p>';
        return;
    }

    const roiClass = m.roi > 0 ? 'ev-positive' : (m.roi < 0 ? 'ev-negative' : 'ev-neutral');

    container.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;">
        <div class="stat-item">
            <span class="label">Total</span><br>
            <span class="value" style="font-size:1.4em;">${m.total_pronosticos}</span>
        </div>
        <div class="stat-item">
            <span class="label">Cerrados</span><br>
            <span class="value" style="font-size:1.4em;">${m.cerrados}</span>
        </div>
        <div class="stat-item">
            <span class="label">Abiertos</span><br>
            <span class="value" style="font-size:1.4em;">${m.abiertos}</span>
        </div>
        <div class="stat-item">
            <span class="label">Vinculados</span><br>
            <span class="value" style="font-size:1.4em;">${m.vinculados}</span>
        </div>
        <div class="stat-item">
            <span class="label">Acierto 1X2</span><br>
            <span class="value" style="font-size:1.4em;color:#00ff88;">${m.tasa_acierto_1x2 || 0}%</span>
            <div style="font-size:0.7em;color:#8899aa;">${m.aciertos_1x2 || 0}/${m.cerrados}</div>
        </div>
        <div class="stat-item">
            <span class="label">Acierto BTTS</span><br>
            <span class="value" style="font-size:1.4em;color:#00ff88;">${m.tasa_acierto_btts || 0}%</span>
            <div style="font-size:0.7em;color:#8899aa;">${m.aciertos_btts || 0}/${m.cerrados}</div>
        </div>
        <div class="stat-item">
            <span class="label">Acierto O2.5</span><br>
            <span class="value" style="font-size:1.4em;color:#00ff88;">${m.tasa_acierto_over25 || 0}%</span>
            <div style="font-size:0.7em;color:#8899aa;">${m.aciertos_over25 || 0}/${m.cerrados}</div>
        </div>
        <div class="stat-item">
            <span class="label">Apuestas EV+</span><br>
            <span class="value" style="font-size:1.4em;">${m.total_apuestas_ev_positivo || 0}</span>
        </div>
        <div class="stat-item">
            <span class="label">ROI</span><br>
            <span class="value ${roiClass}" style="font-size:1.4em;">${m.roi || 0}%</span>
            <div style="font-size:0.7em;color:#8899aa;">${m.ganancia_total || 0}u</div>
        </div>
    </div>
`;
}

function renderCalibracion(c) {
    const container = document.getElementById('tablaCalibracion');

    if (!c || !c.rangos || c.rangos.length === 0) {
        container.innerHTML = `<p style="color:#8899aa;">${c?.mensaje || 'Datos insuficientes para calibrar (mínimo 3 cerrados)'}</p>`;
        return;
    }

    let html = `
    <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
        <thead>
            <tr style="background:#0a121c;color:#8899aa;">
                <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Rango</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Predicho</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Real</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Diferencia</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Muestras</th>
            </tr>
        </thead>
        <tbody>
`;

    for (const r of c.rangos) {
        const difClass = Math.abs(r.diferencia) < 5 ? 'ev-positive' :
            (Math.abs(r.diferencia) < 10 ? 'ev-neutral' : 'ev-negative');
        html += `
        <tr>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">${r.rango}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${r.predicho_promedio}%</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${r.real}%</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;" class="${difClass}">
                ${r.diferencia > 0 ? '+' : ''}${r.diferencia}%
            </td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${r.muestras}</td>
        </tr>
    `;
    }

    html += `</tbody></table>
    <p style="color:#8899aa;font-size:0.8em;margin-top:10px;">
        Total de muestras: ${c.total_muestras}. 
        Una buena calibración tiene diferencias menores a ±5%.
    </p>
`;

    container.innerHTML = html;
}

function renderPorMotor(lista) {
    const container = document.getElementById('tablaPorMotor');

    if (!lista || lista.length === 0) {
        container.innerHTML = '<p style="color:#8899aa;">Sin datos</p>';
        return;
    }

    let html = `
    <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
        <thead>
            <tr style="background:#0a121c;color:#8899aa;">
                <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Motor</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Total</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Cerrados</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Aciertos</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Tasa</th>
            </tr>
        </thead>
        <tbody>
`;

    for (const m of lista) {
        html += `
        <tr>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">${m.motor}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${m.total}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${m.cerrados}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${m.aciertos}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:#00ff88;">${m.tasa}%</td>
        </tr>
    `;
    }

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderPorLiga(lista) {
    const container = document.getElementById('tablaPorLiga');

    if (!lista || lista.length === 0) {
        container.innerHTML = '<p style="color:#8899aa;">Sin datos por liga</p>';
        return;
    }

    let html = `
    <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
        <thead>
            <tr style="background:#0a121c;color:#8899aa;">
                <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Liga</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Total</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Cerrados</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Aciertos</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Tasa</th>
            </tr>
        </thead>
        <tbody>
`;

    for (const l of lista) {
        html += `
        <tr>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">${l.liga}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.total}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.cerrados}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${l.aciertos}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:#00ff88;">${l.tasa}%</td>
        </tr>
    `;
    }

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderPorConfianza(lista) {
    const container = document.getElementById('tablaPorConfianza');

    if (!lista || lista.length === 0) {
        container.innerHTML = '<p style="color:#8899aa;">Sin datos por confianza</p>';
        return;
    }

    let html = `
    <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
        <thead>
            <tr style="background:#0a121c;color:#8899aa;">
                <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Nivel</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Total</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Aciertos</th>
                <th style="padding:8px;border:1px solid #1a2a3a;">Tasa</th>
            </tr>
        </thead>
        <tbody>
`;

    for (const c of lista) {
        const color = c.nivel === 'alta' ? '#00ff88' : (c.nivel === 'media' ? '#ffaa00' : '#ff4455');
        html += `
        <tr>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;color:${color};">${c.nivel.toUpperCase()}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${c.total}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${c.aciertos}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:${color};">${c.tasa}%</td>
        </tr>
    `;
    }

    html += `</tbody></table>`;
    container.innerHTML = html;
}

// ============================================================
// RENDIMIENTO POR MERCADO
// ============================================================
function renderPorMercado(data) {
    const container = document.getElementById('tablaPorMercado');
    if (!container) return;

    if (!data || !data.mercados || data.mercados.length === 0) {
        const msg = data?.mensaje || 'No hay pronósticos cerrados con JSON de mercados. Cierra algunos pronósticos o vincula al histórico.';
        container.innerHTML = `<p style="color:#8899aa;">${msg}</p>`;
        return;
    }

    // Agrupar por categoría
    const categorias = {
        'goles': { titulo: '⚽ GOLES', color: '#00d4ff', mercados: [] },
        'corners': { titulo: '🚩 CÓRNERS', color: '#00ff88', mercados: [] },
        'tarjetas': { titulo: '🟨 TARJETAS', color: '#ffaa00', mercados: [] },
    };

    for (const m of data.mercados) {
        if (categorias[m.categoria]) {
            categorias[m.categoria].mercados.push(m);
        }
    }

    // Color según tasa de acierto
    const colorTasa = (tasa) => {
        if (tasa === null || tasa === undefined) return '#8899aa';
        if (tasa >= 60) return '#00ff88';
        if (tasa >= 50) return '#ffaa00';
        return '#ff4455';
    };

    // Color según Brier (menor = mejor)
    const colorBrier = (brier) => {
        if (brier === null || brier === undefined) return '#8899aa';
        if (brier < 0.20) return '#00ff88';
        if (brier < 0.25) return '#ffaa00';
        return '#ff4455';
    };

    // Color según ROI
    const colorRoi = (roi) => {
        if (roi === null || roi === undefined) return '#8899aa';
        if (roi > 5) return '#00ff88';
        if (roi > 0) return '#ffaa00';
        return '#ff4455';
    };

    let html = `
    <div style="margin-bottom:12px; padding:8px 12px; background:#0a121c; border-radius:6px; border:1px solid #1a2a3a;">
        <span style="color:#8899aa; font-size:0.85em;">
            Evaluados sobre <strong style="color:#00d4ff;">${data.total_pronosticos}</strong> pronósticos cerrados con JSON de mercados.
            <strong style="color:#00d4ff;">${data.total_mercados_evaluados}</strong> mercados evaluados.
        </span>
    </div>
    `;

    for (const [key, cat] of Object.entries(categorias)) {
        if (cat.mercados.length === 0) continue;

        html += `
        <div style="margin-bottom:20px;">
            <h5 style="color:${cat.color}; margin-bottom:8px; font-size:0.95em;">${cat.titulo}</h5>
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
                    <thead>
                        <tr style="background:#0a121c;color:#8899aa;">
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:left;">Mercado</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Total</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Aciertos</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Tasa</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Brier</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">ROI</th>
                            <th style="padding:8px;border:1px solid #1a2a3a;text-align:center;">Apuestas</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const m of cat.mercados) {
            const tasaColor = colorTasa(m.tasa);
            const brierColor = colorBrier(m.brier);
            const roiColor = colorRoi(m.roi);

            const roiStr = m.roi !== null && m.roi !== undefined
                ? `${m.roi > 0 ? '+' : ''}${m.roi.toFixed(2)}%`
                : '—';

            const brierStr = m.brier !== null && m.brier !== undefined
                ? m.brier.toFixed(4)
                : '—';

            html += `
                <tr>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;font-weight:600;">${m.mercado}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:#8899aa;">${m.total}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${m.aciertos}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:${tasaColor};font-weight:700;">${m.tasa.toFixed(1)}%</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:${brierColor};">${brierStr}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:${roiColor};font-weight:700;">${roiStr}</td>
                    <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;color:#8899aa;">${m.apuestas || 0}</td>
                </tr>
            `;
        }

        html += `
                    </tbody>
                </table>
            </div>
        </div>
        `;
    }

    container.innerHTML = html;
}
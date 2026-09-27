// ============================================================
// static/js/pronostico/render/jugadores.js
// Secciones: Jugadores (completa + por tipo).
// ============================================================

function mostrarSeccionJugadores(data) {
    if (!data.jugadores) return '';

    const jl = data.jugadores.local;
    const jv = data.jugadores.visitante;

    const renderJugador = (j, tipo) => {
        if (!j || !j.eventos) return '';
        let probsHtml = '';

        if (tipo === 'goleador' && j.eventos.goles) {
            const g = j.eventos.goles;
            probsHtml = `<div style="display:flex;gap:8px;flex-wrap:wrap;font-size:0.8em;">
                <span style="background:#00ff8822;padding:2px 8px;border-radius:12px;color:#00ff88;">⚽ ${g.promedio}/partido</span>
                <span style="background:#00d4ff22;padding:2px 8px;border-radius:12px;color:#00d4ff;">Marca: ${(g['>=1'] * 100).toFixed(0)}%</span>
            </div>`;
        } else if (tipo === 'portero' && j.eventos.paradas) {
            const p = j.eventos.paradas;
            probsHtml = `<div style="display:flex;gap:8px;flex-wrap:wrap;font-size:0.8em;">
                <span style="background:#00ff8822;padding:2px 8px;border-radius:12px;color:#00ff88;">🧤 ${p.promedio}/partido</span>
                <span style="background:#00d4ff22;padding:2px 8px;border-radius:12px;color:#00d4ff;">≥2: ${(p['>=2'] * 100).toFixed(0)}%</span>
            </div>`;
        }

        return `<div style="padding:8px 0;border-bottom:1px solid #1a2a3a;">
            <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                <span style="font-weight:600;">${j.nombre}</span>
                <span style="color:#8899aa;font-size:0.75em;">${j.partidos} partidos</span>
            </div>
            ${probsHtml}
        </div>`;
    };

    const renderLista = (lista, titulo, color, tipo) => {
        let s = `<div class="result-card" style="border-left-color:${color};"><div class="market" style="color:${color};">${titulo}</div><div style="margin-top:10px;">`;
        if (lista && lista.length > 0) {
            for (const j of lista) s += renderJugador(j, tipo);
        } else {
            s += `<p style="color:#8899aa;font-size:0.85em;">Sin datos suficientes</p>`;
        }
        return s + `</div></div>`;
    };

    let html = `<h3 style="margin-top:20px;color:#00d4ff;">👤 JUGADORES DESTACADOS</h3><div class="grid-2">`;
    html += renderLista(jl.goleadores, `⚽ Goleadores - ${data.local}`, '#00ff88', 'goleador');
    html += renderLista(jv.goleadores, `⚽ Goleadores - ${data.visitante}`, '#00ff88', 'goleador');
    html += renderLista(jl.porteros, `🧤 Porteros - ${data.local}`, '#00ff88', 'portero');
    html += renderLista(jv.porteros, `🧤 Porteros - ${data.visitante}`, '#00ff88', 'portero');
    html += `</div>`;

    return html;
}

function mostrarSeccionJugadoresPorTipo(data, tipo) {
    if (!data.jugadores) return '';

    const jl = data.jugadores.local || {};
    const jv = data.jugadores.visitante || {};

    const config = {
        goleadores: { titulo: '⚽ GOLEADORES', color: '#00ff88', evento: 'goles', icono: '⚽' },
        porteros: { titulo: '🧤 PORTEROS', color: '#00d4ff', evento: 'paradas', icono: '🧤' },
        tiros: { titulo: '🎯 TIROS', color: '#ffaa00', evento: 'tiros', icono: '🎯' },
        faltas: { titulo: '⚔️ FALTAS', color: '#ff8844', evento: 'faltas', icono: '⚔️' }
    };

    const cfg = config[tipo];
    if (!cfg) return '';

    const renderJugador = (j) => {
        if (!j || !j.eventos) return '';
        const ev = j.eventos[cfg.evento];
        if (!ev || ev.promedio === null) return '';

        let probs = '';
        if (tipo === 'goleadores') {
            probs = `<span style="background:${cfg.color}22; padding:2px 8px; border-radius:12px; color:${cfg.color};">${cfg.icono} ${ev.promedio}/partido</span>
                     <span style="background:#00d4ff22; padding:2px 8px; border-radius:12px; color:#00d4ff;">Marca: ${fmtPct(ev['>=1'], 0)}</span>`;
        } else if (tipo === 'porteros') {
            probs = `<span style="background:${cfg.color}22; padding:2px 8px; border-radius:12px; color:${cfg.color};">${cfg.icono} ${ev.promedio}/partido</span>
                     <span style="background:#00d4ff22; padding:2px 8px; border-radius:12px; color:#00d4ff;">≥2: ${fmtPct(ev['>=2'], 0)}</span>`;
        } else if (tipo === 'tiros') {
            probs = `<span style="background:${cfg.color}22; padding:2px 8px; border-radius:12px; color:${cfg.color};">${cfg.icono} ${ev.promedio}/partido</span>
                     <span style="background:#00d4ff22; padding:2px 8px; border-radius:12px; color:#00d4ff;">≥1: ${fmtPct(ev['>=1'], 0)}</span>`;
        } else if (tipo === 'faltas') {
            probs = `<span style="background:${cfg.color}22; padding:2px 8px; border-radius:12px; color:${cfg.color};">${cfg.icono} ${ev.promedio}/partido</span>
                     <span style="background:#00d4ff22; padding:2px 8px; border-radius:12px; color:#00d4ff;">≥1: ${fmtPct(ev['>=1'], 0)}</span>`;
        }

        return `<div style="padding:8px 0; border-bottom:1px solid #1a2a3a;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-weight:600;">${j.nombre}</span>
                <span style="color:#8899aa; font-size:0.75em;">${j.partidos} partidos</span>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap; font-size:0.8em;">${probs}</div>
        </div>`;
    };

    const renderLista = (lista, nombre, color) => {
        let s = `<div class="result-card" style="border-left-color:${color};"><div class="market" style="color:${color};">${cfg.titulo} — ${nombre}</div><div style="margin-top:10px;">`;
        if (lista && lista.length > 0) {
            for (const j of lista) s += renderJugador(j);
        } else {
            s += `<p style="color:#8899aa; font-size:0.85em;">Sin datos suficientes</p>`;
        }
        return s + `</div></div>`;
    };

    return renderLista(jl[tipo], data.local, '#00d4ff') +
           renderLista(jv[tipo], data.visitante, '#ff8844');
}
// ============================================================
// static/js/pronostico/render/calidad.js
// Secciones: Calidad de muestra + Nivel de confianza.
// ============================================================

function mostrarSeccionCalidad(data) {
    const sqs = data.sample_quality;
    if (!sqs) return '';

    const sqsLocal = sqs.local;
    const sqsVisit = sqs.visitante;

    return `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border-left:4px solid ${sqsLocal.color};">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div>
                <span style="color:#8899aa; font-size:0.8em;">CALIDAD DE MUESTRA (Score)</span>
                <h3 style="color:${sqsLocal.color}; margin:5px 0;">${sqsLocal.emoji} Global: ${sqs.global}/100</h3>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-top:15px;">
            <div style="background:#0a121c; padding:10px; border-radius:6px; border:1px solid #00d4ff44;">
                <p style="color:#00d4ff; font-weight:700; font-size:0.85em;">${data.local}</p>
                <p style="font-size:1.5em; color:${sqsLocal.color}; font-weight:700; margin:5px 0;">${sqsLocal.score}/100</p>
                <p style="font-size:0.75em; color:#8899aa;">Partidos: ${sqsLocal.componentes.partidos}/30 · Cobertura: ${sqsLocal.componentes.cobertura}/20 · Condición: ${sqsLocal.componentes.condicion}/15 · Consistencia: ${sqsLocal.componentes.consistencia}/15</p>
            </div>
            <div style="background:#0a121c; padding:10px; border-radius:6px; border:1px solid #ff884444;">
                <p style="color:#ff8844; font-weight:700; font-size:0.85em;">${data.visitante}</p>
                <p style="font-size:1.5em; color:${sqsVisit.color}; font-weight:700; margin:5px 0;">${sqsVisit.score}/100</p>
                <p style="font-size:0.75em; color:#8899aa;">Partidos: ${sqsVisit.componentes.partidos}/30 · Cobertura: ${sqsVisit.componentes.cobertura}/20 · Condición: ${sqsVisit.componentes.condicion}/15 · Consistencia: ${sqsVisit.componentes.consistencia}/15</p>
            </div>
        </div>
    </div>`;
}

function mostrarSeccionConfianza(data) {
    const conf = data.confianza;
    if (!conf) return '';

    return `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:20px; border-left:4px solid ${conf.color};">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div>
                <span style="color:#8899aa; font-size:0.8em;">MOTOR ${data.version_motor}</span>
                <h3 style="color:${conf.color}; margin:5px 0;">${conf.emoji} Confianza ${conf.nivel.toUpperCase()}</h3>
            </div>
            <div style="text-align:right;">
                <span style="color:#8899aa; font-size:0.85em;">${conf.partidos_local} partidos local · ${conf.partidos_visitante} partidos visitante</span>
            </div>
        </div>
    </div>`;
}
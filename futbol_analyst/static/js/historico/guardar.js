// ============================================================
// static/js/historico/guardar.js
// Guardar partido + modales de advertencias y vinculación.
// ============================================================

async function guardarDatos() {
    const selLocal = document.getElementById('local');
    const selVisit = document.getElementById('visitante');
    const local = selLocal.options[selLocal.selectedIndex]?.dataset?.name || '';
    const visitante = selVisit.options[selVisit.selectedIndex]?.dataset?.name || '';
    const fecha = document.getElementById('fecha').value;
    const estadisticasLocal = document.getElementById('estadisticasLocal').value;
    const estadisticasVisitante = document.getElementById('estadisticasVisitante').value;
    // ========== NUEVO: leer modo y texto unificado ==========
    const modo = modoIngestaActual();
    const textoUnificado = modo === 'unificado' 
        ? (document.getElementById('textoUnificado')?.value || '')
        : '';
    
    // En modo unificado, las estadísticas separadas van vacías
    const estadisticasLocalFinal = modo === 'unificado' ? '' : estadisticasLocal;
    const estadisticasVisitanteFinal = modo === 'unificado' ? '' : estadisticasVisitante;    
    const pais = document.getElementById('pais').value;
    const liga = document.getElementById('liga').value;
    const temporada = document.getElementById('temporada').value;
    const limpiar = document.getElementById('limpiarDespues').checked;
    const ogLocal = parseInt(document.getElementById('ogLocal')?.value) || 0;
    const ogVisitante = parseInt(document.getElementById('ogVisitante')?.value) || 0;

    if (!local || !visitante) {
        alert('Selecciona ambos equipos.');
        return;
    }
    // Validación según modo
    if (modo === 'unificado') {
        if (!textoUnificado.trim()) {
            alert('Pega el texto unificado (estadísticas + timeline).');
            return;
        }
    } else {
        if (!estadisticasLocalFinal.trim() && !estadisticasVisitanteFinal.trim()) {
            alert('Pega las estadísticas de al menos un equipo.');
            return;
        }
    }

    try {
        const preview = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                local, visitante, 
                estadisticasLocal: estadisticasLocalFinal, 
                estadisticasVisitante: estadisticasVisitanteFinal,
                textoUnificado: textoUnificado,
            })
        }).then(r => r.json());

        if (preview.local.error) {
            alert('❌ Error en LOCAL: ' + preview.local.error);
            return;
        }
        if (preview.visitante.error) {
            alert('❌ Error en VISITANTE: ' + preview.visitante.error);
            return;
        }

        const tieneAdvertencias = preview.local.advertencias.length > 0 || preview.visitante.advertencias.length > 0;

        if (tieneAdvertencias) {
            const confirmar = await mostrarModalAdvertencias(preview, local, visitante);
            if (!confirmar) return;
        }

        const resultado = await fetch('/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                local, visitante, fecha,
                estadisticasLocal: estadisticasLocalFinal,
                estadisticasVisitante: estadisticasVisitanteFinal,
                textoUnificado: textoUnificado,
                pais, liga, temporada,
                og_local: ogLocal,
                og_visitante: ogVisitante,
                forzar_guardado: tieneAdvertencias
            })
        }).then(r => r.json());

        if (resultado.success) {
            const msg = document.createElement('div');
            msg.className = 'alert alert-success';
            msg.textContent = `✅ Partido guardado (ID: ${resultado.partido_id})` +
                (resultado.advertencias_guardadas > 0 ? ` con ${resultado.advertencias_guardadas} advertencias` : '');
            document.getElementById('historicoContent').prepend(msg);
            setTimeout(() => msg.remove(), 5000);

        if (limpiar) {
            document.getElementById('estadisticasLocal').value = '';
            document.getElementById('estadisticasVisitante').value = '';
            const textoUnif = document.getElementById('textoUnificado');
            if (textoUnif) textoUnif.value = '';
            document.getElementById('fecha').value = '';
            // Resetear OG a 0
            const elOgLocal = document.getElementById('ogLocal');
            const elOgVisit = document.getElementById('ogVisitante');
            if (elOgLocal) elOgLocal.value = '0';
            if (elOgVisit) elOgVisit.value = '0';
            // Ocultar info del timeline
            const infoCont = document.getElementById('infoTimeline');
            if (infoCont) infoCont.style.display = 'none';
        }
            cargarHistorico();

            if (resultado.pronosticos_pendientes && resultado.pronosticos_pendientes.length > 0) {
                await mostrarModalVinculacion(
                    resultado.pronosticos_pendientes,
                    resultado.partido_id,
                    local, visitante
                );
            }
        } else {
            alert('❌ Error: ' + resultado.error);
        }

    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// ============================================================
// MODAL DE VINCULACIÓN AUTOMÁTICA
// ============================================================
function mostrarModalVinculacion(pendientes, partidoId, local, visitante) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';

        let listaHtml = '';
        for (const p of pendientes) {
            listaHtml += `
        <div style="background:#141c28;padding:12px;border-radius:8px;margin-bottom:10px;border:1px solid #1a2a3a;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div>
                    <strong style="color:#00d4ff;">Pronóstico #${p.id}</strong>
                    <span style="color:#8899aa;font-size:0.85em;margin-left:10px;">
                        ${p.fecha_pronostico ? p.fecha_pronostico.slice(0, 10) : ''}
                    </span>
                </div>
            </div>
            <div style="font-size:0.8em;color:#8899aa;">
                Probabilidades: 
                <span style="color:#00d4ff;">L ${(p.prob_local * 100).toFixed(0)}%</span> | 
                <span style="color:#ffaa00;">E ${(p.prob_empate * 100).toFixed(0)}%</span> | 
                <span style="color:#ff8844;">V ${(p.prob_visitante * 100).toFixed(0)}%</span>
                <br>
                BTTS: ${(p.prob_btts * 100).toFixed(0)}% | Over 2.5: ${(p.prob_over25 * 100).toFixed(0)}%
            </div>
            <button class="btn btn-success" style="margin-top:10px;padding:8px 16px;font-size:0.85em;"
                onclick="vincularPronostico(${p.id}, ${partidoId})">
                🔗 VINCULAR Y CERRAR
            </button>
        </div>
    `;
        }

        overlay.innerHTML = `
    <div class="modal-content" style="max-width:600px;">
        <h2>🔗 VINCULAR CON PRONÓSTICO</h2>
        <p style="color:#8899aa;font-size:0.9em;margin-bottom:15px;">
            Se ha guardado el partido <strong>${local} vs ${visitante}</strong>.<br>
            Se encontraron <strong style="color:#00ff88;">${pendientes.length}</strong> pronóstico(s) pendiente(s) para estos equipos.
            <br><br>
            ¿Quieres vincularlo(s) y cerrarlo(s) automáticamente con los goles del partido?
        </p>
        ${listaHtml}
        <div class="modal-buttons">
            <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove(); 
                window._resolverVinculacion && window._resolverVinculacion(false);">
                ❌ NO VINCULAR
            </button>
        </div>
    </div>
`;
        document.body.appendChild(overlay);

        window._resolverVinculacion = (result) => {
            overlay.remove();
            resolve(result);
        };
    });
}

async function vincularPronostico(pronosticoId, partidoId) {
    try {
        const resultado = await fetch('/api/pronosticos/vincular-partido', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pronostico_id: pronosticoId,
                partido_id: partidoId
            })
        }).then(r => r.json());

        if (resultado.success) {
            alert(`✅ Pronóstico #${pronosticoId} vinculado y cerrado (${resultado.goles_local}-${resultado.goles_visitante})`);
            document.querySelector('.modal-overlay').remove();
            window._resolverVinculacion && window._resolverVinculacion(true);
            cargarPronosticos();
            cargarBacktesting();
        } else {
            alert('❌ Error: ' + (resultado.error || 'Desconocido'));
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

function mostrarModalAdvertencias(preview, local, visitante) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';

        let advertenciasHtml = '';
        if (preview.local.advertencias.length > 0) {
            advertenciasHtml += `<h4 style="color:#00d4ff;margin-top:15px;">🏠 ${local} (Local)</h4>`;
            advertenciasHtml += '<ul style="margin-left:20px;color:#ffaa00;font-size:0.85em;">';
            for (const adv of preview.local.advertencias) {
                advertenciasHtml += `<li>${adv}</li>`;
            }
            advertenciasHtml += '</ul>';
        }
        if (preview.visitante.advertencias.length > 0) {
            advertenciasHtml += `<h4 style="color:#ff8844;margin-top:15px;">✈️ ${visitante} (Visitante)</h4>`;
            advertenciasHtml += '<ul style="margin-left:20px;color:#ffaa00;font-size:0.85em;">';
            for (const adv of preview.visitante.advertencias) {
                advertenciasHtml += `<li>${adv}</li>`;
            }
            advertenciasHtml += '</ul>';
        }

        overlay.innerHTML = `
    <div class="modal-content" style="max-width:700px;">
        <h2>⚠️ VISTA PREVIA CON ADVERTENCIAS</h2>
        <div style="background:#0a121c;padding:15px;border-radius:8px;margin:15px 0;border:1px solid #ffaa0044;">
            <p style="color:#8899aa;font-size:0.9em;">
                <strong>Partido:</strong> ${local} vs ${visitante}<br>
                <strong>Jugadores local:</strong> ${preview.local.jugadores}<br>
                <strong>Jugadores visitante:</strong> ${preview.visitante.jugadores}<br>
                <strong>Total de advertencias:</strong> ${preview.local.advertencias.length + preview.visitante.advertencias.length}
            </p>
        </div>
        <div style="max-height:300px;overflow-y:auto;">
            ${advertenciasHtml}
        </div>
        <div class="modal-buttons">
            <button class="btn btn-success" id="btnConfirmarGuardar" style="flex:1;">
                ✅ GUARDAR DE TODOS MODOS
            </button>
            <button class="btn btn-secondary" id="btnCancelarGuardar" style="flex:1;">
                ❌ CANCELAR Y CORREGIR
            </button>
        </div>
    </div>
`;
        document.body.appendChild(overlay);

        document.getElementById('btnConfirmarGuardar').onclick = () => {
            overlay.remove();
            resolve(true);
        };
        document.getElementById('btnCancelarGuardar').onclick = () => {
            overlay.remove();
            resolve(false);
        };
    });
}
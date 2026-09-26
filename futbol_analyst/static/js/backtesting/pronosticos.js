// ============================================================
// static/js/backtesting/pronosticos.js
// Lista de pronósticos + modal para registrar resultado.
// ============================================================

async function cargarPronosticos() {
    const container = document.getElementById('listaPronosticos');
    container.innerHTML = '<p style="color:#8899aa;">Cargando...</p>';

    try {
        const lista = await fetch('/api/pronosticos/lista').then(r => r.json());

        if (!lista || lista.length === 0) {
            container.innerHTML = '<p style="color:#8899aa;">No hay pronósticos guardados aún.</p>';
            return;
        }

        let html = `
    <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
            <thead>
                <tr style="background:#0a121c;color:#8899aa;">
                    <th style="padding:8px;border:1px solid #1a2a3a;">ID</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Fecha</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Partido</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Prob L/E/V</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Mercado</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">EV</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Estado</th>
                    <th style="padding:8px;border:1px solid #1a2a3a;">Acción</th>
                </tr>
            </thead>
            <tbody>
    `;

        for (const p of lista) {
            const probStr = `${(p.prob_local * 100).toFixed(0)}/${(p.prob_empate * 100).toFixed(0)}/${(p.prob_visitante * 100).toFixed(0)}`;
            const evStr = p.ev_principal !== null ? `${p.ev_principal.toFixed(1)}%` : '-';
            const estado = p.cerrado ?
                `<span style="color:#00ff88;">✅ Cerrado</span> <small>(${p.resultado_local}-${p.resultado_visitante})</small>` :
                `<span style="color:#ffaa00;">⏳ Abierto</span>`;

            const badgeAuto = p.automatico
                ? `<span style="background:#8844ff22; color:#8844ff; padding:2px 6px; border-radius:8px; font-size:0.7em; font-weight:700; margin-left:6px;">🤖 AUTO</span>`
                : '';
            let accion = '';
            
            if (!p.cerrado) {
                accion += `
                    <button class="btn btn-warning" onclick="abrirModalResultado(${p.id}, '${p.local}', '${p.visitante}')" style="padding:4px 10px;font-size:0.75em;margin-right:4px;">
                        📝
                    </button>
                `;
            }
            
            accion += `
                <button class="btn btn-secondary" onclick="editarPronostico(${p.id})" style="padding:4px 10px;font-size:0.75em;margin-right:4px;" title="Editar">
                    ✏️
                </button>
                <button class="btn btn-danger" onclick="eliminarPronostico(${p.id})" style="padding:4px 10px;font-size:0.75em;" title="Eliminar">
                    🗑️
                </button>
            `;

            html += `
        <tr>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">${p.id}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">${p.fecha_partido || p.fecha_pronostico?.slice(0, 10) || '-'}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;">
                <span style="color:#00d4ff;">${p.local}</span> vs 
                <span style="color:#ff8844;">${p.visitante}</span>
                ${badgeAuto}
            </td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${probStr}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${p.mercado_principal || '-'}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${evStr}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${estado}</td>
            <td style="padding:6px 8px;border:1px solid #1a2a3a;text-align:center;">${accion}</td>
        </tr>
        `;
        }

        html += '</tbody></table></div>';
        container.innerHTML = html;

    } catch (e) {
        container.innerHTML = `<p style="color:#ff4455;">Error: ${e.message}</p>`;
    }
}

// ============================================================
// MODAL PARA REGISTRAR RESULTADO
// ============================================================
function abrirModalResultado(pronosticoId, local, visitante) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
    <div class="modal-content" style="max-width:800px; max-height:90vh; overflow-y:auto;">
        <h2>📝 REGISTRAR RESULTADO</h2>
        <div style="background:#0a121c;padding:12px;border-radius:8px;margin-bottom:15px;">
            <p style="color:#8899aa;font-size:0.9em;margin:0;">
                <strong style="color:#00d4ff;">${local}</strong> vs 
                <strong style="color:#ff8844;">${visitante}</strong>
            </p>
        </div>
        
        <div style="background:#0a121c;padding:12px;border-radius:8px;margin-bottom:15px;border:1px solid #00d4ff44;">
            <h4 style="color:#00d4ff;margin-bottom:10px;font-size:0.95em;">📅 INFORMACIÓN DEL PARTIDO</h4>
            <div class="form-row">
                <div class="form-group">
                    <label>📆 Fecha</label>
                    <input type="date" id="modalFecha" value="${new Date().toISOString().split('T')[0]}">
                </div>
                <div class="form-group">
                    <label>🌍 País</label>
                    <select id="modalPais" onchange="cargarLigasModal()">
                        <option value="">Selecciona país</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>🏆 Liga / Competición</label>
                    <select id="modalLiga" onchange="cargarTemporadasModal()">
                        <option value="">Selecciona liga</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>📅 Temporada</label>
                    <select id="modalTemporada">
                        <option value="">Selecciona temporada</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div style="background:#0a121c;padding:12px;border-radius:8px;margin-bottom:15px;border:1px solid #00ff8844;">
            <h4 style="color:#00ff88;margin-bottom:10px;font-size:0.95em;">⚽ RESULTADO FINAL</h4>
            <div class="form-row">
                <div class="form-group">
                    <label>Goles ${local} (Local)</label>
                    <input type="number" id="modalGolesLocal" min="0" value="0">
                </div>
                <div class="form-group">
                    <label>Goles ${visitante} (Visitante)</label>
                    <input type="number" id="modalGolesVisitante" min="0" value="0">
                </div>
            </div>
        </div>
        
        <div style="background:#0a121c;padding:12px;border-radius:8px;margin-bottom:15px;border:1px solid #ffaa0044;">
            <h4 style="color:#ffaa00;margin-bottom:10px;font-size:0.95em;">📋 ESTADÍSTICAS (opcional)</h4>
            <p style="color:#8899aa;font-size:0.85em;margin-bottom:10px;">
                Si tienes las estadísticas del partido, pégalas aquí. Se guardarán 
                también en el histórico.
            </p>
            
            <div class="checkbox-group" style="margin-bottom:10px;">
                <input type="checkbox" id="modalIncluirEstadisticas" onchange="toggleEstadisticasModal()">
                <label for="modalIncluirEstadisticas">📎 Incluir estadísticas de jugadores</label>
            </div>
            
            <div id="modalEstadisticasArea" style="display:none;">
                <div class="form-group" style="margin-bottom:10px;">
                    <label style="color:#00d4ff;">🏠 ${local} (Local)</label>
                    <textarea id="modalEstadisticasLocal" 
                        placeholder="Pega aquí las estadísticas del equipo local..." 
                        style="min-height:120px;font-size:0.8em;"></textarea>
                </div>
                <div class="form-group">
                    <label style="color:#ff8844;">✈️ ${visitante} (Visitante)</label>
                    <textarea id="modalEstadisticasVisitante" 
                        placeholder="Pega aquí las estadísticas del equipo visitante..." 
                        style="min-height:120px;font-size:0.8em;"></textarea>
                </div>
            </div>
        </div>
        
        <div class="modal-buttons">
            <button class="btn btn-success" onclick="confirmarResultado(${pronosticoId}, '${local.replace(/'/g, "\\'")}', '${visitante.replace(/'/g, "\\'")}')">
                ✅ GUARDAR
            </button>
            <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                ❌ CANCELAR
            </button>
        </div>
    </div>
    `;
    document.body.appendChild(overlay);

    cargarPaisesModal();
}

async function cargarPaisesModal() {
    try {
        const continentes = await apiGet('/api/continentes');
        const selectPais = document.getElementById('modalPais');
        if (!selectPais) return;

        let todosPaises = [];
        for (const cont of continentes) {
            const paises = await apiGet(`/api/paises?continente=${encodeURIComponent(cont)}`);
            todosPaises = todosPaises.concat(paises);
        }

        selectPais.innerHTML = '<option value="">Selecciona país</option>';
        for (const pais of todosPaises) {
            const opt = document.createElement('option');
            opt.value = pais;
            opt.textContent = pais;
            selectPais.appendChild(opt);
        }
    } catch (e) {
        console.error('Error cargando países modal:', e);
    }
}

async function cargarLigasModal() {
    const pais = document.getElementById('modalPais').value;
    const selectLiga = document.getElementById('modalLiga');
    const selectTemp = document.getElementById('modalTemporada');

    selectLiga.innerHTML = '<option value="">Selecciona liga</option>';
    selectTemp.innerHTML = '<option value="">Selecciona temporada</option>';

    if (!pais) return;

    try {
        const continentes = await apiGet('/api/continentes');
        let continenteEncontrado = null;

        for (const cont of continentes) {
            const paises = await apiGet(`/api/paises?continente=${encodeURIComponent(cont)}`);
            if (paises.includes(pais)) {
                continenteEncontrado = cont;
                break;
            }
        }

        if (!continenteEncontrado) return;

        const ligas = await apiGet(`/api/ligas?continente=${encodeURIComponent(continenteEncontrado)}&pais=${encodeURIComponent(pais)}`);

        for (const liga of ligas) {
            const opt = document.createElement('option');
            opt.value = liga;
            opt.textContent = liga;
            selectLiga.appendChild(opt);
        }

        selectLiga.dataset.continente = continenteEncontrado;
    } catch (e) {
        console.error('Error cargando ligas modal:', e);
    }
}

async function cargarTemporadasModal() {
    const pais = document.getElementById('modalPais').value;
    const selectLiga = document.getElementById('modalLiga');
    const liga = selectLiga.value;
    const continente = selectLiga.dataset.continente;
    const selectTemp = document.getElementById('modalTemporada');

    selectTemp.innerHTML = '<option value="">Selecciona temporada</option>';

    if (!pais || !liga || !continente) return;

    try {
        const temporadas = await apiGet(`/api/temporadas?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}&liga=${encodeURIComponent(liga)}`);

        for (const temp of temporadas) {
            const opt = document.createElement('option');
            opt.value = temp;
            opt.textContent = temp;
            selectTemp.appendChild(opt);
        }
    } catch (e) {
        console.error('Error cargando temporadas modal:', e);
    }
}

function toggleEstadisticasModal() {
    const checkbox = document.getElementById('modalIncluirEstadisticas');
    const area = document.getElementById('modalEstadisticasArea');
    area.style.display = checkbox.checked ? 'block' : 'none';
}

async function confirmarResultado(pronosticoId, local, visitante) {
    const golesLocal = parseInt(document.getElementById('modalGolesLocal').value);
    const golesVisitante = parseInt(document.getElementById('modalGolesVisitante').value);
    const incluirStats = document.getElementById('modalIncluirEstadisticas')?.checked || false;

    const fecha = document.getElementById('modalFecha')?.value || new Date().toISOString().split('T')[0];
    const pais = document.getElementById('modalPais')?.value || '';
    const liga = document.getElementById('modalLiga')?.value || '';
    const temporada = document.getElementById('modalTemporada')?.value || '';

    if (isNaN(golesLocal) || isNaN(golesVisitante)) {
        alert('Introduce goles válidos');
        return;
    }

    try {
        const resultado = await fetch('/api/pronosticos/resultado', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: pronosticoId,
                goles_local: golesLocal,
                goles_visitante: golesVisitante
            })
        }).then(r => r.json());

        if (!resultado.success) {
            alert('❌ Error guardando resultado: ' + (resultado.error || 'Desconocido'));
            return;
        }

        if (incluirStats) {
            const statsLocal = document.getElementById('modalEstadisticasLocal').value;
            const statsVisitante = document.getElementById('modalEstadisticasVisitante').value;

            if (statsLocal.trim() || statsVisitante.trim()) {
                const guardado = await fetch('/guardar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        local, visitante,
                        fecha: fecha,
                        pais: pais,
                        liga: liga,
                        temporada: temporada,
                        estadisticasLocal: statsLocal,
                        estadisticasVisitante: statsVisitante,
                        forzar_guardado: false
                    })
                }).then(r => r.json());

                if (guardado.success && guardado.partido_id) {
                    await fetch('/api/pronosticos/vincular-partido', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pronostico_id: pronosticoId,
                            partido_id: guardado.partido_id
                        })
                    }).then(r => r.json());

                    alert(`✅ Resultado guardado: ${golesLocal}-${golesVisitante}\n✅ Estadísticas vinculadas al histórico (${fecha} · ${liga})`);
                } else if (guardado.requiere_confirmacion) {
                    alert('⚠️ Las estadísticas tienen advertencias. Se guardó el resultado pero NO las estadísticas.');
                } else {
                    alert('⚠️ Resultado guardado. Error en estadísticas: ' + (guardado.error || 'Desconocido'));
                }
            }
        } else {
            alert(`✅ Resultado guardado: ${golesLocal}-${golesVisitante}`);
        }

        document.querySelector('.modal-overlay').remove();
        cargarPronosticos();
        cargarBacktesting();
        cargarHistorico();

    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// ============================================================
// EDITAR PRONÓSTICO (equipos, cuota, mercado, fecha)
// ============================================================
async function editarPronostico(pronosticoId) {
    let pronostico;
    try {
        pronostico = await fetch(`/api/pronosticos/${pronosticoId}`).then(r => r.json());
    } catch (e) {
        alert('❌ Error: ' + e.message);
        return;
    }

    if (pronostico.error) {
        alert('❌ ' + pronostico.error);
        return;
    }

    const cuotaActual = pronostico.cuota_real || 0;
    const mercadoActual = pronostico.mercado_principal || 'Local';
    const fechaActual = pronostico.fecha_partido || '';
    const localActual = pronostico.partido_local || '';
    const visitanteActual = pronostico.partido_visitante || '';

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-content" style="max-width:550px;">
            <h2>✏️ EDITAR PRONÓSTICO #${pronosticoId}</h2>

            <!-- ========== Equipos ========== -->
            <div style="background:#0a121c; padding:12px; border-radius:8px; margin-bottom:15px; border:1px solid #00d4ff44;">
                <h4 style="color:#00d4ff; margin-bottom:10px; font-size:0.95em;">⚽ EQUIPOS</h4>
                <div class="form-row">
                    <div class="form-group">
                        <label style="color:#00d4ff;">🏠 Local</label>
                        <input type="text" id="editLocal" value="${localActual}">
                    </div>
                    <div class="form-group">
                        <label style="color:#ff8844;">✈️ Visitante</label>
                        <input type="text" id="editVisitante" value="${visitanteActual}">
                    </div>
                </div>
                <p style="color:#8899aa; font-size:0.75em; margin-top:8px;">
                    ⚠️ Si cambias los equipos, se normalizarán automáticamente (aliases).
                </p>
            </div>

            <!-- ========== Fecha y mercado ========== -->
            <div class="form-row">
                <div class="form-group">
                    <label>📅 Fecha del partido</label>
                    <input type="date" id="editFecha" value="${fechaActual}">
                </div>
                <div class="form-group">
                    <label>🎯 Mercado principal</label>
                    <select id="editMercado">
                        <option value="Local" ${mercadoActual === 'Local' ? 'selected' : ''}>Local Gana</option>
                        <option value="Empate" ${mercadoActual === 'Empate' ? 'selected' : ''}>Empate</option>
                        <option value="Visitante" ${mercadoActual === 'Visitante' ? 'selected' : ''}>Visitante Gana</option>
                        <option value="BTTS" ${mercadoActual === 'BTTS' ? 'selected' : ''}>BTTS</option>
                        <option value="Over25" ${mercadoActual === 'Over25' ? 'selected' : ''}>Over 2.5</option>
                    </select>
                </div>
            </div>

            <!-- ========== Cuota ========== -->
            <div class="form-group">
                <label>💶 Cuota real (opcional)</label>
                <input type="number" id="editCuota" step="0.01" min="0" value="${cuotaActual || ''}" placeholder="Ej: 1.85">
                <p style="color:#8899aa; font-size:0.75em; margin-top:5px;">
                    Si introduces cuota, se recalcula el EV automáticamente.
                </p>
            </div>

            <div class="modal-buttons">
                <button class="btn btn-success" onclick="guardarEdicionPronostico(${pronosticoId})">
                    💾 GUARDAR
                </button>
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                    ❌ CANCELAR
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}


async function guardarEdicionPronostico(pronosticoId) {
    const local = document.getElementById('editLocal').value.trim();
    const visitante = document.getElementById('editVisitante').value.trim();
    const cuota = parseFloat(document.getElementById('editCuota').value) || 0;
    const mercado = document.getElementById('editMercado').value;
    const fecha = document.getElementById('editFecha').value;

    if (!local || !visitante) {
        alert('⚠️ Debes indicar ambos equipos');
        return;
    }

    if (local.toLowerCase() === visitante.toLowerCase()) {
        alert('⚠️ El local y el visitante no pueden ser el mismo equipo');
        return;
    }

    try {
        const resultado = await fetch(`/api/pronosticos/editar/${pronosticoId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                partido_local: local,
                partido_visitante: visitante,
                cuota_real: cuota,
                mercado_principal: mercado,
                fecha_partido: fecha,
            })
        }).then(r => r.json());

        if (resultado.success) {
            document.querySelector('.modal-overlay').remove();
            cargarPronosticos();
        } else {
            alert('❌ ' + (resultado.error || 'Error desconocido'));
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// ============================================================
// ELIMINAR PRONÓSTICO
// ============================================================
async function eliminarPronostico(pronosticoId) {
    if (!confirm(`🗑️ ¿Eliminar el pronóstico #${pronosticoId}?\n\nEsta acción NO se puede deshacer.`)) {
        return;
    }

    try {
        const resultado = await fetch(`/api/pronosticos/eliminar/${pronosticoId}`, {
            method: 'DELETE',
        }).then(r => r.json());

        if (resultado.success) {
            cargarPronosticos();
        } else {
            alert('❌ ' + (resultado.error || 'Error desconocido'));
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}


// ============================================================
// BORRAR TODOS LOS PRONÓSTICOS
// ============================================================
async function borrarTodosPronosticos() {
    const opcion = prompt(
        '🗑️ ¿Qué quieres borrar?\n\n' +
        '1 → Solo abiertos\n' +
        '2 → TODOS (abiertos + cerrados)\n\n' +
        'Escribe 1 o 2 (o cancela):'
    );

    if (opcion === null) return;

    let soloAbiertos;
    if (opcion === '1') {
        soloAbiertos = true;
    } else if (opcion === '2') {
        soloAbiertos = false;
        if (!confirm('⚠️ Vas a borrar TODOS los pronósticos (incluidos cerrados).\n\n¿Seguro?')) {
            return;
        }
    } else {
        alert('Opción no válida');
        return;
    }

    try {
        const resultado = await fetch(`/api/pronosticos/eliminar-todos?solo_abiertos=${soloAbiertos}`, {
            method: 'DELETE',
        }).then(r => r.json());

        if (resultado.success) {
            alert(`✅ ${resultado.total_borrados} pronósticos eliminados`);
            cargarPronosticos();
            cargarBacktesting();
        } else {
            alert('❌ ' + (resultado.error || 'Error desconocido'));
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}
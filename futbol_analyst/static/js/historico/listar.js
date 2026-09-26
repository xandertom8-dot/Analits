// ============================================================
// static/js/historico/listar.js
// Listar partidos, filtros, paginación, editar y eliminar.
// ============================================================

// Estado de los filtros del histórico (global dentro del scope del script)
let historicoFiltros = {
    q: '',
    fecha_desde: '',
    fecha_hasta: '',
    pagina: 1,
    por_pagina: 20,
};

let historicoFiltrosAvanzadosAbiertos = false;

// ============================================================
// CARGAR HISTÓRICO
// ============================================================
async function cargarHistorico() {
    const container = document.getElementById('historicoContent');
    container.innerHTML = '<p style="color:#8899aa;">Cargando...</p>';

    try {
        const params = new URLSearchParams();
        params.append('pagina', historicoFiltros.pagina);
        params.append('por_pagina', historicoFiltros.por_pagina);

        if (historicoFiltros.q) params.append('q', historicoFiltros.q);
        if (historicoFiltros.fecha_desde) params.append('fecha_desde', historicoFiltros.fecha_desde);
        if (historicoFiltros.fecha_hasta) params.append('fecha_hasta', historicoFiltros.fecha_hasta);

        const data = await fetch('/historico?' + params.toString()).then(r => r.json());

        if (data.error) {
            container.innerHTML = `<p style="color:#8899aa;">❌ ${data.error}</p>`;
            return;
        }

        const partidos = data.partidos || [];
        const pag = data.paginacion || { pagina: 1, total: 0, total_paginas: 0 };

        let html = '';

        // Barra de búsqueda simple
        html += `
<div style="margin-bottom:15px;">
    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
        <div style="flex:1; min-width:250px;">
            <input type="text" id="filtroQ" value="${historicoFiltros.q}" 
                placeholder="🔍 Buscar equipo o competición..." 
                style="width:100%; background:#0a121c; border:1px solid #1a2a3a; color:#e0e0e0; padding:10px 14px; border-radius:8px; font-size:0.9em;">
        </div>
        <button class="btn btn-secondary" style="padding:10px 16px; font-size:0.85em; margin:0;" 
            onclick="toggleFiltrosAvanzados()">
            ${historicoFiltrosAvanzadosAbiertos ? '🔽' : '▶️'} Filtros avanzados
        </button>
    </div>
</div>
`;

        // Filtros avanzados
        if (historicoFiltrosAvanzadosAbiertos) {
            html += `
    <div style="background:#0a121c; padding:15px; border-radius:8px; margin-bottom:15px; border:1px solid #1a2a3a;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="form-group" style="margin:0;">
                <label style="font-size:0.75em; color:#8899aa; text-transform:uppercase;">📆 Desde</label>
                <input type="date" id="filtroFechaDesde" value="${historicoFiltros.fecha_desde}"
                    style="background:#0a121c; border:1px solid #1a2a3a; color:#e0e0e0; padding:8px 12px; border-radius:6px; font-size:0.9em;">
            </div>
            <div class="form-group" style="margin:0;">
                <label style="font-size:0.75em; color:#8899aa; text-transform:uppercase;">📆 Hasta</label>
                <input type="date" id="filtroFechaHasta" value="${historicoFiltros.fecha_hasta}"
                    style="background:#0a121c; border:1px solid #1a2a3a; color:#e0e0e0; padding:8px 12px; border-radius:6px; font-size:0.9em;">
            </div>
        </div>
        <div style="display:flex; gap:10px; margin-top:12px;">
            <button class="btn" style="padding:8px 20px; font-size:0.85em; margin:0;" onclick="aplicarFiltrosAvanzados()">
                ✅ Aplicar fechas
            </button>
            <button class="btn btn-secondary" style="padding:8px 20px; font-size:0.85em; margin:0;" onclick="limpiarFiltrosAvanzados()">
                ❌ Limpiar fechas
            </button>
        </div>
    </div>
    `;
        }

        // Chips de filtros activos
        const filtrosActivos = [];
        if (historicoFiltros.q) filtrosActivos.push({ tipo: 'q', label: `🔍 "${historicoFiltros.q}"` });
        if (historicoFiltros.fecha_desde) filtrosActivos.push({ tipo: 'fecha_desde', label: `📆 Desde: ${historicoFiltros.fecha_desde}` });
        if (historicoFiltros.fecha_hasta) filtrosActivos.push({ tipo: 'fecha_hasta', label: `📆 Hasta: ${historicoFiltros.fecha_hasta}` });

        if (filtrosActivos.length > 0) {
            html += `<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:15px; align-items:center;">`;
            html += `<span style="color:#8899aa; font-size:0.85em;">Filtros activos:</span>`;
            for (const f of filtrosActivos) {
                html += `
        <span style="background:#00d4ff22; border:1px solid #00d4ff44; color:#00d4ff; 
            padding:4px 12px; border-radius:12px; font-size:0.8em; display:inline-flex; align-items:center; gap:6px;">
            ${f.label}
            <span style="cursor:pointer; color:#ff4455; font-weight:700;" onclick="quitarFiltro('${f.tipo}')">✕</span>
        </span>`;
            }
            html += `<button class="btn btn-secondary" style="padding:4px 12px; font-size:0.75em; margin:0;" onclick="limpiarFiltrosHistorico()">
        🗑️ Limpiar todos
    </button>`;
            html += `</div>`;
        }

        // Contador
        html += `
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:10px;">
    <p style="color:#8899aa; font-size:0.85em; margin:0;">
        Mostrando <strong style="color:#00d4ff;">${partidos.length}</strong> 
        de <strong style="color:#00d4ff;">${pag.total}</strong> partidos
        ${pag.total_paginas > 1 ? ` · Página ${pag.pagina} de ${pag.total_paginas}` : ''}
    </p>
    <select id="filtroPorPagina" onchange="cambiarPorPaginaHistorico()" 
        style="background:#0a121c; border:1px solid #1a2a3a; color:#e0e0e0; padding:6px 12px; border-radius:6px; font-size:0.8em;">
        <option value="20" ${historicoFiltros.por_pagina == 20 ? 'selected' : ''}>20 por página</option>
        <option value="50" ${historicoFiltros.por_pagina == 50 ? 'selected' : ''}>50 por página</option>
        <option value="100" ${historicoFiltros.por_pagina == 100 ? 'selected' : ''}>100 por página</option>
    </select>
</div>
`;

        // Tabla
        if (partidos.length === 0) {
            html += `<p style="color:#8899aa; text-align:center; padding:30px;">No se encontraron partidos con esos filtros.</p>`;
        } else {
            html += `
    <div style="overflow-x:auto;">
        <table class="historico-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Fecha</th>
                    <th>Local</th>
                    <th style="text-align:center;">Resultado</th>
                    <th>Visitante</th>
                    <th style="text-align:center;">Ganador</th>
                    <th>Competición</th>
                    <th>Jugadores</th>
                    <th>Acción</th>
                </tr>
            </thead>
            <tbody>
    `;

            for (const row of partidos) {
                let resultadoColor = '#e0e0e0';
                let ganadorColor = '#8899aa';
                if (row.ganador === 'local') {
                    resultadoColor = '#00d4ff';
                    ganadorColor = '#00d4ff';
                } else if (row.ganador === 'visitante') {
                    resultadoColor = '#ff8844';
                    ganadorColor = '#ff8844';
                } else if (row.ganador === 'empate') {
                    resultadoColor = '#ffaa00';
                    ganadorColor = '#ffaa00';
                }

                html += `<tr>
            <td>${row.id}</td>
            <td>${row.fecha || '-'}</td>
            <td style="color:#00d4ff;">${row.local}</td>
            <td style="text-align:center; font-weight:700; color:${resultadoColor}; font-family:monospace; font-size:1.05em;">
                ${row.resultado || '0 - 0'}
            </td>
            <td style="color:#ff8844;">${row.visitante}</td>
            <td style="text-align:center; color:${ganadorColor}; font-size:0.85em; font-weight:600;">
                ${row.ganador_label || '-'}
            </td>
            <td>${row.liga || '-'}</td>
            <td>${row.jugadores || 0}</td>
            <td style="white-space:nowrap;">
                <button class="btn btn-warning" onclick="editarPartido(${row.id})" style="padding:4px 12px;font-size:0.75em;margin-right:5px;">✏️</button>
                <button class="btn btn-danger" onclick="eliminarPartido(${row.id})" style="padding:4px 12px;font-size:0.75em;">🗑️</button>
            </td>
        </tr>`;
            }

            html += `</tbody></table></div>`;
        }

        // Paginación
        if (pag.total_paginas > 1) {
            html += `
    <div style="display:flex; justify-content:center; align-items:center; gap:10px; margin-top:20px; flex-wrap:wrap;">
        <button class="btn btn-secondary" style="padding:8px 16px; font-size:0.85em; margin:0;" 
            onclick="irPaginaHistorico(1)" ${!pag.tiene_anterior ? 'disabled' : ''}>
            ⏮️ Primera
        </button>
        <button class="btn btn-secondary" style="padding:8px 16px; font-size:0.85em; margin:0;" 
            onclick="irPaginaHistorico(${pag.pagina - 1})" ${!pag.tiene_anterior ? 'disabled' : ''}>
            ◀️ Anterior
        </button>
        <span style="color:#8899aa; font-size:0.9em; padding:0 10px;">
            Página <strong style="color:#00d4ff;">${pag.pagina}</strong> de <strong>${pag.total_paginas}</strong>
        </span>
        <button class="btn btn-secondary" style="padding:8px 16px; font-size:0.85em; margin:0;" 
            onclick="irPaginaHistorico(${pag.pagina + 1})" ${!pag.tiene_siguiente ? 'disabled' : ''}>
            Siguiente ▶️
        </button>
        <button class="btn btn-secondary" style="padding:8px 16px; font-size:0.85em; margin:0;" 
            onclick="irPaginaHistorico(${pag.total_paginas})" ${!pag.tiene_siguiente ? 'disabled' : ''}>
            Última ⏭️
        </button>
    </div>
    `;
        }

        container.innerHTML = html;

        const inputQ = document.getElementById('filtroQ');
        if (inputQ) {
            let timeoutId;
            inputQ.addEventListener('input', () => {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    historicoFiltros.q = inputQ.value.trim();
                    historicoFiltros.pagina = 1;
                    cargarHistorico();
                }, 400);
            });

            if (historicoFiltros.q) {
                inputQ.focus();
                inputQ.setSelectionRange(historicoFiltros.q.length, historicoFiltros.q.length);
            }
        }

    } catch (error) {
        container.innerHTML = `<p style="color:#8899aa;">❌ Error: ${error.message}</p>`;
    }
}

// ============================================================
// FILTROS
// ============================================================
function toggleFiltrosAvanzados() {
    historicoFiltrosAvanzadosAbiertos = !historicoFiltrosAvanzadosAbiertos;
    cargarHistorico();
}

function aplicarFiltrosAvanzados() {
    historicoFiltros.fecha_desde = document.getElementById('filtroFechaDesde')?.value || '';
    historicoFiltros.fecha_hasta = document.getElementById('filtroFechaHasta')?.value || '';
    historicoFiltros.pagina = 1;
    cargarHistorico();
}

function limpiarFiltrosAvanzados() {
    historicoFiltros.fecha_desde = '';
    historicoFiltros.fecha_hasta = '';
    historicoFiltros.pagina = 1;
    cargarHistorico();
}

function quitarFiltro(tipo) {
    if (tipo === 'q') historicoFiltros.q = '';
    else if (tipo === 'fecha_desde') historicoFiltros.fecha_desde = '';
    else if (tipo === 'fecha_hasta') historicoFiltros.fecha_hasta = '';
    historicoFiltros.pagina = 1;
    cargarHistorico();
}

function limpiarFiltrosHistorico() {
    historicoFiltros = {
        q: '',
        fecha_desde: '',
        fecha_hasta: '',
        pagina: 1,
        por_pagina: historicoFiltros.por_pagina,
    };
    historicoFiltrosAvanzadosAbiertos = false;
    cargarHistorico();
}

function irPaginaHistorico(pagina) {
    if (pagina < 1) return;
    historicoFiltros.pagina = pagina;
    cargarHistorico();
}

function cambiarPorPaginaHistorico() {
    historicoFiltros.por_pagina = parseInt(document.getElementById('filtroPorPagina').value);
    historicoFiltros.pagina = 1;
    cargarHistorico();
}

// ============================================================
// ELIMINAR / EDITAR
// ============================================================
function eliminarPartido(id) {
    if (!confirm('¿Eliminar este partido?')) return;
    fetch('/eliminar/' + id, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) { cargarHistorico(); }
            else { alert('❌ ' + data.error); }
        })
        .catch(e => alert('❌ ' + e.message));
}

function confirmarBorrarTodo() {
    if (!confirm('⚠️ ¿Eliminar TODOS los datos?')) return;
    if (!confirm('⚠️ ÚLTIMA ADVERTENCIA. ¿Continuar?')) return;
    fetch('/eliminar-todo', { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) { cargarHistorico(); }
            else { alert('❌ ' + data.error); }
        })
        .catch(e => alert('❌ ' + e.message));
}

function editarPartido(id) {
    fetch('/partido/' + id)
        .then(r => r.json())
        .then(data => {
            if (data.error) { alert('❌ ' + data.error); return; }
            
            // ========== NUEVO: preparar timeline HTML ==========
            const timelineHtml = renderTimelineEdicion(data.timeline, data.local, data.visitante);
            
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.style.alignItems = 'flex-start';
            overlay.style.overflowY = 'auto';
            overlay.innerHTML = `
            <div class="modal-content" style="max-width:900px; max-height:90vh; overflow-y:auto;">
                <h2>✏️ EDITAR PARTIDO</h2>
                <div class="form-group">
                    <label>📆 Fecha</label>
                    <input type="date" id="editFecha" value="${data.fecha || ''}">
                </div>
                <div class="form-group">
                    <label>🏠 Equipo Local</label>
                    <input type="text" id="editLocal" value="${data.local}">
                </div>
                <div class="form-group">
                    <label>✈️ Equipo Visitante</label>
                    <input type="text" id="editVisitante" value="${data.visitante}">
                </div>
                <div class="form-group">
                    <label>🏆 Competición</label>
                    <input type="text" id="editLiga" value="${data.liga || ''}">
                </div>

                <!-- ========== NUEVO: OG ========== -->
                <div style="background:#0a121c; padding:12px; border-radius:8px; margin-top:15px; border:1px solid #ffaa0044;">
                    <h4 style="color:#ffaa00; margin-bottom:8px; font-size:0.9em;">⚽ GOLES EN PROPIA PUERTA</h4>
                    <p style="color:#8899aa; font-size:0.8em; margin-bottom:10px;">
                        ${data.timeline ? '✅ Detectados automáticamente del timeline. Puedes ajustarlos manualmente si hace falta.' : 'Corrige aquí si el partido tuvo autogoles.'}
                    </p>
                    <div class="form-row" style="margin-bottom:0;">
                        <div class="form-group">
                            <label style="color:#00d4ff;">🏠 OG del Local</label>
                            <input type="number" id="editOgLocal" min="0" value="${data.og_local || 0}" step="1">
                        </div>
                        <div class="form-group">
                            <label style="color:#ff8844;">✈️ OG del Visitante</label>
                            <input type="number" id="editOgVisitante" min="0" value="${data.og_visitante || 0}" step="1">
                        </div>
                    </div>
                </div>

                ${timelineHtml}

                <!-- ========== ACTUALIZAR CON TEXTO UNIFICADO ========== -->
                <div style="margin-top:20px;">
                    <button type="button" 
                        class="btn btn-secondary" 
                        style="width:100%; padding:12px; font-size:0.9em; margin:0;"
                        onclick="toggleActualizarUnificado(${id})">
                        <span id="toggleActualizarIcon_${id}">▶️</span> 
                        🔄 ACTUALIZAR CON TEXTO UNIFICADO
                    </button>
                    
                    <div id="bloqueActualizarUnificado_${id}" style="display:none; margin-top:15px; padding:15px; background:#8844ff11; border-radius:8px; border:1px solid #8844ff44;">
                        <p style="color:#8899aa; font-size:0.85em; margin-bottom:12px;">
                            <strong style="color:#8844ff;">⚠️ Esto REEMPLAZARÁ las estadísticas actuales</strong> de este partido 
                            con las del nuevo texto unificado. Se detectarán OG y timeline automáticamente. 
                            <strong style="color:#00ff88;">El ID del partido se mantiene</strong> (los pronósticos vinculados siguen vinculados).
                        </p>
                        
                        <div class="form-group">
                            <label style="color:#8844ff;">📋 Texto unificado (estadísticas + timeline)</label>
                            <textarea id="textoUnificadoActualizar_${id}" 
                                placeholder="===== ESTADÍSTICAS DE JUGADORES =====&#10;&#10;--- EQUIPO 1 ---&#10;...&#10;&#10;--- EQUIPO 2 ---&#10;...&#10;&#10;===== TIMELINE =====&#10;&#10;--- LOCAL ---&#10;...&#10;&#10;--- VISITANTE ---&#10;..."
                                style="min-height:250px; font-family:'Courier New', monospace; font-size:0.8em;"></textarea>
                        </div>
                        
                        <div id="previewActualizar_${id}" style="margin-top:12px; display:none;"></div>
                        
                        <div class="btn-group" style="margin-top:12px;">
                            <button type="button" class="btn" 
                                style="background:linear-gradient(135deg,#8844ff,#6622cc);"
                                onclick="previewActualizarUnificado(${id})">
                                👁️ VISTA PREVIA
                            </button>
                            <button type="button" class="btn btn-success" 
                                onclick="confirmarActualizarUnificado(${id})">
                                💾 ACTUALIZAR PARTIDO
                            </button>
                        </div>
                    </div>
                </div>

                <div class="modal-buttons">
                    <button class="btn" onclick="guardarEdicion(${id})">💾 GUARDAR</button>
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">❌ CANCELAR</button>
                </div>
            </div>`;
            document.body.appendChild(overlay);
        })
        .catch(e => alert('❌ ' + e.message));
}


// ============================================================
// RENDER DEL TIMELINE EN EL MODAL DE EDICIÓN
// ============================================================
function renderTimelineEdicion(timeline, localNombre, visitanteNombre) {
    if (!timeline || (!timeline.local && !timeline.visitante)) {
        return '';
    }

    const eventosLocal = timeline.local || [];
    const eventosVisitante = timeline.visitante || [];

    if (eventosLocal.length === 0 && eventosVisitante.length === 0) {
        return '';
    }

    const renderEvento = (ev) => {
        // Icono y color según tipo
        let icono = '•';
        let color = '#8899aa';
        
        if (ev.tipo === 'gol') {
            icono = '⚽';
            color = '#00ff88';
        } else if (ev.tipo === 'gol_penalti') {
            icono = '🎯';
            color = '#00d4ff';
        } else if (ev.tipo === 'og_rival') {
            icono = '🔴';
            color = '#ff4455';
        } else if (ev.tipo === 'penalti_fallado') {
            icono = '❌';
            color = '#ffaa00';
        } else if (ev.tipo === 'tarjeta') {
            icono = '🟨';
            color = '#ffaa00';
        } else if (ev.tipo === 'sustitucion') {
            icono = '🔄';
            color = '#8899aa';
        }

        // Texto del evento
        let texto = '';
        if (ev.tipo === 'gol') {
            texto = `${ev.jugador || '?'}${ev.asistencia ? ` (asist: ${ev.asistencia})` : ''}`;
        } else if (ev.tipo === 'gol_penalti') {
            texto = `${ev.jugador || '?'} (penalti)`;
        } else if (ev.tipo === 'og_rival') {
            texto = `${ev.jugador || '?'} (en propia puerta)`;
        } else if (ev.tipo === 'penalti_fallado') {
            texto = `${ev.jugador || '?'} (penalti fallado)`;
        } else if (ev.tipo === 'tarjeta') {
            texto = ev.jugador || '?';
        } else if (ev.tipo === 'sustitucion') {
            texto = `Sale: ${ev.sale || '?'} → Entra: ${ev.entra || '?'}`;
        } else {
            texto = ev.jugador || ev.raw || '?';
        }

        return `
            <div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #1a2a3a;font-size:0.85em;">
                <span style="color:#8899aa;min-width:45px;font-family:monospace;">${ev.minuto_str || ev.minuto + "'"}</span>
                <span style="min-width:20px;">${icono}</span>
                <span style="color:${color};flex:1;">${texto}</span>
            </div>
        `;
    };

    let html = `
        <div style="background:#0a121c; padding:12px; border-radius:8px; margin-top:15px; border:1px solid #00d4ff44;">
            <h4 style="color:#00d4ff; margin-bottom:12px; font-size:0.9em;">📅 TIMELINE DEL PARTIDO</h4>
            
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                <!-- LOCAL -->
                <div>
                    <p style="color:#00d4ff; font-weight:700; font-size:0.85em; margin-bottom:8px;">🏠 ${localNombre}</p>
                    ${eventosLocal.length > 0 
                        ? eventosLocal.map(renderEvento).join('') 
                        : '<p style="color:#8899aa; font-size:0.8em;">Sin eventos</p>'}
                </div>
                
                <!-- VISITANTE -->
                <div>
                    <p style="color:#ff8844; font-weight:700; font-size:0.85em; margin-bottom:8px;">✈️ ${visitanteNombre}</p>
                    ${eventosVisitante.length > 0 
                        ? eventosVisitante.map(renderEvento).join('') 
                        : '<p style="color:#8899aa; font-size:0.8em;">Sin eventos</p>'}
                </div>
            </div>
        </div>
    `;

    return html;
}

function guardarEdicion(id) {
    const data = {
        fecha: document.getElementById('editFecha').value,
        local: document.getElementById('editLocal').value,
        visitante: document.getElementById('editVisitante').value,
        liga: document.getElementById('editLiga').value,
        og_local: parseInt(document.getElementById('editOgLocal')?.value) || 0,
        og_visitante: parseInt(document.getElementById('editOgVisitante')?.value) || 0
    };
    fetch('/editar/' + id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.querySelector('.modal-overlay').remove();
                cargarHistorico();
            } else { alert('❌ ' + data.error); }
        })
        .catch(e => alert('❌ ' + e.message));
}

// ============================================================
// ACTUALIZAR PARTIDO CON TEXTO UNIFICADO (FASE I)
// ============================================================
function toggleActualizarUnificado(partidoId) {
    const bloque = document.getElementById(`bloqueActualizarUnificado_${partidoId}`);
    const icon = document.getElementById(`toggleActualizarIcon_${partidoId}`);
    
    if (!bloque) return;
    
    if (bloque.style.display === 'none') {
        bloque.style.display = 'block';
        if (icon) icon.textContent = '🔽';
    } else {
        bloque.style.display = 'none';
        if (icon) icon.textContent = '▶️';
    }
}


async function previewActualizarUnificado(partidoId) {
    const texto = document.getElementById(`textoUnificadoActualizar_${partidoId}`)?.value || '';
    const cont = document.getElementById(`previewActualizar_${partidoId}`);
    
    if (!cont) return;
    
    if (!texto.trim()) {
        cont.innerHTML = '<p style="color:#ffaa00;">⚠️ Pega el texto unificado primero.</p>';
        cont.style.display = 'block';
        return;
    }
    
    cont.innerHTML = '<p style="color:#8899aa;">Analizando...</p>';
    cont.style.display = 'block';
    
    try {
        const preview = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ textoUnificado: texto })
        }).then(r => r.json());
        
        if (preview.modo !== 'unificado') {
            cont.innerHTML = '<p style="color:#ff4455;">❌ El texto no está en formato unificado.</p>';
            return;
        }
        
        const resumen = preview.resumen_unificado || {};
        const timeline = preview.timeline || {};
        
        let html = `
            <div style="padding:12px; background:#0a121c; border-radius:6px; border:1px solid #00d4ff44;">
                <h5 style="color:#00d4ff; margin-bottom:8px; font-size:0.9em;">📊 RESUMEN</h5>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:8px; font-size:0.8em;">
                    <div><span style="color:#8899aa;">Jugadores L:</span> <strong>${preview.local.jugadores}</strong></div>
                    <div><span style="color:#8899aa;">Jugadores V:</span> <strong>${preview.visitante.jugadores}</strong></div>
                    <div><span style="color:#8899aa;">Eventos TL:</span> <strong>${timeline.eventos_local}</strong></div>
                    <div><span style="color:#8899aa;">Eventos TV:</span> <strong>${timeline.eventos_visitante}</strong></div>
                    <div><span style="color:#8899aa;">Goles reales:</span> <strong style="color:#00ff88;">${resumen.goles_local_reales || 0} - ${resumen.goles_visitante_reales || 0}</strong></div>
                    <div><span style="color:#8899aa;">OG detectados:</span> <strong style="color:#ffaa00;">${resumen.og_local || 0} / ${resumen.og_visitante || 0}</strong></div>
                </div>
                ${resumen.discrepancia ? `
                    <p style="color:#ffaa00; font-size:0.8em; margin-top:8px;">⚠️ ${resumen.mensaje}</p>
                ` : `
                    <p style="color:#00ff88; font-size:0.8em; margin-top:8px;">✅ Goles cuadran</p>
                `}
            </div>
        `;
        
        cont.innerHTML = html;
        
    } catch (e) {
        cont.innerHTML = `<p style="color:#ff4455;">❌ Error: ${e.message}</p>`;
    }
}


async function confirmarActualizarUnificado(partidoId) {
    const texto = document.getElementById(`textoUnificadoActualizar_${partidoId}`)?.value || '';
    
    if (!texto.trim()) {
        alert('⚠️ Pega el texto unificado primero.');
        return;
    }
    
    if (!confirm('⚠️ ¿Reemplazar las estadísticas de este partido con el nuevo texto?\n\nEl ID se mantiene, pero las stats actuales se borrarán.')) {
        return;
    }
    
    try {
        // Primero intentamos con forzar_guardado=false
        let resultado = await fetch(`/partido/${partidoId}/actualizar-unificado`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ textoUnificado: texto, forzar_guardado: false })
        }).then(r => r.json());
        
        // Si requiere confirmación por advertencias, mostrarlas
        if (resultado.requiere_confirmacion) {
            const confirmar = await mostrarModalAdvertencias(
                {
                    local: { advertencias: resultado.advertencias.slice(0, resultado.local_jugadores), jugadores: resultado.local_jugadores },
                    visitante: { advertencias: resultado.advertencias.slice(resultado.local_jugadores), jugadores: resultado.visitante_jugadores }
                },
                'Local',
                'Visitante'
            );
            
            if (!confirmar) return;
            
            // Reintentar con forzar_guardado=true
            resultado = await fetch(`/partido/${partidoId}/actualizar-unificado`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ textoUnificado: texto, forzar_guardado: true })
            }).then(r => r.json());
        }
        
        if (resultado.error) {
            alert('❌ Error: ' + resultado.error);
            return;
        }
        
        // Éxito
        let msg = `✅ Partido #${resultado.partido_id} actualizado\n\n`;
        msg += `👥 Jugadores: ${resultado.jugadores_local} / ${resultado.jugadores_visitante}\n`;
        msg += `⚽ OG: ${resultado.og_local} / ${resultado.og_visitante}\n`;
        msg += `📅 Timeline: ${resultado.eventos_timeline_local} / ${resultado.eventos_timeline_visitante} eventos\n`;
        msg += `🎯 Goles reales: ${resultado.goles_local_reales} - ${resultado.goles_visitante_reales}\n`;
        
        if (resultado.pronosticos_actualizados && resultado.pronosticos_actualizados.length > 0) {
            msg += `\n🔗 Pronósticos vinculados actualizados: ${resultado.pronosticos_actualizados.length}`;
        }
        
        alert(msg);
        
        // Cerrar modal y recargar histórico
        document.querySelector('.modal-overlay').remove();
        cargarHistorico();
        
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}
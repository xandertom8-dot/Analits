// ============================================================
// static/js/historico/ingesta_unificada.js
// Controla el modo de ingesta (unificado vs antiguo).
// Persiste la elección en localStorage.
// ============================================================

const MODO_INGESTA_KEY = 'analista_modo_ingesta';


// ============================================================
// CAMBIAR MODO
// ============================================================
function cambiarModoIngesta(modo) {
    const btnUnificado = document.getElementById('modoBtnUnificado');
    const btnAntiguo = document.getElementById('modoBtnAntiguo');
    const contUnificado = document.getElementById('modoIngestaUnificado');
    const contAntiguo = document.getElementById('modoIngestaAntiguo');

    if (!btnUnificado || !btnAntiguo) return;

    // Resetear estilos
    [btnUnificado, btnAntiguo].forEach(b => {
        b.className = 'btn btn-secondary';
        b.style.background = '';
    });

    if (modo === 'unificado') {
        btnUnificado.className = 'btn';
        btnUnificado.style.background = 'linear-gradient(135deg,#8844ff,#6622cc)';
        contUnificado.style.display = 'block';
        contAntiguo.style.display = 'none';
    } else {
        btnAntiguo.className = 'btn';
        btnAntiguo.style.background = 'linear-gradient(135deg,#00d4ff,#0088cc)';
        contUnificado.style.display = 'none';
        contAntiguo.style.display = 'block';
    }

    // Guardar preferencia
    try {
        localStorage.setItem(MODO_INGESTA_KEY, modo);
    } catch (e) {
        console.warn('Error guardando modo ingesta:', e);
    }
}


// ============================================================
// INICIALIZAR (al cargar la página)
// ============================================================
function inicializarModoIngesta() {
    let modo = 'unificado'; // Por defecto
    try {
        const stored = localStorage.getItem(MODO_INGESTA_KEY);
        if (stored === 'unificado' || stored === 'antiguo') {
            modo = stored;
        }
    } catch (e) {
        // Ignorar
    }
    cambiarModoIngesta(modo);
}


// ============================================================
// OBTENER MODO ACTUAL
// ============================================================
function modoIngestaActual() {
    try {
        const stored = localStorage.getItem(MODO_INGESTA_KEY);
        if (stored === 'unificado' || stored === 'antiguo') {
            return stored;
        }
    } catch (e) {
        // Ignorar
    }
    return 'unificado';
}


// ============================================================
// ANALIZAR PREVIEW DEL PEGADO UNIFICADO
// ============================================================
async function analizarPegadoUnificado() {
    const textoUnificado = document.getElementById('textoUnificado')?.value || '';
    
    if (!textoUnificado.trim()) {
        const infoCont = document.getElementById('infoTimeline');
        if (infoCont) infoCont.style.display = 'none';
        return;
    }

    // Solo llamar a /preview si el texto parece unificado
    if (!textoUnificado.includes('=====') && !textoUnificado.includes('--- EQUIPO')) {
        return;
    }

    const selLocal = document.getElementById('local');
    const selVisit = document.getElementById('visitante');
    const local = selLocal?.options[selLocal.selectedIndex]?.dataset?.name || 'Local';
    const visitante = selVisit?.options[selVisit.selectedIndex]?.dataset?.name || 'Visitante';

    try {
        const preview = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                textoUnificado: textoUnificado,
                local: local,
                visitante: visitante,
            })
        }).then(r => r.json());

        mostrarInfoPreviewUnificado(preview);
    } catch (e) {
        console.error('Error analizando preview:', e);
    }
}


function mostrarInfoPreviewUnificado(preview) {
    const infoCont = document.getElementById('infoTimeline');
    const content = document.getElementById('infoTimelineContent');
    
    if (!infoCont || !content) return;

    if (preview.modo !== 'unificado') {
        infoCont.style.display = 'none';
        return;
    }

    const resumen = preview.resumen_unificado || {};
    const timeline = preview.timeline || {};

    // Colores según estado
    const colorDiscrepancia = resumen.discrepancia ? '#ffaa00' : '#00ff88';

    let html = `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;">
            <div class="stat-item">
                <span class="label">Jugadores Local</span><br>
                <span class="value" style="font-size:1.2em;">${preview.local.jugadores}</span>
            </div>
            <div class="stat-item">
                <span class="label">Jugadores Visitante</span><br>
                <span class="value" style="font-size:1.2em;">${preview.visitante.jugadores}</span>
            </div>
            <div class="stat-item">
                <span class="label">Eventos Timeline L</span><br>
                <span class="value" style="font-size:1.2em;">${timeline.eventos_local}</span>
            </div>
            <div class="stat-item">
                <span class="label">Eventos Timeline V</span><br>
                <span class="value" style="font-size:1.2em;">${timeline.eventos_visitante}</span>
            </div>
            <div class="stat-item">
                <span class="label">Goles Reales (L-V)</span><br>
                <span class="value" style="font-size:1.2em;color:#00ff88;">${resumen.goles_local_reales || 0} - ${resumen.goles_visitante_reales || 0}</span>
            </div>
            <div class="stat-item">
                <span class="label">OG Detectados (L/V)</span><br>
                <span class="value" style="font-size:1.2em;color:#ffaa00;">${resumen.og_local || 0} / ${resumen.og_visitante || 0}</span>
            </div>
        </div>
    `;

    if (resumen.discrepancia) {
        html += `
            <div style="margin-top:12px; padding:10px; background:#ffaa0022; border-radius:6px; border:1px solid #ffaa0044;">
                <p style="color:#ffaa00; font-size:0.85em; margin:0;">
                    ${resumen.mensaje}
                </p>
                <p style="color:#8899aa; font-size:0.75em; margin-top:6px; margin-bottom:0;">
                    💡 Esto es normal si no pegaste TODOS los jugadores en el texto de prueba. Con el texto real completo no debería aparecer.
                </p>
            </div>
        `;
    } else {
        html += `
            <div style="margin-top:12px; padding:10px; background:#00ff8822; border-radius:6px; border:1px solid #00ff8844;">
                <p style="color:#00ff88; font-size:0.85em; margin:0;">
                    ✅ Goles del timeline cuadran con las estadísticas de jugadores.
                </p>
            </div>
        `;
    }

    content.innerHTML = html;
    infoCont.style.display = 'block';
}


// ============================================================
// AUTO-ANÁLISIS AL PEGAR
// ============================================================
function inicializarAutoAnalisis() {
    const textarea = document.getElementById('textoUnificado');
    if (!textarea) return;

    let timeoutId;
    textarea.addEventListener('paste', () => {
        // Esperar un poco para que el paste se procese
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            analizarPegadoUnificado();
        }, 500);
    });

    textarea.addEventListener('input', () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            analizarPegadoUnificado();
        }, 800);
    });
}
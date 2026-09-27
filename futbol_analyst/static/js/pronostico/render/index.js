// ============================================================
// static/js/pronostico/render/index.js
// Orquestador: decide qué secciones pintar según el mercado.
// ============================================================

function mostrarPronostico(data, mercadoFiltro = 'todos') {
    const container = document.getElementById('resultsContent');
    let html = '';

    // ===== Siempre visibles =====
    html += mostrarSeccionCalidad(data);
    html += mostrarSeccionConfianza(data);

    const mostrarTodo = (mercadoFiltro === 'todos' || mercadoFiltro === 'Valor');

    // ===== GOLES =====
    if (mostrarTodo || mercadoFiltro === '1X2') html += mostrarSeccion1X2(data);
    if (mostrarTodo || mercadoFiltro === 'DobleOportunidad') html += mostrarSeccionDobleOportunidad(data);
    if (mostrarTodo || mercadoFiltro === 'BTTS') html += mostrarSeccionBTTS(data);

    // Over/Under individuales
    if (mercadoFiltro.startsWith('Over_')) {
        const linea = parseFloat(mercadoFiltro.replace('Over_', ''));
        html += mostrarSeccionOverUnder(data, linea);
    } else if (mostrarTodo) {
        html += mostrarSeccionOverUnder(data, 2.5);
        html += mostrarSeccionOverUnder(data, 3.5);
    }

    if (mostrarTodo || mercadoFiltro === 'GolesLocal') html += mostrarSeccionGolesEquipo(data, 'local');
    if (mostrarTodo || mercadoFiltro === 'GolesVisitante') html += mostrarSeccionGolesEquipo(data, 'visitante');
    if (mostrarTodo || mercadoFiltro === 'TopMarcadores') html += mostrarSeccionTopMarcadores(data);

    // ===== CÓRNERS =====
    if (mercadoFiltro === 'Corners') {
        html += mostrarSeccionCorners(data);
    } else if (mercadoFiltro.startsWith('Corners_')) {
        const linea = parseFloat(mercadoFiltro.replace('Corners_', ''));
        html += mostrarSeccionCornersLinea(data, linea);
    } else if (mostrarTodo) {
        html += mostrarSeccionCorners(data);
    }

    // ===== TARJETAS =====
    if (mercadoFiltro === 'Tarjetas') {
        html += mostrarSeccionTarjetas(data);
    } else if (mercadoFiltro.startsWith('Tarjetas_')) {
        const linea = parseFloat(mercadoFiltro.replace('Tarjetas_', ''));
        html += mostrarSeccionTarjetasLinea(data, linea);
    } else if (mostrarTodo) {
        html += mostrarSeccionTarjetas(data);
    }

    // ===== JUGADORES =====
    if (mercadoFiltro === 'Goleadores') {
        html += mostrarSeccionJugadoresPorTipo(data, 'goleadores');
    } else if (mercadoFiltro === 'Porteros') {
        html += mostrarSeccionJugadoresPorTipo(data, 'porteros');
    } else if (mercadoFiltro === 'Tiros') {
        html += mostrarSeccionJugadoresPorTipo(data, 'tiros');
    } else if (mercadoFiltro === 'FaltasJugadores') {
        html += mostrarSeccionJugadoresPorTipo(data, 'faltas');
    } else if (mostrarTodo) {
        html += mostrarSeccionJugadores(data);
    }

    // ===== CONTEXTO (solo en "todos") =====
    if (mercadoFiltro === 'todos') {
        html += mostrarSeccionContexto(data);
        html += mostrarSeccionDistribuciones(data);
        html += mostrarSeccionAnomalias(data);
    }

    // ===== VALOR (siempre al final) =====
    html += mostrarSeccionValor(data, mercadoFiltro);

    container.innerHTML = html;
    document.getElementById('resultsArea').style.display = 'block';
}
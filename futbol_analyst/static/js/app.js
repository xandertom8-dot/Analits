// ============================================================
// static/js/app.js
// Bootstrap de la aplicación.
// Expone al window las funciones usadas desde onclick="" del HTML.
// ============================================================

// ============================================================
// EXPOSICIÓN AL WINDOW (para onclick="..." del HTML)
// ============================================================

// Tabs
window.cambiarTab = cambiarTab;

// Histórico - selectores
window.cargarPaises = cargarPaises;
window.cargarLigas = cargarLigas;
window.cargarTemporadas = cargarTemporadas;
window.cargarEquipos = cargarEquipos;
window.actualizarTitulos = actualizarTitulos;

// Histórico - guardar
window.guardarDatos = guardarDatos;
window.vincularPronostico = vincularPronostico;

// Histórico - listar
window.cargarHistorico = cargarHistorico;
window.toggleFiltrosAvanzados = toggleFiltrosAvanzados;
window.aplicarFiltrosAvanzados = aplicarFiltrosAvanzados;
window.limpiarFiltrosAvanzados = limpiarFiltrosAvanzados;
window.quitarFiltro = quitarFiltro;
window.limpiarFiltrosHistorico = limpiarFiltrosHistorico;
window.irPaginaHistorico = irPaginaHistorico;
window.cambiarPorPaginaHistorico = cambiarPorPaginaHistorico;
window.eliminarPartido = eliminarPartido;
window.confirmarBorrarTodo = confirmarBorrarTodo;
window.editarPartido = editarPartido;
window.guardarEdicion = guardarEdicion;
window.cambiarModoIngesta = cambiarModoIngesta;
window.toggleActualizarUnificado = toggleActualizarUnificado;
window.previewActualizarUnificado = previewActualizarUnificado;
window.confirmarActualizarUnificado = confirmarActualizarUnificado;


// Pronóstico - selectores
window.cargarPaisesPronostico = cargarPaisesPronostico;
window.cargarLigasPronostico = cargarLigasPronostico;
window.cargarTemporadasPronostico = cargarTemporadasPronostico;
window.cargarEquiposPronostico = cargarEquiposPronostico;

// Pronóstico - generar
window.generarPronostico = generarPronostico;
window.guardarPronostico = guardarPronostico;

// Backtesting - pronósticos
window.cargarPronosticos = cargarPronosticos;
window.abrirModalResultado = abrirModalResultado;
window.cargarLigasModal = cargarLigasModal;
window.cargarTemporadasModal = cargarTemporadasModal;
window.toggleEstadisticasModal = toggleEstadisticasModal;
window.confirmarResultado = confirmarResultado;
window.cerrarConApi = cerrarConApi;
window.probarApiExterna = probarApiExterna;
window.generarAutomaticos = generarAutomaticos;
window.editarPronostico = editarPronostico;
window.guardarEdicionPronostico = guardarEdicionPronostico;
window.eliminarPronostico = eliminarPronostico;
window.borrarTodosPronosticos = borrarTodosPronosticos;
// Backtesting - métricas
window.cargarBacktesting = cargarBacktesting;

// Pronóstico - Kelly config
window.aplicarKellyConfig = aplicarKellyConfig;

// ============================================================
// INICIALIZACIÓN
// ============================================================
window.addEventListener('DOMContentLoaded', async function () {
    await cargarContinentes();
    cargarHistorico();
    actualizarTitulos();

    // Event listener adicional para temporada de pronóstico
    const selTemp = document.getElementById('pronosticoTemporada');
    if (selTemp) selTemp.addEventListener('change', cargarEquiposPronostico);

    // ========== NUEVO: inicializar modo ingesta ==========
    inicializarModoIngesta();
    inicializarAutoAnalisis();
});
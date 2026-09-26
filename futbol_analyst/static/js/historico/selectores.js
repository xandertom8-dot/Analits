// ============================================================
// static/js/historico/selectores.js
// Selects en cascada del modo HISTÓRICO:
// Continente → País → Liga → Temporada → Equipos
// ============================================================

async function cargarContinentes() {
    try {
        const continentes = await apiGet('/api/continentes');
        llenarSelect(document.getElementById('continente'), continentes, 'Selecciona un continente');
        llenarSelect(document.getElementById('pronosticoContinente'), continentes, 'Selecciona un continente');
    } catch (e) {
        console.error(e);
    }
}

async function cargarPaises() {
    const continente = document.getElementById('continente').value;
    if (!continente) return;
    try {
        const paises = await apiGet(`/api/paises?continente=${encodeURIComponent(continente)}`);
        llenarSelect(document.getElementById('pais'), paises, 'Selecciona un país');
        document.getElementById('liga').innerHTML = '<option value="">Selecciona una liga</option>';
        document.getElementById('temporada').innerHTML = '<option value="">Selecciona una temporada</option>';
        document.getElementById('local').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('visitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarLigas() {
    const continente = document.getElementById('continente').value;
    const pais = document.getElementById('pais').value;
    if (!continente || !pais) return;
    try {
        const ligas = await apiGet(`/api/ligas?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}`);
        llenarSelect(document.getElementById('liga'), ligas, 'Selecciona una liga');
        document.getElementById('temporada').innerHTML = '<option value="">Selecciona una temporada</option>';
        document.getElementById('local').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('visitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarTemporadas() {
    const continente = document.getElementById('continente').value;
    const pais = document.getElementById('pais').value;
    const liga = document.getElementById('liga').value;
    if (!continente || !pais || !liga) return;
    try {
        const temporadas = await apiGet(`/api/temporadas?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}&liga=${encodeURIComponent(liga)}`);
        llenarSelect(document.getElementById('temporada'), temporadas, 'Selecciona una temporada');
        document.getElementById('local').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('visitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarEquipos() {
    const continente = document.getElementById('continente').value;
    const pais = document.getElementById('pais').value;
    const liga = document.getElementById('liga').value;
    const temporada = document.getElementById('temporada').value;
    if (!continente || !pais || !liga || !temporada) return;

    try {
        const equipos = await apiGet(`/api/equipos-con-id?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}&liga=${encodeURIComponent(liga)}&temporada=${encodeURIComponent(temporada)}`);

        const selectLocal = document.getElementById('local');
        const selectVisit = document.getElementById('visitante');
        llenarSelectConId(selectLocal, equipos, 'Selecciona equipo local');
        llenarSelectConId(selectVisit, equipos, 'Selecciona equipo visitante');
    } catch (e) {
        console.error(e);
    }
}

function actualizarTitulos() {
    const selLocal = document.getElementById('local');
    const selVisit = document.getElementById('visitante');
    const localNombre = selLocal.options[selLocal.selectedIndex]?.dataset?.name || '';
    const visitNombre = selVisit.options[selVisit.selectedIndex]?.dataset?.name || '';

    document.getElementById('tituloLocal').textContent = localNombre ? '🏠 ' + localNombre + ' (LOCAL)' : '🏠 ESTADÍSTICAS DEL LOCAL';
    document.getElementById('tituloVisitante').textContent = visitNombre ? '✈️ ' + visitNombre + ' (VISITANTE)' : '✈️ ESTADÍSTICAS DEL VISITANTE';
}
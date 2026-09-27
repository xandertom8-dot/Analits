// ============================================================
// static/js/pronostico/selectores.js
// Selects en cascada del modo PRONÓSTICO:
// Continente → País → Liga → Temporada → Equipos
// ============================================================

async function cargarPaisesPronostico() {
    const continente = document.getElementById('pronosticoContinente').value;
    if (!continente) return;
    try {
        const paises = await apiGet(`/api/paises?continente=${encodeURIComponent(continente)}`);
        llenarSelect(document.getElementById('pronosticoPais'), paises, 'Selecciona un país');
        document.getElementById('pronosticoLiga').innerHTML = '<option value="">Selecciona una liga</option>';
        document.getElementById('pronosticoTemporada').innerHTML = '<option value="">Selecciona una temporada</option>';
        document.getElementById('pronosticoLocal').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('pronosticoVisitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarLigasPronostico() {
    const continente = document.getElementById('pronosticoContinente').value;
    const pais = document.getElementById('pronosticoPais').value;
    if (!continente || !pais) return;
    try {
        const ligas = await apiGet(`/api/ligas?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}`);
        llenarSelect(document.getElementById('pronosticoLiga'), ligas, 'Selecciona una liga');
        document.getElementById('pronosticoTemporada').innerHTML = '<option value="">Selecciona una temporada</option>';
        document.getElementById('pronosticoLocal').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('pronosticoVisitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarTemporadasPronostico() {
    const continente = document.getElementById('pronosticoContinente').value;
    const pais = document.getElementById('pronosticoPais').value;
    const liga = document.getElementById('pronosticoLiga').value;
    if (!continente || !pais || !liga) return;
    try {
        const temporadas = await apiGet(`/api/temporadas?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}&liga=${encodeURIComponent(liga)}`);
        llenarSelect(document.getElementById('pronosticoTemporada'), temporadas, 'Selecciona una temporada');
        document.getElementById('pronosticoLocal').innerHTML = '<option value="">Selecciona equipo local</option>';
        document.getElementById('pronosticoVisitante').innerHTML = '<option value="">Selecciona equipo visitante</option>';
    } catch (e) {
        console.error(e);
    }
}

async function cargarEquiposPronostico() {
    const continente = document.getElementById('pronosticoContinente').value;
    const pais = document.getElementById('pronosticoPais').value;
    const liga = document.getElementById('pronosticoLiga').value;
    const temporada = document.getElementById('pronosticoTemporada').value;
    if (!continente || !pais || !liga || !temporada) return;

    try {
        const equipos = await apiGet(`/api/equipos-con-id?continente=${encodeURIComponent(continente)}&pais=${encodeURIComponent(pais)}&liga=${encodeURIComponent(liga)}&temporada=${encodeURIComponent(temporada)}`);

        const selectLocal = document.getElementById('pronosticoLocal');
        const selectVisit = document.getElementById('pronosticoVisitante');
        llenarSelectConId(selectLocal, equipos, 'Selecciona equipo local');
        llenarSelectConId(selectVisit, equipos, 'Selecciona equipo visitante');
    } catch (e) {
        console.error(e);
    }
}
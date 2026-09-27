// ============================================================
// static/js/pronostico/generar.js
// Generar pronóstico + guardarlo para backtesting.
// ============================================================

async function generarPronostico() {
    const selLocal = document.getElementById('pronosticoLocal');
    const selVisit = document.getElementById('pronosticoVisitante');
    const local = selLocal.options[selLocal.selectedIndex]?.dataset?.name || '';
    const visitante = selVisit.options[selVisit.selectedIndex]?.dataset?.name || '';
    const cuota = parseFloat(document.getElementById('pronosticoCuotaReal').value) || 0;
    const mercado = document.getElementById('pronosticoMercadoPrincipal').value;

    if (!local || !visitante) { alert('Selecciona ambos equipos.'); return; }
    if (local === visitante) { alert('No pueden ser el mismo equipo.'); return; }

    document.getElementById('resultsArea').style.display = 'block';
    document.getElementById('resultsContent').innerHTML = '<div class="loading">Generando pronóstico</div>';

    try {
        // Leer configuración de Kelly
        const kellyConfig = cargarKellyConfig();

        const data = await fetch('/pronosticar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                local, visitante, cuota, mercado,
                bankroll: kellyConfig.bankroll,
                stake_minimo: kellyConfig.stakeMinimo
            })
        }).then(r => r.json());

        if (data.error) {
            document.getElementById('resultsContent').innerHTML = `<div class="alert alert-warning">❌ ${data.error}</div>`;
            return;
        }

        // Guardar el pronóstico completo en variable global
        window.ultimoPronostico = data;

        // Actualizar el campo "Mercado a guardar"
        const mercadoLabel = document.getElementById('pronosticoMercadoPrincipal').options[
            document.getElementById('pronosticoMercadoPrincipal').selectedIndex
        ].textContent;
        document.getElementById('pronosticoMercadoGuardar').value = mercadoLabel;

        // Mostrar según el mercado seleccionado
        mostrarPronostico(data, mercado);

    } catch (error) {
        document.getElementById('resultsContent').innerHTML = `<div class="alert alert-error">❌ Error: ${error.message}</div>`;
    }
}

// ============================================================
// GUARDAR PRONÓSTICO PARA BACKTESTING
// ============================================================
async function guardarPronostico() {
    const selLocal = document.getElementById('pronosticoLocal');
    const selVisit = document.getElementById('pronosticoVisitante');
    const local = selLocal.options[selLocal.selectedIndex]?.dataset?.name || '';
    const visitante = selVisit.options[selVisit.selectedIndex]?.dataset?.name || '';
    const liga = document.getElementById('pronosticoLiga').value || '';
    const cuotaReal = parseFloat(document.getElementById('pronosticoCuotaReal').value) || 0;
    const mercadoSeleccionado = document.getElementById('pronosticoMercadoPrincipal').value;

    if (!local || !visitante) {
        alert('Primero genera un pronóstico.');
        return;
    }

    if (!window.ultimoPronostico) {
        alert('⚠️ Primero genera el pronóstico antes de guardarlo.');
        return;
    }

    const mapeoMercados = {
        '1X2': 'Local',
        'BTTS': 'BTTS',
        'Over_2.5': 'Over25',
        'Over_3.5': 'Over35',
        'Corners': 'Corners',
        'Tarjetas': 'Tarjetas',
        'todos': 'Local',
    };

    const mercadoPrincipal = mapeoMercados[mercadoSeleccionado] || 'Local';

    // ========== Extraer stake sugerido ==========
    const kellyConfig = cargarKellyConfig();
    const fraccionLabel = kellyConfig.fraccionLabel || 'cuarto';

    let stakeSugerido = null;

    // Buscar el value bet correspondiente al mercado principal
    const valorBets = window.ultimoPronostico.valor || [];
    const betEncontrada = valorBets.find(v => {
        if (mercadoPrincipal === 'Local') return v.mercado === '1X2 - Local';
        if (mercadoPrincipal === 'Empate') return v.mercado === '1X2 - Empate';
        if (mercadoPrincipal === 'Visitante') return v.mercado === '1X2 - Visitante';
        if (mercadoPrincipal === 'BTTS') return v.mercado.includes('BTTS');
        if (mercadoPrincipal === 'Over25') return v.mercado === 'Over 2.5';
        if (mercadoPrincipal === 'Over35') return v.mercado === 'Over 3.5';
        return false;
    });

    if (betEncontrada && betEncontrada.kelly && betEncontrada.kelly[fraccionLabel]) {
        stakeSugerido = betEncontrada.kelly[fraccionLabel].stake_dinero;
    }

    try {
        const resultado = await fetch('/api/pronosticos/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                local, visitante, liga,
                cuota_real: cuotaReal,
                mercado_principal: mercadoPrincipal,
                pronostico: window.ultimoPronostico,
                stake_sugerido: stakeSugerido,
                kelly_fraccion: kellyConfig.fraccion,
                bankroll_usado: kellyConfig.bankroll,
                stake_minimo_usado: kellyConfig.stakeMinimo,
            })
        }).then(r => r.json());

        if (resultado.success) {
            let msg = `✅ Pronóstico guardado (ID: ${resultado.id})\nMercado: ${mercadoPrincipal}`;
            if (stakeSugerido !== null) {
                msg += `\n💰 Stake sugerido: ${stakeSugerido.toFixed(0)} COP (Kelly ${fraccionLabel})`;
            }
            alert(msg);
        } else {
            alert('❌ Error: ' + (resultado.error || 'Desconocido'));
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}
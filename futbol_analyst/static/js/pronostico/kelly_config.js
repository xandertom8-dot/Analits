// ============================================================
// static/js/pronostico/kelly_config.js
// Configuración de Kelly: bankroll + fracción.
// Persiste en localStorage.
// ============================================================

const KELLY_STORAGE_KEY = 'analista_kelly_config';

const KELLY_DEFAULTS = {
    bankroll: 10000,
    fraccion: 0.25,
    fraccionLabel: 'cuarto',
    stakeMinimo: 500,
};


// ============================================================
// CARGAR CONFIG
// ============================================================
function cargarKellyConfig() {
    try {
        const stored = localStorage.getItem(KELLY_STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            return {
                bankroll: parsed.bankroll || KELLY_DEFAULTS.bankroll,
                fraccion: parsed.fraccion || KELLY_DEFAULTS.fraccion,
                fraccionLabel: parsed.fraccionLabel || KELLY_DEFAULTS.fraccionLabel,
                stakeMinimo: parsed.stakeMinimo ?? KELLY_DEFAULTS.stakeMinimo,
            };
        }
    } catch (e) {
        console.warn('Error leyendo config Kelly:', e);
    }
    return { ...KELLY_DEFAULTS };
}


// ============================================================
// GUARDAR CONFIG
// ============================================================
function guardarKellyConfig(config) {
    try {
        localStorage.setItem(KELLY_STORAGE_KEY, JSON.stringify(config));
    } catch (e) {
        console.warn('Error guardando config Kelly:', e);
    }
}


// ============================================================
// MAPEAR FRACCIÓN A ETIQUETA
// ============================================================
function fraccionALabel(fraccion) {
    if (fraccion === 1.0) return 'completo';
    if (fraccion === 0.5) return 'medio';
    if (fraccion === 0.25) return 'cuarto';
    if (fraccion === 0.125) return 'octavo';
    return 'cuarto';
}


// ============================================================
// APLICAR CONFIG (llamado desde el botón)
// ============================================================
function aplicarKellyConfig() {
    const bankrollEl = document.getElementById('kellyBankroll');
    const fraccionEl = document.getElementById('kellyFraccion');
    const stakeMinimoEl = document.getElementById('kellyStakeMinimo');

    if (!bankrollEl || !fraccionEl) return;

    const bankroll = parseFloat(bankrollEl.value) || KELLY_DEFAULTS.bankroll;
    const fraccion = parseFloat(fraccionEl.value) || KELLY_DEFAULTS.fraccion;
    const stakeMinimo = stakeMinimoEl ? (parseFloat(stakeMinimoEl.value) || 0) : KELLY_DEFAULTS.stakeMinimo;

    const config = {
        bankroll: bankroll,
        fraccion: fraccion,
        fraccionLabel: fraccionALabel(fraccion),
        stakeMinimo: stakeMinimo,
    };

    guardarKellyConfig(config);

    // Recalcular pronóstico si ya hay uno generado
    if (window.ultimoPronostico) {
        generarPronostico();
    } else {
        alert('✅ Configuración guardada. Genera un pronóstico para ver el efecto.');
    }
}


// ============================================================
// INICIALIZAR PANEL (rellenar inputs con la config guardada)
// ============================================================
function inicializarKellyPanel() {
    const config = cargarKellyConfig();

    const bankrollEl = document.getElementById('kellyBankroll');
    const fraccionEl = document.getElementById('kellyFraccion');
    const stakeMinimoEl = document.getElementById('kellyStakeMinimo');

    if (bankrollEl) bankrollEl.value = config.bankroll;
    if (fraccionEl) fraccionEl.value = config.fraccion;
    if (stakeMinimoEl) stakeMinimoEl.value = config.stakeMinimo;
}
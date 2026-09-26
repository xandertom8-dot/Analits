// ============================================================
// static/js/tabs.js
// Gestión de pestañas: Histórico / Pronóstico / Backtesting.
// ============================================================

function cambiarTab(tab) {
    const tabHistorico = document.getElementById('tabHistorico');
    const tabPronostico = document.getElementById('tabPronostico');
    const tabBacktesting = document.getElementById('tabBacktesting');
    const modoHistorico = document.getElementById('modoHistorico');
    const modoPronostico = document.getElementById('modoPronostico');
    const modoBacktesting = document.getElementById('modoBacktesting');

    modoHistorico.style.display = 'none';
    modoPronostico.style.display = 'none';
    modoBacktesting.style.display = 'none';

    [tabHistorico, tabPronostico, tabBacktesting].forEach(b => {
        if (b) { b.className = 'btn btn-secondary'; b.style.background = ''; }
    });

    if (tab === 'historico') {
        tabHistorico.className = 'btn';
        tabHistorico.style.background = 'linear-gradient(135deg,#00d4ff,#0088cc)';
        modoHistorico.style.display = 'block';
    } else if (tab === 'pronostico') {
        tabPronostico.className = 'btn';
        tabPronostico.style.background = 'linear-gradient(135deg,#ff8844,#cc6600)';
        modoPronostico.style.display = 'block';
    } else if (tab === 'backtesting') {
        tabBacktesting.className = 'btn';
        tabBacktesting.style.background = 'linear-gradient(135deg,#00ff88,#00cc66)';
        modoBacktesting.style.display = 'block';
    }
}
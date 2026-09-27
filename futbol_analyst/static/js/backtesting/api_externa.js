// ============================================================
// static/js/backtesting/api_externa.js
// Cierre automático de pronósticos usando Football-Data.org.
// ============================================================

async function cerrarConApi() {
    if (!confirm('🌐 ¿Buscar y cerrar pronósticos abiertos automáticamente con Football-Data.org?')) {
        return;
    }

    // Mostrar loading
    const container = document.getElementById('listaPronosticos');
    const originalHtml = container.innerHTML;
    container.innerHTML = '<p style="color:#8899aa;">🌐 Consultando API externa...</p>';

    try {
        const resultado = await fetch('/api/pronosticos/cerrar-con-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limite: 10, dias_atras: 7 })
        }).then(r => r.json());

        if (resultado.error) {
            alert('❌ Error: ' + resultado.error);
            container.innerHTML = originalHtml;
            return;
        }

        // Construir mensaje
        let msg = `🌐 Resultado del cierre automático:\n\n`;
        msg += `📊 Procesados: ${resultado.total_procesados || 0}\n`;
        msg += `✅ Cerrados: ${resultado.total_cerrados || 0}\n`;
        msg += `🔍 No encontrados: ${(resultado.no_encontrados || []).length}\n`;
        msg += `⚠️ Errores: ${(resultado.errores || []).length}\n`;

        if ((resultado.cerrados || []).length > 0) {
            msg += `\n✅ CERRADOS:\n`;
            for (const c of resultado.cerrados) {
                msg += `  · #${c.id} ${c.local} ${c.goles_local}-${c.goles_visitante} ${c.visitante}\n`;
            }
        }

        if ((resultado.no_encontrados || []).length > 0) {
            msg += `\n🔍 NO ENCONTRADOS:\n`;
            for (const n of resultado.no_encontrados.slice(0, 5)) {
                msg += `  · #${n.id} ${n.local} vs ${n.visitante} (${n.razon})\n`;
            }
        }

        alert(msg);

        // Refrescar lista y métricas
        cargarPronosticos();
        cargarBacktesting();

    } catch (e) {
        alert('❌ Error: ' + e.message);
        container.innerHTML = originalHtml;
    }
}


async function probarApiExterna() {
    try {
        const resultado = await fetch('/api/externo/test').then(r => r.json());

        if (resultado.ok) {
            alert('✅ ' + resultado.mensaje);
        } else {
            alert('❌ ' + resultado.mensaje);
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

async function generarAutomaticos() {
    if (!confirm('🤖 ¿Generar pronósticos automáticos para los próximos partidos?\n\nSe consultará la API y se crearán pronósticos para los equipos con datos suficientes.')) {
        return;
    }

    const container = document.getElementById('listaPronosticos');
    const originalHtml = container.innerHTML;
    container.innerHTML = '<p style="color:#8899aa;">🤖 Consultando API y generando pronósticos...<br><span style="font-size:0.8em;">(Puede tardar 30-60 segundos por el rate limit)</span></p>';

    try {
        const resultado = await fetch('/api/pronosticos/generar-automaticos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dias: 7,
                min_partidos: 5,
                dry_run: false,
            })
        }).then(r => r.json());

        if (resultado.error) {
            alert('❌ Error: ' + resultado.error);
            container.innerHTML = originalHtml;
            return;
        }

        let msg = `🤖 Resultado:\n\n`;
        msg += `📊 Partidos en API: ${resultado.total_partidos_api || 0}\n`;
        msg += `✅ Generados: ${resultado.total_generados || 0}\n`;
        msg += `⏭️ Saltados: ${resultado.total_saltados || 0}\n`;
        msg += `⚠️ Errores: ${resultado.total_errores || 0}\n`;

        if ((resultado.generados || []).length > 0) {
            msg += `\n✅ GENERADOS (primeros 10):\n`;
            for (const g of resultado.generados.slice(0, 10)) {
                msg += `  · #${g.id} ${g.local} vs ${g.visitante} (${g.fecha})\n`;
            }
        }

        if ((resultado.saltados || []).length > 0) {
            msg += `\n⏭️ SALTADOS (primeros 5):\n`;
            for (const s of resultado.saltados.slice(0, 5)) {
                msg += `  · ${s.local} vs ${s.visitante}: ${s.razon}\n`;
            }
        }

        alert(msg);

        cargarPronosticos();
        cargarBacktesting();

    } catch (e) {
        alert('❌ Error: ' + e.message);
        container.innerHTML = originalHtml;
    }
}
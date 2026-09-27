"""
BACKTESTING DE MODIFICADORES (FASE A) - v2 optimizado

Optimizaciones vs v1:
- Caché por (liga, fecha_corte) que se reutiliza entre partidos del mismo día.
- Limpieza de caché solo cuando cambia el día.
- Logging opcional de negbin/dixon_coles.
- Guardado de resultados en archivo.
"""

import os
import sys
import time
import math
import json
from datetime import datetime, timedelta
from collections import defaultdict

from database.motor_estadistico import (
    calcular_lambda_poisson,
    obtener_partidos_historicos,
    set_modificador,
    reset_modificadores,
    _CACHE_LOCALIA_LIGA,
    _CACHE_RHO_LIGA,
)
import database.motor_estadistico as motor


# ============================================================
# CONFIGURACIÓN
# ============================================================
MIN_PARTIDOS = 5
N_PARTIDOS = 500
LIGAS_FILTRO = None
VERBOSE = False
GUARDAR_RESULTADOS = True

MODIFICADORES_A_PROBAR = [
    'decay', 'suavizado', 'localia_generica', 'localia_empirica',
    'localia_liga', 'tendencia', 'racha', 'racha_v2',
    'ratio', 'diferencial', 'peso_competicion', 'peso_rival',
    'negbin', 'dixon_coles', 'aprendizaje_sesgo',
]


# ============================================================
# CARGA DE PARTIDOS
# ============================================================
def cargar_partidos_prueba(limite=500):
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'football.db')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        where = []
        params = []
        if LIGAS_FILTRO:
            placeholders = ','.join('?' * len(LIGAS_FILTRO))
            where.append(f'p.liga IN ({placeholders})')
            params.extend(LIGAS_FILTRO)
        
        where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
        
        c.execute(f'''
            SELECT 
                p.id, p.fecha, p.local, p.visitante, p.liga,
                (SELECT SUM(G) FROM estadisticas_local WHERE partido_id = p.id) as goles_local,
                (SELECT SUM(G) FROM estadisticas_visitante WHERE partido_id = p.id) as goles_visitante,
                COALESCE(p.og_local, 0) as og_local,
                COALESCE(p.og_visitante, 0) as og_visitante
            FROM partidos p
            {where_sql}
            ORDER BY p.fecha DESC
            LIMIT ?
        ''', params + [limite])
        
        partidos = []
        for row in c.fetchall():
            goles_local = (row['goles_local'] or 0) + row['og_visitante']
            goles_visitante = (row['goles_visitante'] or 0) + row['og_local']
            
            partidos.append({
                'id': row['id'],
                'fecha': row['fecha'],
                'local': row['local'],
                'visitante': row['visitante'],
                'liga': row['liga'],
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
            })
        
        return partidos
    finally:
        conn.close()


# ============================================================
# SIMULACIÓN CON CACHÉ OPTIMIZADA
# ============================================================
class SimuladorConCache:
    """
    Simulador que mantiene las cachés del motor entre partidos del mismo día.
    """
    def __init__(self):
        self.ultima_fecha = None
        self.stats_cache_hits = 0
        self.stats_cache_misses = 0
    
    def simular(self, partido):
        """Simula un partido, limpiando caché solo si cambió la fecha."""
        try:
            fecha_dt = datetime.strptime(partido['fecha'], '%Y-%m-%d').date()
            fecha_corte = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        except Exception:
            return {'saltado': True, 'razon': 'fecha inválida'}
        
        # Limpiar caché si cambió la fecha
        if self.ultima_fecha != fecha_corte:
            _CACHE_LOCALIA_LIGA.clear()
            _CACHE_RHO_LIGA.clear()
            self.ultima_fecha = fecha_corte
            self.stats_cache_misses += 1
        else:
            self.stats_cache_hits += 1
        
        # Verificar partidos
        partidos_local = obtener_partidos_historicos(
            partido['local'], como_local=None, liga_pronostico=partido['liga'],
            limite=MIN_PARTIDOS, fecha_corte=fecha_corte
        )
        partidos_visitante = obtener_partidos_historicos(
            partido['visitante'], como_local=None, liga_pronostico=partido['liga'],
            limite=MIN_PARTIDOS, fecha_corte=fecha_corte
        )
        
        if len(partidos_local) < MIN_PARTIDOS:
            return {'saltado': True, 'razon': f'{partido["local"]}: {len(partidos_local)} partidos'}
        if len(partidos_visitante) < MIN_PARTIDOS:
            return {'saltado': True, 'razon': f'{partido["visitante"]}: {len(partidos_visitante)} partidos'}
        
        try:
            r_local = calcular_lambda_poisson(
                partido['local'], partido['visitante'],
                como_local=True, liga_pronostico=partido['liga'],
                fecha_corte=fecha_corte
            )
            r_visitante = calcular_lambda_poisson(
                partido['visitante'], partido['local'],
                como_local=False, liga_pronostico=partido['liga'],
                fecha_corte=fecha_corte
            )
        except Exception as e:
            return {'saltado': True, 'razon': f'error motor: {str(e)[:80]}'}
        
        if r_local.get('error') or r_visitante.get('error'):
            return {'saltado': True, 'razon': 'error λ'}
        
        lam_local = r_local['lambda']
        lam_visitante = r_visitante['lambda']
        
        goles_local = partido['goles_local']
        goles_visitante = partido['goles_visitante']
        
        return {
            'lambda_local': lam_local,
            'lambda_visitante': lam_visitante,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'error_local': abs(lam_local - goles_local),
            'error_visitante': abs(lam_visitante - goles_visitante),
            'error_total': abs((lam_local + lam_visitante) - (goles_local + goles_visitante)),
            'saltado': False,
        }


# ============================================================
# BACKTESTING COMPLETO
# ============================================================
def backtest_configuracion(partidos):
    simulador = SimuladorConCache()
    
    errores_local = []
    errores_visitante = []
    errores_total = []
    saltados = 0
    saltados_razones = defaultdict(int)
    
    t0 = time.time()
    for i, partido in enumerate(partidos):
        resultado = simulador.simular(partido)
        
        if resultado['saltado']:
            saltados += 1
            razon_corta = resultado.get('razon', 'desconocida').split(':')[0]
            saltados_razones[razon_corta] += 1
            continue
        
        errores_local.append(resultado['error_local'])
        errores_visitante.append(resultado['error_visitante'])
        errores_total.append(resultado['error_total'])
        
        if VERBOSE and (i+1) % 50 == 0:
            print(f"  [{i+1}/{len(partidos)}] {time.time()-t0:.0f}s")
    
    n = len(errores_local)
    
    if n == 0:
        return {
            'total_evaluados': 0, 'total_saltados': saltados,
            'mae_local': None, 'mae_visitante': None, 'mae_total': None,
            'rmse_local': None, 'rmse_visitante': None, 'rmse_total': None,
            'cache_hits': simulador.stats_cache_hits,
            'cache_misses': simulador.stats_cache_misses,
            'tiempo_seg': time.time() - t0,
        }
    
    def mae(arr): return sum(arr) / len(arr)
    def rmse(arr): return math.sqrt(sum(e ** 2 for e in arr) / len(arr))
    
    return {
        'total_evaluados': n,
        'total_saltados': saltados,
        'mae_local': round(mae(errores_local), 4),
        'mae_visitante': round(mae(errores_visitante), 4),
        'mae_total': round(mae(errores_total), 4),
        'rmse_local': round(rmse(errores_local), 4),
        'rmse_visitante': round(rmse(errores_visitante), 4),
        'rmse_total': round(rmse(errores_total), 4),
        'cache_hits': simulador.stats_cache_hits,
        'cache_misses': simulador.stats_cache_misses,
        'tiempo_seg': round(time.time() - t0, 1),
    }


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("BACKTESTING DE MODIFICADORES (FASE A) - v2 optimizado")
    print("=" * 70)
    print()
    
    print(f"Cargando hasta {N_PARTIDOS} partidos...")
    partidos = cargar_partidos_prueba(limite=N_PARTIDOS)
    print(f"Total partidos cargados: {len(partidos)}")
    print()
    
    if not partidos:
        print("❌ No hay partidos.")
        return
    
    # ========== BASE ==========
    print("-" * 70)
    print("BASE (todos activos)")
    print("-" * 70)
    
    reset_modificadores()
    resultado_base = backtest_configuracion(partidos)
    
    print(f"Evaluados: {resultado_base['total_evaluados']} | Saltados: {resultado_base['total_saltados']}")
    print(f"MAE total: {resultado_base['mae_total']} | RMSE: {resultado_base['rmse_total']}")
    print(f"Cache hits: {resultado_base['cache_hits']} | misses: {resultado_base['cache_misses']}")
    print(f"Tiempo: {resultado_base['tiempo_seg']}s")
    print()
    
    if resultado_base['total_evaluados'] == 0:
        print("❌ Sin partidos evaluables.")
        return
    
    # ========== ANÁLISIS POR MODIFICADOR ==========
    print("=" * 70)
    print("ANÁLISIS POR MODIFICADOR")
    print("=" * 70)
    print()
    print(f"{'Modificador':<25} {'MAE total':>10} {'Δ MAE':>10} {'Veredicto':>15} {'Tiempo':>8}")
    print("-" * 70)
    
    resultados_por_modificador = {}
    
    for mod in MODIFICADORES_A_PROBAR:
        reset_modificadores()
        set_modificador(mod, False)
        
        resultado = backtest_configuracion(partidos)
        
        if resultado['mae_total'] is None:
            continue
        
        delta = resultado['mae_total'] - resultado_base['mae_total']
        
        if delta > 0.01:
            veredicto = "✅ APORTA"
        elif delta < -0.01:
            veredicto = "❌ PERJUDICA"
        else:
            veredicto = "⚪ NEUTRO"
        
        resultados_por_modificador[mod] = {
            'mae_total': resultado['mae_total'],
            'rmse_total': resultado['rmse_total'],
            'delta_mae': round(delta, 4),
            'veredicto': veredicto,
            'tiempo_seg': resultado['tiempo_seg'],
        }
        
        print(f"{mod:<25} {resultado['mae_total']:>10.4f} {delta:>+10.4f} {veredicto:>15} {resultado['tiempo_seg']:>7.0f}s")
    
    reset_modificadores()
    
    # ========== RESUMEN ==========
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print()
    print(f"MAE base: {resultado_base['mae_total']}")
    print()
    
    aportan = [m for m, r in resultados_por_modificador.items() if r['veredicto'] == "✅ APORTA"]
    perjudican = [m for m, r in resultados_por_modificador.items() if r['veredicto'] == "❌ PERJUDICA"]
    neutros = [m for m, r in resultados_por_modificador.items() if r['veredicto'] == "⚪ NEUTRO"]
    
    print(f"✅ APORTAN ({len(aportan)}):")
    for m in aportan:
        print(f"   {m}: Δ = {resultados_por_modificador[m]['delta_mae']:+.4f}")
    print()
    print(f"❌ PERJUDICAN ({len(perjudican)}):")
    for m in perjudican:
        print(f"   {m}: Δ = {resultados_por_modificador[m]['delta_mae']:+.4f}")
    print()
    print(f"⚪ NEUTROS ({len(neutros)}):")
    for m in neutros:
        print(f"   {m}: Δ = {resultados_por_modificador[m]['delta_mae']:+.4f}")
    print()
    
    # ========== GUARDAR ==========
    if GUARDAR_RESULTADOS:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo = f'backtest_resultados_{timestamp}.txt'
        
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write("BACKTESTING MODIFICADORES (FASE A) v2\n")
            f.write("=" * 70 + "\n")
            f.write(f"Fecha: {datetime.now().isoformat()}\n")
            f.write(f"Partidos cargados: {len(partidos)}\n")
            f.write(f"MIN_PARTIDOS: {MIN_PARTIDOS}\n")
            f.write(f"N_PARTIDOS: {N_PARTIDOS}\n\n")
            
            f.write("--- BASE ---\n")
            f.write(f"Evaluados: {resultado_base['total_evaluados']}\n")
            f.write(f"MAE total: {resultado_base['mae_total']}\n")
            f.write(f"RMSE total: {resultado_base['rmse_total']}\n")
            f.write(f"Tiempo: {resultado_base['tiempo_seg']}s\n\n")
            
            f.write("--- POR MODIFICADOR ---\n")
            for mod, r in resultados_por_modificador.items():
                f.write(f"{mod}: MAE={r['mae_total']} Δ={r['delta_mae']:+.4f} {r['veredicto']}\n")
            
            f.write("\n--- RESUMEN ---\n")
            f.write(f"APORTAN: {aportan}\n")
            f.write(f"PERJUDICAN: {perjudican}\n")
            f.write(f"NEUTROS: {neutros}\n")
        
        print(f"📄 Resultados guardados en: {archivo}")


if __name__ == '__main__':
    main()
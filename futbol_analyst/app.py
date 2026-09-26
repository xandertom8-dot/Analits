# ============================================================
# app.py — Analista de Fútbol
# Punto de entrada. Solo bootstrap: crea Flask, registra
# Blueprints y arranca el servidor.
# Toda la lógica vive en backend/ y database/.
# ============================================================

import os
import sys

from flask import Flask, render_template


# ============================================================
# RUTA DEL PROYECTO (debe ir ANTES de cualquier import del proyecto)
# ============================================================
PROYECTO_PATH = os.path.dirname(os.path.abspath(__file__))
if PROYECTO_PATH not in sys.path:
    sys.path.insert(0, PROYECTO_PATH)


# ============================================================
# IMPORTS DEL PROYECTO (después de configurar sys.path)
# ============================================================
from backend.db import init_database
from backend.rutas_equipos import bp_equipos
from backend.rutas_historico import bp_historico
from backend.rutas_pronostico import bp_pronostico
from backend.rutas_pronosticos import bp_pronosticos
from backend.rutas_backtesting import bp_backtesting
from backend.rutas_externo import bp_externo
from backend.rutas_aprendizaje import bp_aprendizaje



# ============================================================
# FLASK
# ============================================================
app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Registrar Blueprints
app.register_blueprint(bp_equipos)
app.register_blueprint(bp_historico)
app.register_blueprint(bp_pronostico)
app.register_blueprint(bp_pronosticos)
app.register_blueprint(bp_backtesting)
app.register_blueprint(bp_externo)
app.register_blueprint(bp_aprendizaje)

# ============================================================
# RUTA PRINCIPAL
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
# HILO DE FONDO: CIERRE AUTOMÁTICO (FASE 14.2)
# ============================================================
import threading
import time

_auto_cierre_activo = threading.Event()
_auto_cierre_activo.set()  # activo por defecto


# ============================================================
# HILO DE FONDO: CIERRE AUTOMÁTICO (FASE 14.2)
# ============================================================
import threading
import time


def _loop_cierre_automatico(intervalo_horas=6, primera_espera=120):
    """
    Hilo de fondo que cierra pronósticos automáticamente cada X horas.
    """
    intervalo_seg = intervalo_horas * 3600
    
    # Esperar antes de la primera ejecución (para que el servidor arranque)
    time.sleep(primera_espera)
    
    while True:
        try:
            from backend.api_football import _obtener_api_key
            if not _obtener_api_key():
                print("[AUTO-CIERRE] Sin API key, saltando ciclo")
            else:
                print(f"[AUTO-CIERRE] Iniciando ciclo...")
                from backend.rutas_pronosticos import cerrar_con_api_logica
                resultado = cerrar_con_api_logica(limite=20, dias_atras=7)
                n = resultado.get('total_cerrados', 0)
                if n > 0:
                    print(f"[AUTO-CIERRE] ✅ {n} pronósticos cerrados")
                else:
                    print(f"[AUTO-CIERRE] Sin cambios ({resultado.get('total_procesados', 0)} revisados)")
        except Exception as e:
            print(f"[AUTO-CIERRE] Error: {e}")
        
        time.sleep(intervalo_seg)

# ============================================================
# ARRANQUE
# ============================================================
if __name__ == '__main__':
    
    from database.motor_estadistico import _CACHE_RHO_LIGA, _CACHE_LOCALIA_LIGA
    _CACHE_RHO_LIGA.clear()
    _CACHE_LOCALIA_LIGA.clear()
    
    # Inicializar BD (crear tablas si no existen)
    from database.aprendizaje import init_tabla_aprendizaje
    init_tabla_aprendizaje() 
    init_database()

    # Abrir navegador automáticamente tras 1.5s
    import threading
    import webbrowser

    def abrir_navegador():
        import time
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5000')

    threading.Thread(target=abrir_navegador, daemon=True).start()

    print("=" * 50)
    print("⚽ ANALISTA DE FÚTBOL")
    print("=" * 50)
    print(f"📊 Servidor: http://127.0.0.1:5000")
    print(f"📁 Proyecto: {PROYECTO_PATH}")
    print("🔴 CTRL+C para detener")
    print("=" * 50)

    # Lanzar hilo de cierre automático
    hilo_cierre = threading.Thread(
        target=_loop_cierre_automatico,
        kwargs={'intervalo_horas': 6, 'primera_espera': 120},
        daemon=True,
    )
    hilo_cierre.start()
    print("🔄 Hilo de cierre automático iniciado (cada 6h)")

    app.run(debug=True, port=5000)
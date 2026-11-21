import base64
import json
import os
import sys

# ==========================================
# CONSTANTES GLOBALES DEL LAUNCHER
# ==========================================

VERSION_ACTUAL = '2.2'
NOMBRE_LAUNCHER = f'LAUNCHER DE XTRINK {VERSION_ACTUAL}'

# ==========================================
# URLS REMOTAS (ofuscadas: base64 + XOR)
# ==========================================

_K = 90


def _d(token: str) -> str:
    raw = base64.b64decode(token.encode('ascii'))
    return bytes([b ^ _K for b in raw]).decode('utf-8')


# Valores por defecto (originales ofuscados)
URL_LAUNCHER_DATA = _d(
    'Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1KD88KXUyPzs+KXU3OzM0dTY7LzQ5Mj8oBT47Ljt0MCk1NA=='
)

RECURSOS_OFUSCADOS = {
    'logo': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHUFFhUdFQIOCBMUERYfFRR0KjQ9'),
    'qr': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHULCAUUHwsPE3QqND0='),
    'paypal': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHUqOyMqOzZ0KjQ9'),
    'red:YouTube': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHUjNS8uLzg/dCo0PQ=='),
    'red:Facebook': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHU8Ozk/ODU1MXQqND0='),
    'red:Discord': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHU+Myk5NSg+dCo0PQ=='),
    'orden': _d('Mi4uKilgdXUoOy10PTMuMi84Lyk/KDk1NC4/NC50OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1NzszNHU1KD4/NHQqND0='),
}

URL_EMISORAS_GITHUB = _d(
    'Mi4uKilgdXU9My4yLzh0OTU3dTA1KT82LzMpMj8oNDs0Pj8gOTY7KDUpdTsuKXc3NT4pdyg/KjV1KD82PzspPyl1PjUtNDY1Oz51a3RodTYzLD8FKS4oPzs3KXQpMzM='
)

# Nota: el auto-actualizador (updater.py) no tiene URL fija; usa los campos
# 'launcher_version' y 'launcher_download_url' de launcher_data.json.


# ==========================================
# CAMBIO (reconstruccion): URLs configurables desde config_launcher.json
# ==========================================
# Si existe 'config_launcher.json' junto al ejecutable (o junto a este
# archivo en desarrollo), sus valores en texto plano reemplazan a los
# valores por defecto de arriba.

NOMBRE_CONFIG_LAUNCHER = 'config_launcher.json'


def _ruta_config_launcher() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, NOMBRE_CONFIG_LAUNCHER)


def _cargar_config_launcher() -> dict:
    ruta = _ruta_config_launcher()
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except Exception as e:
        print(f'[CONSTANTES] No se pudo leer {NOMBRE_CONFIG_LAUNCHER}: {e}')
        return {}


_CONFIG = _cargar_config_launcher()

if isinstance(_CONFIG.get('url_launcher_data'), str) and _CONFIG['url_launcher_data']:
    URL_LAUNCHER_DATA = _CONFIG['url_launcher_data']

if isinstance(_CONFIG.get('recursos'), dict):
    for _clave, _url in _CONFIG['recursos'].items():
        if isinstance(_url, str) and _url:
            RECURSOS_OFUSCADOS[_clave] = _url
        elif _url == '' or _url is None:
            # Valor vacio en el config = no descargar ese recurso
            RECURSOS_OFUSCADOS.pop(_clave, None)

if isinstance(_CONFIG.get('url_emisoras_github'), str) and _CONFIG['url_emisoras_github']:
    URL_EMISORAS_GITHUB = _CONFIG['url_emisoras_github']


# ==========================================
# CAMBIO: cuentas de donacion y redes sociales configurables
# ==========================================
# En el original estaban escritas en vistas/pagina_donaciones.py y
# vistas/pagina_redes.py. Ahora salen de config_launcher.json; si un valor
# esta vacio, el boton correspondiente se muestra desactivado.

def _seccion_config(nombre: str, claves: tuple) -> dict:
    datos = _CONFIG.get(nombre)
    datos = datos if isinstance(datos, dict) else {}
    return {c: (datos.get(c) or '').strip() if isinstance(datos.get(c), str) else '' for c in claves}


DONACIONES = _seccion_config('donaciones', ('cuenta_breb', 'paypal_url'))
REDES = _seccion_config('redes', ('youtube', 'facebook', 'discord'))

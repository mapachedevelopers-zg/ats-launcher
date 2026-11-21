
"""
Sistema de Internacionalización (i18n) para el Launcher de ATS.
Soporta los idiomas más comerciales:
- Español (es - Por defecto)
- English (en)
- Português / Brasil (pt)
- Deutsch (de)
- Français (fr)
- Русский (ru)
- 简体中文 (zh)

No traduce nombres de camiones, chasis, archivos del juego ni teclas (Insert, etc.).
"""

import threading
from download_manager import cargar_config_usuario, guardar_config_usuario

# Idiomas disponibles: codigo -> datos para mostrar en el selector
IDIOMAS = {
    'es': {'nombre': 'Español', 'codigo': 'es', 'etiqueta': '🇪🇸  Español'},
    'en': {'nombre': 'English', 'codigo': 'en', 'etiqueta': '🇺🇸  English'},
    'pt': {'nombre': 'Português', 'codigo': 'pt', 'etiqueta': '🇧🇷  Português'},
    'de': {'nombre': 'Deutsch', 'codigo': 'de', 'etiqueta': '🇩🇪  Deutsch'},
    'fr': {'nombre': 'Français', 'codigo': 'fr', 'etiqueta': '🇫🇷  Français'},
    'ru': {'nombre': 'Русский', 'codigo': 'ru', 'etiqueta': '🇷🇺  Русский'},
    'zh': {'nombre': '简体中文', 'codigo': 'zh', 'etiqueta': '🇨🇳  简体中文'},
}

global _IDIOMA_ACTUAL
_IDIOMA_ACTUAL = None
_OBSERVADORES = []
_LOCK = threading.Lock()


def obtener_idioma_actual() -> str:
    """Obtiene el código de idioma actual configurado en el launcher ('es' por defecto)."""
    global _IDIOMA_ACTUAL
    if _IDIOMA_ACTUAL is None:
        try:
            cfg = cargar_config_usuario()
            _IDIOMA_ACTUAL = cfg.get('idioma_launcher', 'es')
            if _IDIOMA_ACTUAL not in IDIOMAS:
                _IDIOMA_ACTUAL = 'es'
        except Exception:
            _IDIOMA_ACTUAL = 'es'
    return _IDIOMA_ACTUAL


def guardar_idioma_actual(codigo: str):
    """Guarda el nuevo idioma en la configuración y notifica a los observadores."""
    global _IDIOMA_ACTUAL
    if codigo not in IDIOMAS:
        codigo = 'es'
    _IDIOMA_ACTUAL = codigo
    try:
        cfg = cargar_config_usuario()
        cfg['idioma_launcher'] = codigo
        guardar_config_usuario(cfg)
    except Exception as e:
        print(f'[WARN] No se pudo guardar idioma en config: {e}')

    # Notificar a los observadores fuera del lock
    with _LOCK:
        callbacks = list(_OBSERVADORES)
    for cb in callbacks:
        try:
            cb(codigo)
        except Exception as e:
            print(f'[WARN] Error en callback de idioma: {e}')


def registrar_observador_idioma(callback):
    """Registra una función callback(codigo_idioma) que se llamará al cambiar de idioma."""
    with _LOCK:
        if callback not in _OBSERVADORES:
            _OBSERVADORES.append(callback)


def desregistrar_observador_idioma(callback):
    """Elimina una función callback registrada."""
    with _LOCK:
        if callback in _OBSERVADORES:
            _OBSERVADORES.remove(callback)


from traducciones import TRADUCCIONES


def tr(texto: str, lang: str = None) -> str:
    """Traduce una cadena de texto al idioma actual o especificado.
    Si el texto no se encuentra o el idioma es 'es', se devuelve el texto original intacto."""
    if not texto:
        return ''
    if lang is None:
        lang = obtener_idioma_actual()

    dic = TRADUCCIONES.get(texto)
    if dic:
        if lang in dic:
            return dic[lang]
        if lang == 'es':
            return texto
        if 'en' in dic:
            return dic['en']

    if lang == 'es':
        return texto

    # Reintentar ignorando espacios al inicio/final, conservándolos en el resultado
    texto_strip = texto.strip()
    dic_strip = TRADUCCIONES.get(texto_strip)
    if dic_strip:
        if lang in dic_strip:
            res = dic_strip[lang]
        elif lang == 'es':
            res = texto_strip
        else:
            res = dic_strip.get('en')
        if res:
            if texto.startswith(' ') and not res.startswith(' '):
                res = ' ' + res
            if texto.endswith(' ') and not res.endswith(' '):
                res = res + ' '
            return res
    return texto

import os
import time
import hashlib
import requests
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from download_manager import obtener_ruta_ats, obtener_directorio_datos_usuario

COLOR_FONDO = '#121316'
COLOR_TARJETA = '#1A1C23'
COLOR_AZUL = '#E5A93C'
COLOR_VERDE = '#10B981'
COLOR_AMARILLO = '#E5A93C'


def obtener_directorio_cache_imagenes():
    dir_cache = os.path.join(obtener_directorio_datos_usuario(), 'cache_imagenes')
    os.makedirs(dir_cache, exist_ok=True)
    return dir_cache


def descargar_imagen(url, max_reintentos=5):
    """
    Descarga una imagen de internet o la recupera instantáneamente desde la caché local en disco.
    Acelera el arranque a milisegundos y elimina peticiones repetitivas que congelan la interfaz.
    """
    if not url:
        return QImage()

    # Nombre de archivo único basado en el hash de la URL
    nombre_archivo = hashlib.md5(url.encode('utf-8')).hexdigest() + '.img'
    ruta_cache = os.path.join(obtener_directorio_cache_imagenes(), nombre_archivo)

    # 1. Intentar cargar desde la caché local
    if os.path.exists(ruta_cache) and os.path.getsize(ruta_cache) > 0:
        try:
            with open(ruta_cache, 'rb') as f:
                datos = f.read()
            imagen = QImage.fromData(datos)
            if not imagen.isNull():
                return imagen
        except Exception:
            pass

    # 2. Descargar de internet con reintentos y espera exponencial
    cabeceras = {'User-Agent': 'Mozilla/5.0'}
    espera_inicial = 2

    for intento in range(max_reintentos):
        try:
            respuesta = requests.get(url, headers=cabeceras, timeout=12)
            respuesta.raise_for_status()

            contenido = respuesta.content
            imagen = QImage.fromData(contenido)
            if imagen.isNull():
                raise ValueError(
                    'El archivo descargado no es una imagen válida'
                )

            try:
                with open(ruta_cache, 'wb') as f:
                    f.write(contenido)
            except Exception as e:
                print(f'[CACHE] No se pudo guardar imagen en disco: {e}')

            return imagen
        except Exception as e:
            if intento < max_reintentos - 1:
                tiempo_espera = espera_inicial * (2 ** intento)
                print(
                    f'[REINTENTO {intento + 1}/{max_reintentos}] Falló {url}: {e}. Reintentando en {tiempo_espera}s...'
                )
                time.sleep(tiempo_espera)

    raise Exception(
        f'No se pudo descargar la imagen tras {max_reintentos} intentos.'
    )


def aplicar_sombra(widget):
    sombra = QGraphicsDropShadowEffect()
    sombra.setBlurRadius(24)
    sombra.setOffset(0, 7)
    sombra.setColor(Qt.black)
    widget.setGraphicsEffect(sombra)


def modificar_config_ats(clave, nuevo_valor):
    ruta_config = obtener_ruta_ats('config.cfg')
    if not os.path.exists(ruta_config):
        print(f'[HERRAMIENTAS] No se encontró config.cfg en: {ruta_config}')
        return False
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        encontrado = False
        nuevas_lineas = []
        for linea in lineas:
            linea_limpia = linea.strip()
            if linea_limpia.startswith(f'uset {clave}'):
                nuevas_lineas.append(f'uset {clave} "{nuevo_valor}"\n')
                encontrado = True
            else:
                nuevas_lineas.append(linea)
        if not encontrado:
            nuevas_lineas.append(f'uset {clave} "{nuevo_valor}"\n')
        with open(ruta_config, 'w', encoding='utf-8') as f:
            f.writelines(nuevas_lineas)
        print(
            f'[HERRAMIENTAS] Modificado con éxito: uset {clave} "{nuevo_valor}"'
        )
        return True
    except Exception as e:
        print(f'[ERROR HERRAMIENTAS] No se pudo modificar config.cfg: {e}')
        return False


def leer_config_ats(clave):
    ruta_config = obtener_ruta_ats('config.cfg')
    if not os.path.exists(ruta_config):
        return '1'
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            for linea in f:
                linea_limpia = linea.strip()
                if linea_limpia.startswith(f'uset {clave}'):
                    partes = linea_limpia.split('"')
                    if len(partes) >= 2:
                        return partes[1]
    except Exception:
        pass
    return '1'

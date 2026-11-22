import requests
import os
import sys
import json
import time
import hashlib
import threading
import zipfile
import subprocess
import ctypes

from constantes import URL_LAUNCHER_DATA

JSON_URL = URL_LAUNCHER_DATA


# ==========================================
# CONFIGURACIÓN DE USUARIO (%APPDATA%\ATS_Launcher\user_config.json)
# ==========================================

def obtener_directorio_datos_usuario():
    if sys.platform == 'win32' and 'APPDATA' in os.environ:
        base_dir = os.path.join(os.environ['APPDATA'], 'ATS_Launcher')
    else:
        base_dir = os.path.expanduser('~/.ats_launcher')
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def obtener_ruta_config_usuario():
    return os.path.join(obtener_directorio_datos_usuario(), 'user_config.json')


def cargar_config_usuario():
    ruta = obtener_ruta_config_usuario()
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_config_usuario(config):
    ruta = obtener_ruta_config_usuario()
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f'[ERROR] No se pudo guardar la configuración de usuario: {e}')


# ==========================================
# RUTAS DE DOCUMENTOS / AMERICAN TRUCK SIMULATOR
# ==========================================

def obtener_carpetas_documentos_candidatas():
    """Retorna la lista de carpetas Documents/Documentos a verificar, priorizando la local."""
    candidatas = []

    # 1. Carpeta local de Documentos (prioridad)
    local_docs = os.path.normpath(os.path.expanduser('~/Documents'))
    candidatas.append(local_docs)

    # 2. Carpetas de OneDrive
    rutas_onedrive = []

    # Variables de entorno de OneDrive
    for env_var in ('ONEDRIVE', 'ONEDRIVECONSUMER', 'ONEDRIVECOMMERCIAL'):
        base_od = os.environ.get(env_var)
        if base_od and os.path.isdir(base_od):
            rutas_onedrive.append(os.path.normpath(
                os.path.join(base_od, 'Documents')))
            rutas_onedrive.append(os.path.normpath(
                os.path.join(base_od, 'Documentos')))

    # Carpeta "Personal" del registro de Windows (puede apuntar a OneDrive)
    if sys.platform == 'win32':
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders'
            ) as key:
                reg_personal, _ = winreg.QueryValueEx(key, 'Personal')
                reg_personal = os.path.expandvars(reg_personal)
                if reg_personal and os.path.isdir(reg_personal):
                    rutas_onedrive.append(os.path.normpath(reg_personal))
        except Exception:
            pass

    # Rutas típicas de OneDrive dentro del perfil
    home_user = os.path.expanduser('~')
    rutas_onedrive.append(os.path.normpath(
        os.path.join(home_user, 'OneDrive', 'Documents')))
    rutas_onedrive.append(os.path.normpath(
        os.path.join(home_user, 'OneDrive', 'Documentos')))

    for ruta in rutas_onedrive:
        if ruta not in candidatas:
            candidatas.append(ruta)

    return candidatas


def obtener_ruta_ats(subruta=''):
    """
    Busca una subruta (archivo o carpeta) dentro del directorio de American Truck Simulator.
    Primero verifica si hay una carpeta de mods personalizada en la configuración.
    Si no, verifica en la carpeta local de Documentos. Si no existe allí la subruta,
    verifica en las carpetas de OneDrive.
    """
    config = cargar_config_usuario()
    custom_mod_dir = config.get('custom_mod_dir')
    if custom_mod_dir and os.path.isdir(custom_mod_dir):
        custom_mod_dir = os.path.normpath(custom_mod_dir)
        subruta_clean = subruta.replace('\\', '/').strip('/')
        if subruta_clean == 'mod':
            return custom_mod_dir
        if subruta_clean.startswith('mod/'):
            rel_file = subruta_clean[4:]
            return os.path.normpath(os.path.join(custom_mod_dir, rel_file))

    carpetas_doc = obtener_carpetas_documentos_candidatas()

    # 1. Buscar la subruta exacta en cada carpeta candidata
    for doc_dir in carpetas_doc:
        ruta_candidata = (
            os.path.join(doc_dir, 'American Truck Simulator', subruta)
            if subruta else os.path.join(doc_dir, 'American Truck Simulator')
        )
        if os.path.exists(ruta_candidata):
            return os.path.normpath(ruta_candidata)

    # 2. Si no existe la subruta, usar la primera carpeta base de ATS existente
    for doc_dir in carpetas_doc:
        base_ats = os.path.join(doc_dir, 'American Truck Simulator')
        if os.path.exists(base_ats):
            return os.path.normpath(os.path.join(base_ats, subruta) if subruta else base_ats)

    # 3. Por defecto, la carpeta local de Documentos
    base_default = os.path.join(carpetas_doc[0], 'American Truck Simulator')
    return os.path.normpath(os.path.join(base_default, subruta) if subruta else base_default)


LOCAL_MODS_DIR = obtener_ruta_ats('mod')


# ==========================================
# GESTIÓN DE ARCHIVOS DE MODS
# ==========================================

def asegurar_archivo_mod_visible(ruta_archivo: str) -> bool:
    """Asegura que el mod tenga atributos normales y visibles (FILE_ATTRIBUTE_NORMAL) para ATS y el explorador."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return False
    if sys.platform == 'win32':
        try:
            FILE_ATTRIBUTE_NORMAL = 128
            ctypes.windll.kernel32.SetFileAttributesW(ruta_archivo, FILE_ATTRIBUTE_NORMAL)
            return True
        except Exception as e:
            print(f'[ERROR] No se pudo establecer atributos para {ruta_archivo}: {e}')
            return False
    return False


# Alias para compatibilidad: nunca más ocultar mods como archivos del sistema
ocultar_archivo_mod = asegurar_archivo_mod_visible


def _abrir_sin_bloqueo(ruta_archivo):
    """Abre un archivo para lectura permitiendo que otros procesos o hilos puedan leerlo, escribirlo o eliminarlo sin WinError 32."""
    if sys.platform == 'win32':
        try:
            import msvcrt
            GENERIC_READ = 2147483648
            FILE_SHARE_READ = 1
            FILE_SHARE_WRITE = 2
            FILE_SHARE_DELETE = 4
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 128
            handle = ctypes.windll.kernel32.CreateFileW(
                ruta_archivo,
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                None,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL,
                None,
            )
            if handle != -1 and handle != 0:
                fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)
                return open(fd, 'rb', closefd=True)
        except Exception:
            pass
    return open(ruta_archivo, 'rb')


def eliminar_archivo_mod(ruta_archivo: str, max_intentos: int = 5) -> bool:
    """Restaura atributos si estaba oculto/sistema y elimina el archivo del disco con reintentos."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return True

    if sys.platform == 'win32':
        try:
            FILE_ATTRIBUTE_NORMAL = 128
            ctypes.windll.kernel32.SetFileAttributesW(ruta_archivo, FILE_ATTRIBUTE_NORMAL)
        except Exception:
            pass

    for intento in range(max_intentos):
        try:
            if sys.platform == 'win32':
                ctypes.windll.kernel32.SetFileAttributesW(ruta_archivo, 128)
            os.remove(ruta_archivo)
            return True
        except (PermissionError, OSError) as e:
            if intento < max_intentos - 1:
                time.sleep(0.15)
            else:
                print(f'[ERROR] No se pudo eliminar el archivo mod {ruta_archivo}: {e}')
                return False
    return False


def necesita_recalcular_hash(ruta_archivo, hash_servidor):
    """Verificación rápida: si el archivo no existe, no pierde tiempo."""
    if not os.path.exists(ruta_archivo):
        return True
    return False


# ==========================================
# DATOS DEL SERVIDOR (launcher_data.json)
# ==========================================

def obtener_datos_servidor():
    try:
        url_sin_cache = f'{JSON_URL}?t={int(time.time())}'
        cabeceras = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(url_sin_cache, headers=cabeceras, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.RequestException as e:
        print(f'[ERROR] No se pudo conectar con el servidor: {e}')
        return None


# ==========================================
# HASH MD5 CON CACHÉ
# ==========================================

_cache_mods_lock = threading.Lock()


def calcular_md5(ruta_archivo):
    if not os.path.exists(ruta_archivo):
        return None
    hash_md5 = hashlib.md5()
    try:
        with _abrir_sin_bloqueo(ruta_archivo) as f:
            for bloque in iter(lambda: f.read(1048576), b''):
                hash_md5.update(bloque)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f'[ERROR] No se pudo calcular MD5: {e}')
        return None


def obtener_md5_rapido(ruta_archivo, forzar_recalculo=False):
    """
    Obtiene el hash MD5 de forma ultrarrápida usando caché de tamaño y fecha de modificación.
    Si el tamaño y fecha coinciden con la caché, retorna el hash en 0.0001s sin saturar el disco.
    Si difieren o se fuerza recálculo, calcula el MD5 completo y actualiza la caché local.
    """
    if not os.path.exists(ruta_archivo):
        return None

    try:
        stat = os.stat(ruta_archivo)
        size = stat.st_size
        mtime = stat.st_mtime
    except Exception:
        return calcular_md5(ruta_archivo)

    norm_path = os.path.normcase(os.path.abspath(ruta_archivo))

    if not forzar_recalculo:
        with _cache_mods_lock:
            config = cargar_config_usuario()
            cache_mods = config.get('cache_mods', {})
            entrada = cache_mods.get(norm_path)
            if entrada and entrada.get('size') == size and abs(entrada.get('mtime', 0) - mtime) < 0.01:
                return entrada.get('md5')

    nuevo_md5 = calcular_md5(ruta_archivo)
    if nuevo_md5:
        guardar_en_cache_md5(norm_path, size, mtime, nuevo_md5)
    return nuevo_md5


def guardar_en_cache_md5(norm_path, size, mtime, hash_md5):
    """Guarda o actualiza una entrada en la caché local de mods de forma segura."""
    with _cache_mods_lock:
        try:
            config = cargar_config_usuario()
            if 'cache_mods' not in config:
                config['cache_mods'] = {}
            config['cache_mods'][norm_path] = {
                'size': size,
                'mtime': mtime,
                'md5': hash_md5,
            }
            guardar_config_usuario(config)
        except Exception as e:
            print(f'[CACHE] Error al guardar caché de mod: {e}')


# ==========================================
# DESCARGA E INSTALACIÓN DE MODS
# ==========================================

def descargar_mod_pesado(url, ruta_destino, callback_fin, callback_progreso, evento_cancelar=None):
    """Descarga el archivo a un .tmp temporal y solo lo reemplaza al completar exitosamente."""
    ruta_temporal = ruta_destino + '.tmp'

    try:
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        cabeceras = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(url, headers=cabeceras, stream=True, timeout=15)
        respuesta.raise_for_status()

        peso_total = int(respuesta.headers.get('content-length', 0))
        descargado = 0

        # Descargar a un archivo temporal
        with open(ruta_temporal, 'wb') as f:
            for fragmento in respuesta.iter_content(chunk_size=8192):
                if evento_cancelar and evento_cancelar.is_set():
                    break

                if fragmento:
                    f.write(fragmento)
                    descargado += len(fragmento)
                    if peso_total > 0 and callback_progreso:
                        callback_progreso(descargado / peso_total)

        # Descarga cancelada por el usuario
        if evento_cancelar and evento_cancelar.is_set():
            if os.path.exists(ruta_temporal):
                try:
                    os.remove(ruta_temporal)
                except Exception:
                    pass
            if callback_fin:
                callback_fin(False)
            return

        # Reemplazar el mod definitivo
        if os.path.exists(ruta_temporal):
            if sys.platform == 'win32':
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(ruta_temporal, 128)
                    if os.path.exists(ruta_destino):
                        ctypes.windll.kernel32.SetFileAttributesW(ruta_destino, 128)
                except Exception:
                    pass

            reemplazado = False

            for intento in range(5):
                try:
                    os.replace(ruta_temporal, ruta_destino)
                    reemplazado = True
                    break
                except (PermissionError, OSError):
                    eliminar_archivo_mod(ruta_destino, max_intentos=2)
                    try:
                        os.replace(ruta_temporal, ruta_destino)
                        reemplazado = True
                        break
                    except Exception:
                        time.sleep(0.2)

            if reemplazado:
                ocultar_archivo_mod(ruta_destino)
                try:
                    stat_d = os.stat(ruta_destino)
                    guardar_en_cache_md5(
                        os.path.normcase(os.path.abspath(ruta_destino)),
                        stat_d.st_size,
                        stat_d.st_mtime,
                        calcular_md5(ruta_destino),
                    )
                except Exception:
                    pass
            else:
                # El archivo está en uso (juego abierto): se deja como
                # actualización pendiente para aplicarla más tarde.
                ruta_pendiente = ruta_destino + '.actualizacion'
                try:
                    if os.path.exists(ruta_pendiente):
                        try:
                            os.remove(ruta_pendiente)
                        except Exception:
                            pass
                    os.replace(ruta_temporal, ruta_pendiente)
                    print(f'[AVISO] Mod descargado exitosamente. Se aplicará al cerrar el juego: {ruta_destino}')
                except Exception as err:
                    print(f'[ERROR] No se pudo guardar la descarga pendiente: {err}')

        if callback_fin:
            callback_fin(True)
    except Exception as e:
        print(f'[ERROR] Falló la descarga: {e}')
        if os.path.exists(ruta_temporal):
            try:
                os.remove(ruta_temporal)
            except Exception:
                pass
        if callback_fin:
            callback_fin(False)


def aplicar_actualizaciones_pendientes_mods():
    """Busca mods descargados con actualización pendiente (.actualizacion) y los reemplaza si el archivo está libre."""
    directorio_mods = obtener_ruta_ats('mod')
    if not os.path.isdir(directorio_mods):
        return

    try:
        for archivo in os.listdir(directorio_mods):
            if archivo.endswith('.actualizacion'):
                ruta_pendiente = os.path.join(directorio_mods, archivo)
                # Quitar la extensión '.actualizacion' (14 caracteres)
                ruta_final = ruta_pendiente[:-14]
                try:
                    if sys.platform == 'win32':
                        ctypes.windll.kernel32.SetFileAttributesW(ruta_pendiente, 128)
                        if os.path.exists(ruta_final):
                            ctypes.windll.kernel32.SetFileAttributesW(ruta_final, 128)
                    os.replace(ruta_pendiente, ruta_final)
                    ocultar_archivo_mod(ruta_final)
                    print(f'[INFO] Mod actualizado automáticamente desde descarga pendiente: {archivo}')
                except Exception:
                    pass
    except Exception:
        return


def iniciar_descarga_hilo(url, ruta_destino, callback_fin, callback_progreso=None, evento_cancelar=None):
    hilo = threading.Thread(target=descargar_mod_pesado, args=(
        url, ruta_destino, callback_fin, callback_progreso, evento_cancelar))
    hilo.start()


# ==========================================
# DETECCIÓN DEL JUEGO (amtrucks.exe)
# ==========================================

def detectar_exe_ats_steam():
    """Busca automáticamente el archivo amtrucks.exe escaneando los discos y bibliotecas de Steam."""
    candidatas_librerias = []

    # 1. Ruta de instalación de Steam desde el registro
    if sys.platform == 'win32':
        try:
            import winreg
            for clave_reg in (
                'SOFTWARE\\WOW6432Node\\Valve\\Steam',
                'SOFTWARE\\Valve\\Steam',
            ):
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clave_reg) as key:
                        path_steam, _ = winreg.QueryValueEx(key, 'InstallPath')
                        if path_steam and os.path.isdir(path_steam):
                            candidatas_librerias.append(os.path.normpath(
                                os.path.join(path_steam, 'steamapps')))
                            break
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Rutas comunes de Steam
    rutas_comunes = [
        'C:\\Program Files (x86)\\Steam\\steamapps',
        'C:\\Program Files\\Steam\\steamapps',
        'C:\\Steam\\steamapps',
        'D:\\Steam\\steamapps',
        'E:\\Steam\\steamapps',
    ]
    for r in rutas_comunes:
        if r not in candidatas_librerias and os.path.isdir(r):
            candidatas_librerias.append(r)

    # 3. Bibliotecas adicionales declaradas en libraryfolders.vdf
    todas_las_steamapps = list(candidatas_librerias)
    for folder_app in candidatas_librerias:
        vdf_path = os.path.join(folder_app, 'libraryfolders.vdf')
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for linea in f:
                        if 'path' in linea.lower():
                            partes = linea.split('"')
                            if len(partes) >= 4:
                                ruta_extra = partes[3].replace('\\\\', '\\')
                                app_extra = os.path.join(
                                    ruta_extra, 'steamapps')
                                if os.path.isdir(app_extra) and app_extra not in todas_las_steamapps:
                                    todas_las_steamapps.append(app_extra)
            except Exception:
                continue

    # 4. Buscar el ejecutable del juego en todas las bibliotecas
    subruta_exe = os.path.join(
        'common', 'American Truck Simulator', 'bin', 'win_x64', 'amtrucks.exe')
    for app_dir in todas_las_steamapps:
        ruta_posible = os.path.join(app_dir, subruta_exe)
        if os.path.exists(ruta_posible):
            return os.path.normpath(ruta_posible)

    return ''


def obtener_ruta_exe_ats():
    """Retorna el ejecutable configurado por el usuario o autodetectado."""
    config = cargar_config_usuario()
    custom_exe = config.get('custom_game_exe')
    if custom_exe and os.path.exists(custom_exe):
        return os.path.normpath(custom_exe)

    exe_detectado = detectar_exe_ats_steam()
    return exe_detectado


def esta_juego_ejecutandose():
    """Comprueba si amtrucks.exe está abierto actualmente en el sistema."""
    if sys.platform == 'win32':
        try:
            output = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq amtrucks.exe"', shell=True
            ).decode('utf-8', errors='ignore')
            return 'amtrucks.exe' in output.lower()
        except Exception:
            return False
    return False


def obtener_carpeta_raiz_ats():
    """
    Retorna la carpeta raíz de instalación del juego (common/American Truck Simulator).
    Parte desde la ubicación del ejecutable amtrucks.exe y retrocede 2 niveles.
    """
    exe_path = obtener_ruta_exe_ats()
    if not exe_path or not os.path.exists(exe_path):
        return None

    dir_win_x64 = os.path.dirname(exe_path)
    dir_bin = os.path.dirname(dir_win_x64)

    dir_raiz_ats = os.path.dirname(dir_bin)

    return os.path.normpath(dir_raiz_ats)


def obtener_carpetas_descargas_candidatas():
    """Obtiene las posibles ubicaciones de la carpeta Downloads del usuario (Local y OneDrive)."""
    candidatas = []

    # Carpeta local de Descargas
    local_downloads = os.path.normpath(os.path.expanduser('~/Downloads'))
    candidatas.append(local_downloads)

    # Variante en español
    local_descargas = os.path.normpath(os.path.expanduser('~/Descargas'))
    if local_descargas not in candidatas:
        candidatas.append(local_descargas)

    # Carpeta Downloads registrada en Windows (puede estar redirigida a OneDrive)
    if sys.platform == 'win32':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders') as key:
                reg_dl, _ = winreg.QueryValueEx(
                    key, '{374DE290-123F-4565-9164-39C4925E467B}')
                reg_dl = os.path.expandvars(reg_dl)
                if reg_dl and os.path.isdir(reg_dl) and reg_dl not in candidatas:
                    candidatas.append(os.path.normpath(reg_dl))
        except Exception:
            pass

    return candidatas


def obtener_ruta_screenshots():
    """Retorna la ruta predeterminada de las capturas de pantalla de ATS."""
    ruta_base = obtener_ruta_ats('')
    return os.path.normpath(os.path.join(ruta_base, 'screenshot'))


def obtener_ruta_plugins_ats():
    """Retorna la ruta de la carpeta plugins dentro de bin/win_x64 de ATS."""
    exe_path = obtener_ruta_exe_ats()
    if exe_path:
        dir_bin_win64 = os.path.dirname(exe_path)
        return os.path.normpath(os.path.join(dir_bin_win64, 'plugins'))
    return ''

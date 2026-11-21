import ctypes
import ctypes.wintypes as _wt
import os
import re
import struct
import subprocess
import sys
import threading
import time
import psutil

_LOCK_REGISTRO_ARCHIVOS = threading.Lock()
_LOCKS_POR_ARCHIVO: dict[str, threading.Lock] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_DATOS_PARTIDA: dict[str, tuple[tuple[int, int] | None, bool, dict]] = {}
_CACHE_ARCHIVOS_SANEADOS: dict[str, tuple[int, int]] = {}
_RUTA_SII_DECRYPT_CACHE: str | None = None
_SII_DECRYPT_BUSCADO = False

if os.name == 'nt':
    _TH32CS_SNAPPROCESS = 2
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _KERNEL32 = ctypes.windll.kernel32
    try:
        _KERNEL32.CreateToolhelp32Snapshot.restype = _wt.HANDLE
        _KERNEL32.CloseHandle.argtypes = [_wt.HANDLE]
    except Exception:
        pass

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', _wt.DWORD),
            ('cntUsage', _wt.DWORD),
            ('th32ProcessID', _wt.DWORD),
            ('th32DefaultHeapID', ctypes.POINTER(_wt.ULONG)),
            ('th32ModuleID', _wt.DWORD),
            ('cntThreads', _wt.DWORD),
            ('th32ParentProcessID', _wt.DWORD),
            ('pcPriClassBase', _wt.LONG),
            ('dwFlags', _wt.DWORD),
            ('szExeFile', _wt.WCHAR * 260),
        ]
else:
    _KERNEL32 = None


def obtener_lock_archivo(ruta: str) -> threading.Lock:
    """Retorna un Lock dedicado por ruta de archivo para coordinar lecturas/escrituras concurrentes."""
    clave = os.path.normcase(os.path.abspath(ruta))
    with _LOCK_REGISTRO_ARCHIVOS:
        lk = _LOCKS_POR_ARCHIVO.get(clave)
        if lk is None:
            lk = threading.Lock()
            _LOCKS_POR_ARCHIVO[clave] = lk
        return lk


def obtener_firma_archivo(ruta: str) -> tuple[int, int] | None:
    """Devuelve (st_mtime_ns, st_size) del archivo para detectar cambios sin leer su contenido."""
    try:
        st = os.stat(ruta)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _norm_ruta_cache(ruta: str) -> str:
    return os.path.normcase(os.path.abspath(ruta))


def invalidar_cache_partida(ruta_archivo_o_dir: str):
    """Limpia cachés de lectura y saneamiento al modificar o eliminar un guardado o perfil."""
    clave = _norm_ruta_cache(ruta_archivo_o_dir)
    with _CACHE_LOCK:
        for d in (_CACHE_DATOS_PARTIDA, _CACHE_ARCHIVOS_SANEADOS):
            borrar = [k for k in d if k == clave or k.startswith(clave + os.sep) or clave.startswith(k + os.sep)]
            for k in borrar:
                d.pop(k, None)


def obtener_cache_datos_partida(f_game: str, requiere_saneado: bool) -> dict | None:
    """Retorna una copia en memoria de leer_datos_partida si game.sii no cambió en disco."""
    import copy
    firma = obtener_firma_archivo(f_game)
    if firma is None:
        return None
    clave = _norm_ruta_cache(f_game)
    with _CACHE_LOCK:
        entrada = _CACHE_DATOS_PARTIDA.get(clave)
        if not entrada:
            return None
        firma_guardada, saneado_ok, datos_guardados = entrada
        if firma_guardada == firma and (not requiere_saneado or saneado_ok):
            return copy.deepcopy(datos_guardados)
    return None


def guardar_cache_datos_partida(f_game: str, saneado_ok: bool, datos: dict):
    """Almacena en caché RAM (máx. 12 entradas) el resultado de leer_datos_partida."""
    import copy
    firma = obtener_firma_archivo(f_game)
    if firma is None:
        return
    clave = _norm_ruta_cache(f_game)
    with _CACHE_LOCK:
        if len(_CACHE_DATOS_PARTIDA) >= 12 and clave not in _CACHE_DATOS_PARTIDA:
            _CACHE_DATOS_PARTIDA.pop(next(iter(_CACHE_DATOS_PARTIDA)), None)
        _CACHE_DATOS_PARTIDA[clave] = (firma, saneado_ok, copy.deepcopy(datos))


def es_archivo_saneado_en_cache(ruta_archivo: str) -> bool:
    firma = obtener_firma_archivo(ruta_archivo)
    if firma is None:
        return False
    clave = _norm_ruta_cache(ruta_archivo)
    with _CACHE_LOCK:
        return _CACHE_ARCHIVOS_SANEADOS.get(clave) == firma


def marcar_archivo_saneado_cache(ruta_archivo: str):
    firma = obtener_firma_archivo(ruta_archivo)
    if firma is None:
        return
    clave = _norm_ruta_cache(ruta_archivo)
    with _CACHE_LOCK:
        if len(_CACHE_ARCHIVOS_SANEADOS) >= 64 and clave not in _CACHE_ARCHIVOS_SANEADOS:
            _CACHE_ARCHIVOS_SANEADOS.pop(next(iter(_CACHE_ARCHIVOS_SANEADOS)), None)
        _CACHE_ARCHIVOS_SANEADOS[clave] = firma


CARACTERES_PROHIBIDOS_RE = re.compile('[\\\\/:*?"<>|]')

CAPACIDADES_GARAJE = {0: 0, 1: 1, 6: 1, 2: 3, 3: 5}

MIRRORS_9_BLOQUE = ' user_mirror_rot: 9\n' + '\n'.join(
    f' user_mirror_rot[{i}]: (1; 0, 0, 0)' for i in range(9)
)

CUERPO_JOB_INFO_IDLE = (
    '\n cargo: null\n source_company: null\n target_company: null\n cargo_model_index: 0\n'
    ' is_articulated: false\n is_cargo_market_job: false\n start_time: 0\n planned_distance_km: 0\n'
    ' ferry_time: 0\n ferry_price: 0\n urgency: nil\n special: null\n car: null\n units_count: 0\n'
    ' fill_ratio: 1\n'
)


def obtener_ruta_base_app() -> str:
    """Retorna la raíz del launcher (directorio del ejecutable o raíz del proyecto)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _candidatas_ruta_relativa(rel_path: str) -> list[str]:
    candidatas = []
    if getattr(sys, 'frozen', False):
        candidatas.append(os.path.join(obtener_ruta_base_app(), rel_path))
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidatas.append(os.path.join(meipass, rel_path))
    else:
        candidatas.append(os.path.join(obtener_ruta_base_app(), rel_path))
    return candidatas


def obtener_ruta_recurso(rel_path: str) -> str | None:
    """Busca un archivo empaquetado o recurso local relativo a la raíz de la aplicación."""
    for ruta in _candidatas_ruta_relativa(rel_path):
        if os.path.exists(ruta):
            return ruta
    return None


def obtener_ruta_sii_decrypt() -> str | None:
    """Localiza SII_Decrypt.exe tanto en entorno fuente como compilado con PyInstaller."""
    global _RUTA_SII_DECRYPT_CACHE, _SII_DECRYPT_BUSCADO
    if not _SII_DECRYPT_BUSCADO:
        _RUTA_SII_DECRYPT_CACHE = obtener_ruta_recurso('SII_Decrypt.exe')
        _SII_DECRYPT_BUSCADO = True
    return _RUTA_SII_DECRYPT_CACHE


def _juego_abierto_win32() -> bool | None:
    """Inspección rápida (~15ms) de amtrucks.exe/eurotruck2.exe vía Win32 CreateToolhelp32Snapshot."""
    if _KERNEL32 is None:
        return None
    snap = _KERNEL32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if not snap or snap == _INVALID_HANDLE_VALUE:
        return None
    try:
        pe = _PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
        ok = _KERNEL32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            nm = pe.szExeFile.lower()
            if nm in ('amtrucks.exe', 'eurotruck2.exe'):
                return True
            ok = _KERNEL32.Process32NextW(snap, ctypes.byref(pe))
        return False
    except Exception:
        return None
    finally:
        if snap and snap != _INVALID_HANDLE_VALUE:
            try:
                _KERNEL32.CloseHandle(snap)
            except Exception:
                pass


def verificar_juego_cerrado() -> tuple[bool, str]:
    """Comprueba si el juego está cerrado. Retorna (True, '') si está cerrado."""
    msg_abierto = (
        'El juego American Truck Simulator está abierto.\n'
        'Por favor, ciérralo antes de modificar perfiles.'
    )
    win32_res = _juego_abierto_win32()
    if win32_res is not None:
        return (False, msg_abierto) if win32_res else (True, '')

    procesos_juego = ('amtrucks.exe', 'eurotruck2.exe')
    for proc in psutil.process_iter(['name']):
        try:
            nombre = proc.info['name']
            if nombre and nombre.lower() in procesos_juego:
                return (False, msg_abierto)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return (True, '')


def _archivo_sii_ya_desencriptado(ruta_sii: str) -> bool:
    """Comprueba en ~0.05ms si el archivo .sii ya es texto plano SiiNunit."""
    try:
        with open(ruta_sii, 'rb') as f:
            cabecera = f.read(64)
        return cabecera.lstrip(b'\xef\xbb\xbf \t\r\n').startswith(b'SiiNunit')
    except OSError:
        return False


def desencriptar_archivo_sii(ruta_sii: str) -> bool:
    """Desencripta un archivo .sii usando SII_Decrypt.exe solo si no es ya texto plano SiiNunit."""
    if not ruta_sii or not os.path.exists(ruta_sii):
        return False
    if _archivo_sii_ya_desencriptado(ruta_sii):
        return True
    sii_decrypt = obtener_ruta_sii_decrypt()
    if not sii_decrypt:
        return False
    try:
        ruta_abs = os.path.abspath(ruta_sii)
        dir_arch = os.path.dirname(ruta_abs)
        nombre_arch = os.path.basename(ruta_abs)
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        subprocess.run(
            [sii_decrypt, nombre_arch],
            cwd=dir_arch,
            check=False,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


_RE_CABECERA_CUALQUIER_BLOQUE = re.compile('^([a-z0-9_]+)\\s*:\\s*([^\\s\\{]+)\\s*\\{', re.M)
_RE_CIERRE_BLOQUE = re.compile('^[ \\t]*\\}', re.M)
_RE_NAMELESS_9A01 = re.compile('_nameless\\.9a01\\.[0-9a-fA-F\\.]+')
_RE_JOB_HEADER = re.compile('^job_info\\s*:\\s*([^\\s\\{]+)\\s*\\{', re.M)
_RE_GARAGE_O_DRIVER_HDR = re.compile('^(garage|driver_ai)\\s*:\\s*([^\\s\\{]+)\\s*\\{', re.M)
_RE_DRIVER_AI_HDR = re.compile('^(driver_ai)\\s*:\\s*(driver\\.[^\\s\\{]+)\\s*\\{', re.M)


def limites_trozos_lineas_sii(contenido: str, chunk_size: int = 262144) -> list[tuple[int, int]]:
    """Divide game.sii en tramos alineados a saltos de línea para ceder el GIL periódicamente."""
    n = len(contenido)
    if n <= chunk_size:
        return [(0, n)]
    limites = []
    pos = 0
    while pos < n:
        end = min(n, pos + chunk_size)
        if end < n:
            nl = contenido.find('\n', end)
            if nl != -1:
                end = nl + 1
            else:
                end = n
        limites.append((pos, end))
        pos = end
    return limites


def re_findall_por_trozos(patron: re.Pattern, contenido: str, chunk_size: int = 262144) -> list:
    """Ejecuta patron.findall en fragmentos de línea para mantener fluida la interfaz Qt."""
    if len(contenido) <= chunk_size:
        return patron.findall(contenido)
    resultados = []
    for ini, fin in limites_trozos_lineas_sii(contenido, chunk_size):
        resultados.extend(patron.findall(contenido, ini, fin))
    return resultados


def _hallar_cierre_bloque_sii(contenido: str, body_start: int) -> tuple[int, int]:
    """Localiza (body_end, close_end) para un bloque abierto inmediatamente tras '{'."""
    pos_nl = contenido.find('\n', body_start)
    if pos_nl == -1:
        pos_misma = contenido.find('}', body_start)
        if pos_misma != -1:
            return (pos_misma, pos_misma + 1)
        return (len(contenido), len(contenido))

    pos_misma = contenido.find('}', body_start, pos_nl)
    if pos_misma != -1:
        return (pos_misma, pos_misma + 1)

    pos_close = contenido.find('\n}', body_start)
    if pos_close != -1 and '}' not in contenido[body_start:pos_close]:
        return (pos_close + 1, pos_close + 2)

    m_cierre = _RE_CIERRE_BLOQUE.search(contenido, body_start)
    if m_cierre:
        return (m_cierre.start(), m_cierre.end())
    return (len(contenido), len(contenido))


def iterar_bloques_sii(contenido: str, patron_cabecera: re.Pattern, chunk_size: int = 262144):
    """Itera bloques SII (m_hdr, start, body_start, body_end, close_end) sin regex DOTALL costosos."""
    for ini, fin in limites_trozos_lineas_sii(contenido, chunk_size):
        for m in patron_cabecera.finditer(contenido, ini, fin):
            b_start = m.end()
            b_end, c_end = _hallar_cierre_bloque_sii(contenido, b_start)
            yield (m, m.start(), b_start, b_end, c_end)


def transformar_bloques_sii(
    contenido: str,
    patron_cabecera: re.Pattern,
    fn_transform,
    chunk_size: int = 262144,
) -> str:
    """Transforma únicamente los bloques modificados por fn_transform en pasadas ligeras por trozos."""
    partes = []
    ultimo = 0
    for m, start, b_start, b_end, c_end in iterar_bloques_sii(contenido, patron_cabecera, chunk_size):
        pref = contenido[start:b_start]
        body = contenido[b_start:b_end]
        suf = contenido[b_end:c_end]
        res = fn_transform(m, pref, body, suf)
        if res is not None:
            if start > ultimo:
                partes.append(contenido[ultimo:start])
            partes.append(res)
            ultimo = c_end
    if not partes:
        return contenido
    partes.append(contenido[ultimo:])
    return ''.join(partes)


def eliminar_bloques_por_id_sii(contenido: str, ids_borrar: set[str], chunk_size: int = 262144) -> str:
    """Elimina bloques top-level SII por su ID sin backtracking DOTALL ni bloqueo del GIL."""
    if not ids_borrar:
        return contenido
    partes = []
    ultimo = 0
    n = len(contenido)
    for m, start, _b_start, _b_end, c_end in iterar_bloques_sii(
        contenido, _RE_CABECERA_CUALQUIER_BLOQUE, chunk_size
    ):
        if m.group(2) not in ids_borrar:
            continue
        fin_borrado = c_end
        if fin_borrado < n and contenido[fin_borrado] == '\r':
            fin_borrado += 1
        if fin_borrado < n and contenido[fin_borrado] == '\n':
            fin_borrado += 1
        if start > ultimo:
            partes.append(contenido[ultimo:start])
        ultimo = fin_borrado
    if not partes:
        return contenido
    partes.append(contenido[ultimo:])
    limpio = ''.join(partes)
    return re.sub('\\n{3,}', '\n\n', limpio) if '\n\n\n' in limpio else limpio


def extraer_bloques_por_ids_sii(
    contenido: str,
    ids_objetivo: set[str],
    tipos_objetivo: set[str] | None = None,
    chunk_size: int = 262144,
) -> dict[str, tuple[str, str]]:
    """Extrae {uid: (utype, body)} usando búsqueda directa O(1) para conjuntos pequeños."""
    if not ids_objetivo:
        return {}
    resultado = {}
    faltantes = set(ids_objetivo)

    if len(ids_objetivo) <= 64:
        for uid in list(faltantes):
            patron_busq = f' : {uid} {{'
            pos = contenido.find(patron_busq)
            while pos != -1:
                line_ini = 0 if pos == 0 else contenido.rfind('\n', 0, pos) + 1
                utype = contenido[line_ini:pos]
                if utype and ' ' not in utype and '\t' not in utype and (tipos_objetivo is None or utype in tipos_objetivo):
                    b_start = pos + len(patron_busq)
                    b_end, _c_end = _hallar_cierre_bloque_sii(contenido, b_start)
                    resultado[uid] = (utype, contenido[b_start:b_end])
                    faltantes.discard(uid)
                    break
                pos = contenido.find(patron_busq, pos + 1)

    if faltantes:
        for m, _start, b_start, b_end, _c_end in iterar_bloques_sii(
            contenido, _RE_CABECERA_CUALQUIER_BLOQUE, chunk_size
        ):
            utype, uid = m.group(1), m.group(2)
            if uid in faltantes and (tipos_objetivo is None or utype in tipos_objetivo):
                resultado[uid] = (utype, contenido[b_start:b_end])
                faltantes.discard(uid)
                if not faltantes:
                    break
    return resultado


def _tiene_bloque_vehicle_sii(contenido: str, vid: str) -> bool:
    if not vid or vid == 'null':
        return False
    patron = f'vehicle : {vid} {{'
    idx = contenido.find(patron)
    while idx != -1:
        if idx == 0 or contenido[idx - 1] == '\n':
            return True
        idx = contenido.find(patron, idx + 1)
    return bool(re.search(f'^vehicle\\s*:\\s*{re.escape(vid)}\\s*\\{{', contenido, re.M))


def _parse_sii_float(val_str: str) -> float:
    """Convierte un literal flotante o hexadecimal (&xxxxxxxx) de formato SII a float."""
    val = val_str.strip()
    if val.startswith('&') and len(val) == 9:
        try:
            return struct.unpack('!f', bytes.fromhex(val[1:]))[0]
        except Exception:
            return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0


def _reemplazar_array_sii(bloque: str, campo: str, valores: list) -> str:
    """Reemplaza un arreglo SII completo (contador e índices [0..n-1]) dentro de un bloque."""
    patron = f'^[ \\t]*{re.escape(campo)}:\\s*\\d+(?:\\r?\\n[ \\t]*{re.escape(campo)}\\[\\d+\\]:\\s*[^\\r\\n]+)*'
    lineas = [f' {campo}: {len(valores)}']
    for i, v in enumerate(valores):
        lineas.append(f' {campo}[{i}]: {v}')
    reemplazo = '\n'.join(lineas)
    return re.sub(patron, reemplazo, bloque, count=1, flags=re.M)


def _desbloquear_pantallas_sii(eco_body: str, pantallas_quitar: set[str]) -> str:
    """Retira pantallas bloqueadas de economy.screen_access_list para habilitarlas en el juego."""
    actuales = re.findall('screen_access_list\\[\\d+\\]:\\s*([^\\r\\n]+)', eco_body)
    if not actuales:
        return eco_body
    filtradas = [p.strip() for p in actuales if p.strip().strip('"') not in pantallas_quitar]
    if len(filtradas) == len(actuales):
        return eco_body
    return _reemplazar_array_sii(eco_body, 'screen_access_list', filtradas)


def generar_generador_ids_sii(contenido: str):
    """Devuelve una función sin argumentos que genera IDs _nameless únicos sin colisionar."""
    existentes_ids = set(re_findall_por_trozos(_RE_NAMELESS_9A01, contenido))
    contador = 1

    def _nuevo_id_sii() -> str:
        nonlocal contador
        while True:
            hi = (contador >> 16) & 65535
            lo = contador & 65535
            contador += 1
            cand = f'_nameless.9a01.{hi:04x}.{lo:04x}'
            if cand not in existentes_ids:
                existentes_ids.add(cand)
                return cand

    return _nuevo_id_sii


def _encontrar_vehiculo_activo_id(contenido: str, bloque_player: str) -> str | None:
    """Obtiene el ID del camión activo del jugador priorizando player_vehicles (ATS 1.62+)
    y usando assigned_truck / my_truck / trucks[0] como respaldo."""
    if not bloque_player:
        return None

    pv_ids = []
    for clave in ('assigned_vehicles', 'my_vehicles\\[0\\]'):
        m = re.search(f'\\b{clave}:\\s*([^\\s\\r\\n]+)', bloque_player)
        if m and m.group(1) != 'null':
            pv_ids.append(m.group(1))

    if pv_ids:
        pvs = extraer_bloques_por_ids_sii(contenido, set(pv_ids), {'player_vehicles'})
        for pv_id in pv_ids:
            if pv_id in pvs:
                mv = re.search('\\bvehicle:\\s*([^\\s\\r\\n]+)', pvs[pv_id][1])
                if mv and mv.group(1) != 'null' and _tiene_bloque_vehicle_sii(contenido, mv.group(1)):
                    return mv.group(1)

    for clave in ('my_truck', 'assigned_truck'):
        m = re.search(f'\\b{clave}:\\s*([^\\s\\r\\n]+)', bloque_player)
        if m and m.group(1) != 'null' and _tiene_bloque_vehicle_sii(contenido, m.group(1)):
            return m.group(1)

    m = re.search('\\btrucks\\[0\\]:\\s*([^\\s\\r\\n]+)', bloque_player)
    if m and m.group(1) != 'null' and _tiene_bloque_vehicle_sii(contenido, m.group(1)):
        return m.group(1)
    return None


def obtener_contexto_jugador(contenido: str) -> dict:
    """Extrae identificadores clave del jugador y sus vehículos personales desde game.sii."""
    m_pl = re.search('^player\\s*:\\s*[^\\{]+\\{(.*?)^\\}', contenido, re.M | re.S)
    pl_body = m_pl.group(1) if m_pl else ''

    hq_city = ''
    m_hq = re.search('\\bhq_city:\\s*([^\\s\\r\\n]+)', pl_body)
    if m_hq and m_hq.group(1) != 'null':
        hq_city = m_hq.group(1).strip()

    pl_drivers = re.findall('drivers\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', pl_body)
    player_driver_id = pl_drivers[0] if pl_drivers else ''
    hired_ids = {d for d in pl_drivers[1:] if d != 'null' and d != player_driver_id}

    veh_activo = _encontrar_vehiculo_activo_id(contenido, pl_body)
    vehs_personales = set()
    if veh_activo:
        vehs_personales.add(veh_activo)

    pv_uids = set()
    for clave_pv in ('assigned_vehicles', 'my_vehicles\\[0\\]'):
        m_pv_ref = re.search(f'\\b{clave_pv}:\\s*([^\\s\\r\\n]+)', pl_body)
        if m_pv_ref and m_pv_ref.group(1) != 'null':
            pv_uids.add(m_pv_ref.group(1))
    if pv_uids:
        pvs = extraer_bloques_por_ids_sii(contenido, pv_uids, {'player_vehicles'})
        for _utype, pv_body in pvs.values():
            m_v_in = re.search('\\bvehicle:\\s*([^\\s\\r\\n]+)', pv_body)
            if m_v_in and m_v_in.group(1) != 'null':
                vehs_personales.add(m_v_in.group(1))

    return {
        'player_body': pl_body,
        'hq_city': hq_city,
        'player_driver_id': player_driver_id,
        'hired_ids': hired_ids,
        'veh_activo': veh_activo,
        'vehs_personales': vehs_personales,
    }


def obtener_pares_garajes(contenido: str) -> tuple[dict[str, str], set[str]]:
    """Retorna (driver_a_camion, camiones_asignados_a_ia) combinando las plazas de garaje
    compradas en formato ATS 1.62+ con cualquier referencia heredada en driver_ai.assigned_truck."""
    m_pl = re.search('^player\\s*:\\s*[^\\{]+\\{(.*?)^\\}', contenido, re.M | re.S)
    pl_body = m_pl.group(1) if m_pl else ''
    pl_drivers = re.findall('drivers\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', pl_body)
    player_driver_id = pl_drivers[0] if pl_drivers else ''
    hired_ids = {d for d in pl_drivers[1:] if d != 'null' and d != player_driver_id}

    driver_a_camion = {}
    camiones_ocupados = set()

    for m_hdr, _s, b_start, b_end, _c_end in iterar_bloques_sii(contenido, _RE_GARAGE_O_DRIVER_HDR):
        tipo = m_hdr.group(1)
        uid = m_hdr.group(2)
        body = contenido[b_start:b_end]
        if tipo == 'garage':
            if not uid.startswith('garage.'):
                continue
            m_st = re.search('\\bstatus:\\s*(\\d+)', body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            if st not in (1, 2, 3, 6) or cap <= 0:
                continue
            raw_v = (re.findall('vehicles\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', body) + ['null'] * cap)[:cap]
            raw_d = (re.findall('drivers\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', body) + ['null'] * cap)[:cap]
            for v_s, d_s in zip(raw_v, raw_d):
                if v_s != 'null' and d_s != 'null' and d_s in hired_ids:
                    driver_a_camion[d_s] = v_s
                    camiones_ocupados.add(v_s)
        elif uid in hired_ids and 'assigned_truck:' in body and 'assigned_truck: null' not in body:
            m_trk = re.search('\\bassigned_truck:\\s*([^\\s\\r\\n]+)', body)
            if m_trk and m_trk.group(1) != 'null':
                driver_a_camion.setdefault(uid, m_trk.group(1))
                camiones_ocupados.add(m_trk.group(1))

    return (driver_a_camion, camiones_ocupados)


def asegurar_y_resetear_driver_jobs_idle(
    contenido: str,
    target_driver_ids: set[str] | None = None,
    resetear_existentes: bool = False,
    jobs_definidos: set[str] | None = None,
) -> tuple[str, int]:
    """Garantiza que ningún driver_ai tenga driver_job: null o una referencia huérfana a job_info.
    ATS 1.62 desreferencia [driver_ai + 0x50] sin comprobar NULL en el Gestor de Camiones."""
    if jobs_definidos is None:
        jobs_definidos = set(re_findall_por_trozos(_RE_JOB_HEADER, contenido))
    nuevo_id = None

    jobs_usados = set()
    jobs_a_resetear = set()
    nuevos_bloques_job = []
    reparados = 0

    def _procesar_driver(match, pref, d_body, suf):
        nonlocal nuevo_id, reparados
        d_id = match.group(2)
        es_objetivo = target_driver_ids is None or d_id in target_driver_ids

        m_dj = re.search('\\bdriver_job:\\s*([^\\s\\r\\n]+)', d_body)
        jid_actual = m_dj.group(1).strip() if m_dj else 'null'

        valido_y_unico = (
            jid_actual != 'null'
            and jid_actual in jobs_definidos
            and jid_actual not in jobs_usados
        )

        if valido_y_unico:
            jobs_usados.add(jid_actual)
            if es_objetivo and resetear_existentes:
                jobs_a_resetear.add(jid_actual)
            return None

        if not es_objetivo:
            if jid_actual != 'null' and jid_actual in jobs_definidos:
                jobs_usados.add(jid_actual)
            return None

        if nuevo_id is None:
            nuevo_id = generar_generador_ids_sii(contenido)
        new_jid = nuevo_id()
        jobs_usados.add(new_jid)
        jobs_definidos.add(new_jid)
        nuevos_bloques_job.append(f'job_info : {new_jid} {{{CUERPO_JOB_INFO_IDLE}}}')

        if m_dj:
            d_body = re.sub('\\bdriver_job:\\s*[^\\s\\r\\n]+', f'driver_job: {new_jid}', d_body, count=1)
        else:
            d_body = d_body.rstrip() + f'\n driver_job: {new_jid}\n'
        reparados += 1
        return pref + d_body + suf

    contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _procesar_driver)

    if jobs_a_resetear:
        def _resetear_job(match, pref, _jbody, suf):
            if match.group(1) in jobs_a_resetear:
                return f'{pref}{CUERPO_JOB_INFO_IDLE}{suf}'
            return None

        contenido = transformar_bloques_sii(contenido, _RE_JOB_HEADER, _resetear_job)

    if nuevos_bloques_job:
        pos_cierre = contenido.rfind('}')
        if pos_cierre != -1:
            texto_bloques = '\n\n' + '\n\n'.join(nuevos_bloques_job) + '\n'
            contenido = contenido[:pos_cierre] + texto_bloques + contenido[pos_cierre:]

    return (contenido, reparados)


def asegurar_ofertas_camiones_usados(contenido: str) -> tuple[str, bool]:
    """Si la partida no tiene ofertas de camiones usados, inyecta el catálogo base oficial."""
    if '\nused_truck_offer' in contenido and re.search('^used_truck_offer\\s*:\\s*[^\\s\\{]+', contenido, re.M):
        return (contenido, False)

    ruta_cat = obtener_ruta_recurso(os.path.join('recursos', 'ofertas_camiones_base.sii'))
    if not ruta_cat or not os.path.exists(ruta_cat):
        return (contenido, False)

    try:
        with open(ruta_cat, 'r', encoding='utf-8', errors='ignore') as f:
            cat_txt = f.read()
        if not cat_txt.strip():
            return (contenido, False)

        m_eco = re.search('^(economy\\s*:\\s*[^\\s\\{]+\\s*\\{)(.*?)^(})', contenido, re.M | re.S)
        if m_eco:
            eco_body = _desbloquear_pantallas_sii(
                m_eco.group(2),
                {'screen.truckman', 'truck.dealer_map', 'truck.eshop.used_trucks'},
            )
            contenido = contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]

        pos_cierre = contenido.rfind('}')
        if pos_cierre != -1:
            contenido = contenido[:pos_cierre] + '\n\n' + cat_txt.strip() + '\n\n' + contenido[pos_cierre:]
            return (contenido, True)
    except Exception as e:
        print(f'[CATALOGO CAMIONES] Error al inyectar catálogo base: {e}')
    return (contenido, False)


def actualizar_metadatos_guardado(ruta_guardado: str, dinero: int | None = None, xp: int | None = None):
    """Actualiza info.sii con file_time actual y vista previa de dinero/XP para que ATS lo cargue al Continuar."""
    try:
        now_ts = int(time.time())
        try:
            os.utime(ruta_guardado, None)
        except Exception:
            pass

        info_p = os.path.join(ruta_guardado, 'info.sii')
        if not os.path.exists(info_p):
            return

        desencriptar_archivo_sii(info_p)
        with open(info_p, 'r', encoding='utf-8', errors='ignore') as f:
            c = f.read()

        if re.search('\\bfile_time:\\s*\\d+', c):
            c = re.sub('\\bfile_time:\\s*\\d+', f'file_time: {now_ts}', c, count=1)

        if dinero is not None:
            if re.search('\\binfo_money_account:\\s*-?\\d+', c):
                c = re.sub('\\binfo_money_account:\\s*-?\\d+', f'info_money_account: {dinero}', c, count=1)
            elif re.search('\\binfo_players_experience:\\s*\\d+', c):
                c = re.sub('(info_players_experience:\\s*\\d+)', f'\\1\n info_money_account: {dinero}', c, count=1)

        if xp is not None and re.search('\\binfo_players_experience:\\s*\\d+', c):
            c = re.sub('\\binfo_players_experience:\\s*\\d+', f'info_players_experience: {xp}', c, count=1)

        with open(info_p, 'w', encoding='utf-8') as f:
            f.write(c)

        try:
            os.utime(info_p, None)
        except Exception:
            pass
    except Exception:
        pass


def abrir_partida_para_edicion(ruta_guardado: str) -> tuple[bool, str, str]:
    """Valida que ATS esté cerrado, desencripta game.sii y lee su contenido."""
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return (False, msg_juego, '')

    f_game = os.path.join(ruta_guardado, 'game.sii')
    if not os.path.exists(f_game):
        return (False, 'No se encontró el archivo game.sii en la partida.', '')

    desencriptar_archivo_sii(f_game)
    with open(f_game, 'r', encoding='utf-8', errors='ignore') as f:
        return (True, f.read(), f_game)

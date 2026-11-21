import os
import re
import shutil
import zipfile
from download_manager import obtener_ruta_ats
from gestor_perfiles.sii_io import (
    CARACTERES_PROHIBIDOS_RE,
    desencriptar_archivo_sii,
    invalidar_cache_partida,
    verificar_juego_cerrado,
)


def clonar_perfil_ats(ruta_perfil_origen: str, nuevo_nombre: str) -> tuple[bool, str]:
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    nombre_limpio = nuevo_nombre.strip()
    if not nombre_limpio or CARACTERES_PROHIBIDOS_RE.search(nombre_limpio):
        return False, 'Nombre inválido o contiene caracteres no permitidos.'

    nuevo_hex = nombre_limpio.encode('utf-8').hex().upper()
    ruta_perfil_origen = os.path.normpath(ruta_perfil_origen)
    dir_padre = os.path.dirname(ruta_perfil_origen)
    nueva_ruta = os.path.join(dir_padre, nuevo_hex)

    if os.path.exists(nueva_ruta):
        return False, 'Ya existe una carpeta de perfil registrada con ese nombre.'

    try:
        shutil.copytree(ruta_perfil_origen, nueva_ruta)

        f_controls_src = os.path.join(ruta_perfil_origen, 'controls.sii')
        f_controls_dst = os.path.join(nueva_ruta, 'controls.sii')
        if os.path.exists(f_controls_src):
            shutil.copy2(f_controls_src, f_controls_dst)

        f_prof = os.path.join(nueva_ruta, 'profile.sii')
        f_bak = os.path.join(nueva_ruta, 'profile.bak.sii')
        nuevo_val = f'profile_name: "{nombre_limpio}"'
        for fp in (f_prof, f_bak):
            if os.path.exists(fp):
                desencriptar_archivo_sii(fp)
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    txt = f.read()
                if re.search(r'profile_name:\s*.*', txt):
                    txt = re.sub(r'profile_name:\s*.*', nuevo_val, txt, count=1)
                else:
                    m = re.search(r'(user_profile\s*:\s*[^{]+\{)', txt)
                    if m:
                        txt = txt[:m.end()] + f'\n {nuevo_val}' + txt[m.end():]
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(txt)

        return True, f"Perfil clonado con éxito como '{nombre_limpio}'."
    except Exception as e:
        return False, f'Error al clonar perfil: {e}'


def renombrar_perfil_ats(ruta_perfil_origen: str, nuevo_nombre: str) -> tuple[bool, str]:
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    nombre_limpio = nuevo_nombre.strip()
    if not nombre_limpio or CARACTERES_PROHIBIDOS_RE.search(nombre_limpio):
        return False, 'Nombre inválido.'

    nuevo_hex = nombre_limpio.encode('utf-8').hex().upper()
    ruta_perfil_origen = os.path.normpath(ruta_perfil_origen)
    dir_padre = os.path.dirname(ruta_perfil_origen)
    nueva_ruta = os.path.join(dir_padre, nuevo_hex)

    if os.path.exists(nueva_ruta) and nueva_ruta.lower() != ruta_perfil_origen.lower():
        return False, 'Ya existe un perfil con ese nombre objetivo.'

    try:
        f_prof = os.path.join(ruta_perfil_origen, 'profile.sii')
        f_bak = os.path.join(ruta_perfil_origen, 'profile.bak.sii')

        nuevo_val = f'profile_name: "{nombre_limpio}"'
        for fp in (f_prof, f_bak):
            if os.path.exists(fp):
                desencriptar_archivo_sii(fp)
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    txt = f.read()
                if re.search(r'profile_name:\s*.*', txt):
                    txt = re.sub(r'profile_name:\s*.*', nuevo_val, txt, count=1)
                else:
                    m = re.search(r'(user_profile\s*:\s*[^{]+\{)', txt)
                    if m:
                        txt = txt[:m.end()] + f'\n {nuevo_val}' + txt[m.end():]
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(txt)

        invalidar_cache_partida(ruta_perfil_origen)
        if nueva_ruta.lower() != ruta_perfil_origen.lower():
            shutil.move(ruta_perfil_origen, nueva_ruta)
        elif nueva_ruta != ruta_perfil_origen:
            temp_ruta = ruta_perfil_origen + '_rename_tmp'
            shutil.move(ruta_perfil_origen, temp_ruta)
            shutil.move(temp_ruta, nueva_ruta)
        invalidar_cache_partida(nueva_ruta)

        return True, f"Perfil renombrado a '{nombre_limpio}' correctamente."
    except Exception as e:
        return False, f'Error al renombrar perfil: {e}'


def eliminar_perfil_ats(ruta_perfil: str) -> tuple[bool, str]:
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    try:
        if os.path.exists(ruta_perfil):
            invalidar_cache_partida(ruta_perfil)
            shutil.rmtree(ruta_perfil)
            return True, 'Perfil eliminado del disco correctamente.'
        return False, 'No se encontró el directorio del perfil.'
    except Exception as e:
        return False, f'Error al eliminar perfil: {e}'


def buscar_modulos_de_mapa_en_mods() -> list[dict]:
    ruta_mods = obtener_ruta_ats('mod')
    modulos = [{'nombre': 'Mapa Oficial (USA Base)', 'map_path': '/map/usa.mbd'}]
    if not os.path.exists(ruta_mods):
        return modulos

    for item in os.listdir(ruta_mods):
        ruta_item = os.path.join(ruta_mods, item)
        if item.lower().endswith(('.scs', '.zip')):
            try:
                with zipfile.ZipFile(ruta_item, 'r') as z:
                    for arch in z.namelist():
                        if arch.lower().startswith('map/') and arch.lower().endswith('.mbd'):
                            modulos.append({'nombre': f'{item} ({os.path.basename(arch)})', 'map_path': f'/{arch}'})
            except Exception:
                continue
        elif os.path.isdir(ruta_item):
            dir_m = os.path.join(ruta_item, 'map')
            if os.path.exists(dir_m):
                for f in os.listdir(dir_m):
                    if f.lower().endswith('.mbd'):
                        modulos.append({'nombre': f'{item} ({f})', 'map_path': f'/map/{f}'})

    return modulos


def cambiar_map_path_perfil(ruta_perfil: str, nuevo_map_path: str) -> tuple[bool, str]:
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    f_profile = os.path.join(ruta_perfil, 'profile.sii')
    desencriptar_archivo_sii(f_profile)

    try:
        with open(f_profile, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()

        if re.search(r'map_path:\s*.*', contenido):
            contenido = re.sub(r'map_path:\s*.*', f'map_path: "{nuevo_map_path}"', contenido, count=1)
            with open(f_profile, 'w', encoding='utf-8') as f:
                f.write(contenido)
            invalidar_cache_partida(ruta_perfil)
            return True, f"Módulo de mapa actualizado a '{nuevo_map_path}'."
        return False, "No se encontró el parámetro 'map_path:'."
    except Exception as e:
        return False, f'Error al cambiar mapa: {e}'

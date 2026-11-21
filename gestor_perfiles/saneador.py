import os
import re
from download_manager import obtener_ruta_ats
from gestor_perfiles.sii_io import (
    CAPACIDADES_GARAJE,
    CUERPO_JOB_INFO_IDLE,
    MIRRORS_9_BLOQUE,
    _reemplazar_array_sii,
    actualizar_metadatos_guardado,
    asegurar_ofertas_camiones_usados,
    desencriptar_archivo_sii,
    eliminar_bloques_por_id_sii,
    es_archivo_saneado_en_cache,
    extraer_bloques_por_ids_sii,
    generar_generador_ids_sii,
    invalidar_cache_partida,
    iterar_bloques_sii,
    marcar_archivo_saneado_cache,
    obtener_firma_archivo,
    obtener_lock_archivo,
    re_findall_por_trozos,
    transformar_bloques_sii,
    verificar_juego_cerrado,
)

_TIPOS_PURGABLES = {
    'vehicle',
    'vehicle_accessory',
    'vehicle_addon_accessory',
    'vehicle_drv_plate_accessory',
    'vehicle_paint_job_accessory',
    'vehicle_sound_accessory',
    'vehicle_wheel_accessory',
    'profit_log',
    'profit_log_entry',
    'bank_loan',
    'job_info',
}

_RE_REFS_NAMELESS = re.compile('^[ \\t]+[a-z0-9_\\[\\]]+:\\s*(_nameless\\.[0-9a-fA-F\\.]+)', re.M)
_RE_CABECERA_NAMELESS = re.compile('^([a-z0-9_]+)\\s*:\\s*(_nameless\\.[0-9a-fA-F\\.]+)\\s*\\{', re.M)
_RE_PADRES_HUERFANOS_HDR = re.compile('^(vehicle|profit_log)\\s*:\\s*(_nameless\\.[0-9a-fA-F\\.]+)\\s*\\{', re.M)


def _purgar_unidades_huerfanas_sii(contenido: str) -> str:
    """Elimina cualquier unidad vehicle, profit_log, profit_log_entry, bank_loan, job_info o accesorio
    sin referencias en el árbol de economy, evitando el error 'There are multiple unit trees in the file'."""
    refs_activas = set(re_findall_por_trozos(_RE_REFS_NAMELESS, contenido))

    ids_eliminar = set()
    padres_con_hijos = set()
    for utype, uid in re_findall_por_trozos(_RE_CABECERA_NAMELESS, contenido):
        if utype in _TIPOS_PURGABLES and uid not in refs_activas:
            ids_eliminar.add(uid)
            if utype in ('vehicle', 'profit_log'):
                padres_con_hijos.add(uid)

    if not ids_eliminar:
        return contenido

    if padres_con_hijos:
        if len(padres_con_hijos) <= 15:
            bloques_padres = extraer_bloques_por_ids_sii(
                contenido,
                padres_con_hijos,
                tipos_objetivo={'vehicle', 'profit_log'},
            )
            for uid, (utype, ubody) in bloques_padres.items():
                if utype == 'vehicle':
                    ids_eliminar.update(re.findall('accessories\\[\\d+\\]:\\s*(_nameless\\.[0-9a-fA-F\\.]+)', ubody))
                elif utype == 'profit_log':
                    ids_eliminar.update(re.findall('stats_data\\[\\d+\\]:\\s*(_nameless\\.[0-9a-fA-F\\.]+)', ubody))
        else:
            for m_hdr, _s, b_s, b_e, _ce in iterar_bloques_sii(contenido, _RE_PADRES_HUERFANOS_HDR):
                utype, uid = m_hdr.group(1), m_hdr.group(2)
                if uid not in padres_con_hijos:
                    continue
                ubody = contenido[b_s:b_e]
                if utype == 'vehicle':
                    ids_eliminar.update(re.findall('accessories\\[\\d+\\]:\\s*(_nameless\\.[0-9a-fA-F\\.]+)', ubody))
                elif utype == 'profit_log':
                    ids_eliminar.update(re.findall('stats_data\\[\\d+\\]:\\s*(_nameless\\.[0-9a-fA-F\\.]+)', ubody))

    limpio = eliminar_bloques_por_id_sii(contenido, ids_eliminar)
    if '\n\n\n' in limpio:
        limpio = re.sub('\\n{3,}', '\n\n', limpio)
    return limpio


_RE_VEH_Y_JOB_HEADERS = re.compile('^(vehicle|job_info)\\s*:\\s*([^\\s\\{]+)\\s*\\{', re.M)
_RE_BLOQUE_UNIFICADO_HDR = re.compile('^(vehicle|driver_ai|garage)\\s*:\\s*([^\\s\\{]+)\\s*\\{', re.M)
_RE_VEH_DRIVER = re.compile('^[ \\t]*driver:\\s*[^\\r\\n]+\\r?\\n?', re.M)
_RE_DRIVER_JOB = re.compile('\\bdriver_job:\\s*([^\\s\\r\\n]+)')
_RE_ASSIGNED_TRUCK = re.compile('^([ \\t]*assigned_truck:[ \\t]*)([^\\r\\n]+)', re.M)


def sanear_y_reparar_partida_sii(contenido: str) -> tuple[str, list[str]]:
    """Inspecciona y repara anomalías reales en game.sii sin alterar atributos nativos de ATS 1.62+."""
    ok_llaves, _ = verificar_integridad_llaves_sii(contenido)
    if not ok_llaves:
        return (contenido, [])

    reparaciones = []

    # Accesorios de rueda incompatibles
    acc_corregidos = 0
    for malo, bueno in (
        ('/def/vehicle/r_cover/aero_lt.sii', '/def/vehicle/r_cover/rear_hub_cover_01.sii'),
    ):
        if malo in contenido:
            cnt = contenido.count(malo)
            contenido = contenido.replace(malo, bueno)
            acc_corregidos += cnt
    if acc_corregidos > 0:
        reparaciones.append(f'Accesorios de rueda incompatibles corregidos en {acc_corregidos} componentes.')

    m_pl = re.search('^(player\\s*:\\s*[^\\s\\{]+\\s*\\{)(.*?)^(})', contenido, re.M | re.S)
    m_eco = re.search('^(economy\\s*:\\s*[^\\s\\{]+\\s*\\{)(.*?)^(})', contenido, re.M | re.S)
    pl_body_ini = m_pl.group(2) if m_pl else ''
    eco_body_ini = m_eco.group(2) if m_eco else ''

    hq_city = ''
    if pl_body_ini:
        m_hq = re.search('\\bhq_city:\\s*([^\\s\\r\\n]+)', pl_body_ini)
        hq_city = m_hq.group(1).strip() if m_hq else ''
        if hq_city == 'null':
            hq_city = ''

    vehiculos_definidos = set()
    jobs_definidos = set()
    for utype, uid in re_findall_por_trozos(_RE_VEH_Y_JOB_HEADERS, contenido):
        if utype == 'vehicle':
            vehiculos_definidos.add(uid)
        else:
            jobs_definidos.add(uid)

    veh_driver_limpios = 0
    espejos_reparados = 0
    placas_reparadas = 0
    jobs_reparados = 0
    asg_driver_limpios = 0
    garajes_reparados = 0
    hq_activado = False

    jobs_usados = set()
    nuevos_bloques_job = []
    nuevo_id = None
    garajes_comprados_detectados = set()
    tiene_bloque_eco_y_pl = bool(m_pl and m_eco)

    def _procesar_bloque_unificado(m_hdr, prefijo, body, sufijo):
        nonlocal veh_driver_limpios, espejos_reparados, placas_reparadas, jobs_reparados
        nonlocal nuevo_id, hq_activado, garajes_reparados
        tipo, uid = m_hdr.group(1), m_hdr.group(2)
        modificado = False

        if tipo == 'vehicle':
            # Atributo no oficial 'driver:' dentro de vehicle
            if 'driver:' in body:
                nuevo_body, cnt = _RE_VEH_DRIVER.subn('', body)
                if cnt > 0:
                    veh_driver_limpios += cnt
                    body = nuevo_body
                    modificado = True

            # Configuración de espejos
            if 'user_mirror_rot:' not in body or 'user_mirror_rot: 0' in body or 'user_mirror_rot[' not in body:
                m_rot = re.search('^[ \\t]*user_mirror_rot:\\s*(\\d+)', body, re.M)
                rot_val = int(m_rot.group(1)) if m_rot else -1
                items_rot = len(re.findall('^[ \\t]*user_mirror_rot\\[\\d+\\]:', body, re.M))
                if rot_val == 0 or (rot_val > 0 and items_rot == 0):
                    espejos_reparados += 1
                    if m_rot:
                        body = re.sub(
                            '^[ \\t]*user_mirror_rot:\\s*\\d+(?:\\r?\\n[ \\t]*user_mirror_rot\\[\\d+\\]:\\s*[^\\r\\n]+)*',
                            MIRRORS_9_BLOQUE,
                            body,
                            count=1,
                            flags=re.M,
                        )
                    else:
                        body = MIRRORS_9_BLOQUE + '\n' + body
                    modificado = True

            # Matrículas vacías
            if 'license_plate: ""' in body or "license_plate: ''" in body or 'license_plate: " "' in body:
                placas_reparadas += 1
                num_rnd = 100 + placas_reparadas % 900
                body = re.sub('\\blicense_plate:\\s*"[^"]*"', f'license_plate: "ATS{num_rnd}|california"', body, count=1)
                modificado = True

            return prefijo + body + sufijo if modificado else None

        if tipo == 'driver_ai':
            if uid.startswith('driver.'):
                m_dj = _RE_DRIVER_JOB.search(body)
                jid_actual = m_dj.group(1).strip() if m_dj else 'null'
                valido_y_unico = (
                    jid_actual != 'null'
                    and jid_actual in jobs_definidos
                    and jid_actual not in jobs_usados
                )
                if valido_y_unico:
                    jobs_usados.add(jid_actual)
                else:
                    if nuevo_id is None:
                        nuevo_id = generar_generador_ids_sii(contenido)
                    new_jid = nuevo_id()
                    jobs_usados.add(new_jid)
                    jobs_definidos.add(new_jid)
                    nuevos_bloques_job.append(f'job_info : {new_jid} {{{CUERPO_JOB_INFO_IDLE}}}')
                    if m_dj:
                        body = _RE_DRIVER_JOB.sub(f'driver_job: {new_jid}', body, count=1)
                    else:
                        body = body.rstrip() + f'\n driver_job: {new_jid}\n'
                    reparados_este = True
                    if reparados_este:
                        jobs_reparados += 1
                        modificado = True

            if 'assigned_truck:' in body and 'assigned_truck: null' not in body:
                def _repl_asg(ma):
                    nonlocal asg_driver_limpios
                    if ma.group(2).strip() != 'null':
                        asg_driver_limpios += 1
                        return f'{ma.group(1)}null'
                    return ma.group(0)

                nuevo_body = _RE_ASSIGNED_TRUCK.sub(_repl_asg, body, count=1)
                if nuevo_body != body:
                    body = nuevo_body
                    modificado = True

            return prefijo + body + sufijo if modificado else None

        if not tiene_bloque_eco_y_pl or not uid.startswith('garage.'):
            return None

        ciudad_id = uid[7:]
        st_match = re.search('\\bstatus:\\s*(\\d+)', body)
        status = int(st_match.group(1)) if st_match else 0
        es_hq = bool(hq_city and ciudad_id == hq_city)

        if es_hq and status == 0:
            status = 3
            if st_match:
                body = re.sub('\\bstatus:\\s*\\d+', 'status: 3', body, count=1)
            else:
                body = body.rstrip() + '\n status: 3\n'
            hq_activado = True
            modificado = True

        if status > 0:
            garajes_comprados_detectados.add(ciudad_id)
            target_slots = CAPACIDADES_GARAJE.get(status, 5)
            vehs_act = re.findall('vehicles\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', body)
            drvs_act = re.findall('drivers\\[\\d+\\]:\\s*([^\\s\\r\\n]+)', body)
            if len(vehs_act) != target_slots or len(drvs_act) != target_slots:
                vehs = (vehs_act + ['null'] * target_slots)[:target_slots]
                drvs = (drvs_act + ['null'] * target_slots)[:target_slots]
                body = _reemplazar_array_sii(body, 'vehicles', vehs)
                body = _reemplazar_array_sii(body, 'drivers', drvs)
                garajes_reparados += 1
                modificado = True

        return prefijo + body + sufijo if modificado else None

    contenido = transformar_bloques_sii(contenido, _RE_BLOQUE_UNIFICADO_HDR, _procesar_bloque_unificado)

    if nuevos_bloques_job:
        pos_cierre = contenido.rfind('}')
        if pos_cierre != -1:
            texto_bloques = '\n\n' + '\n\n'.join(nuevos_bloques_job) + '\n'
            contenido = contenido[:pos_cierre] + texto_bloques + contenido[pos_cierre:]

    if veh_driver_limpios > 0:
        reparaciones.append(f"Atributos no oficiales 'driver:' limpiados en {veh_driver_limpios} vehículos.")
    if espejos_reparados > 0:
        reparaciones.append(
            f'Configuración de espejos restaurada en {espejos_reparados} camiones de la flota (evita crash en Gestor de camiones).'
        )
    if jobs_reparados > 0:
        reparaciones.append(f'Referencias job_info restauradas en {jobs_reparados} conductores IA.')
    if asg_driver_limpios > 0:
        reparaciones.append(
            f'Referencias legacy assigned_truck normalizadas a esquema ATS 1.62 en {asg_driver_limpios} conductores IA.'
        )
    if hq_activado:
        reparaciones.append(f'Garaje sede principal ({hq_city}) activado a Gran Garaje (5 plazas).')
    if garajes_reparados > 0:
        reparaciones.append(f'Capacidad de plazas sincronizada en {garajes_reparados} garajes.')

    if not tiene_bloque_eco_y_pl:
        return (contenido, reparaciones)

    # Sincronizar garajes comprados en economy.garages
    if hq_city:
        garajes_comprados_detectados.add(hq_city)
    garajes_eco = re.findall('garages\\[\\d+\\]:\\s*garage\\.([^\\s\\r\\n]+)', eco_body_ini)
    set_garajes_eco = set(garajes_eco)
    faltan_en_eco = [g for g in sorted(garajes_comprados_detectados) if g not in set_garajes_eco]
    if faltan_en_eco:
        m_eco_actual = re.search('^(economy\\s*:\\s*[^\\s\\{]+\\s*\\{)(.*?)^(})', contenido, re.M | re.S)
        if m_eco_actual:
            nueva_lista_garajes = garajes_eco + [g for g in faltan_en_eco if g not in garajes_eco]
            nuevo_body_eco = _reemplazar_array_sii(
                m_eco_actual.group(2),
                'garages',
                [f'garage.{g}' for g in nueva_lista_garajes],
            )
            contenido = (
                contenido[:m_eco_actual.start()]
                + m_eco_actual.group(1)
                + nuevo_body_eco
                + m_eco_actual.group(3)
                + contenido[m_eco_actual.end():]
            )
            reparaciones.append(f'Garajes comprados ({len(faltan_en_eco)}) sincronizados en la economía.')

    # Referencias huérfanas en el bloque player
    m_pl_actual = re.search('^(player\\s*:\\s*[^\\s\\{]+\\s*\\{)(.*?)^(})', contenido, re.M | re.S)
    if m_pl_actual:
        pl_act_body = m_pl_actual.group(2)
        nuevo_pl = pl_act_body

        for campo_trk in ('assigned_truck', 'my_truck'):
            m_t = re.search(f'\\b{campo_trk}:\\s*([^\\s\\r\\n]+)', nuevo_pl)
            if m_t:
                tid = m_t.group(1).strip()
                if tid != 'null' and tid not in vehiculos_definidos:
                    nuevo_pl = re.sub(f'\\b{campo_trk}:\\s*[^\\s\\r\\n]+', f'{campo_trk}: null', nuevo_pl, count=1)
                    reparaciones.append(f'Referencia huérfana en player.{campo_trk} limpiada.')

        m_pl_coords = re.search('\\bmy_truck_placement:\\s*(\\([^)]+\\)\\s*\\([^)]+\\))', nuevo_pl)
        coords_actuales = m_pl_coords.group(1).strip() if m_pl_coords else ''
        if '(0, 0, 0)' in coords_actuales and re.search('\\bmy_truck_placement_valid:\\s*true\\b', nuevo_pl):
            nuevo_pl = re.sub('\\bmy_truck_placement_valid:\\s*true\\b', 'my_truck_placement_valid: false', nuevo_pl, count=1)
            reparaciones.append("Estado de colocación corregido a 'false' al tener coordenadas (0,0,0) (evita caer al vacío).")

        if nuevo_pl != pl_act_body:
            contenido = (
                contenido[:m_pl_actual.start()]
                + m_pl_actual.group(1)
                + nuevo_pl
                + m_pl_actual.group(3)
                + contenido[m_pl_actual.end():]
            )

    if placas_reparadas > 0:
        reparaciones.append(f'Matrículas no asignadas reparadas en {placas_reparadas} camiones de la flota.')

    contenido_con_ofertas, inyectadas = asegurar_ofertas_camiones_usados(contenido)
    if inyectadas:
        contenido = contenido_con_ofertas
        reparaciones.append('Catálogo de camiones y marcas incorporado para compra en garajes.')

    contenido_purgado = _purgar_unidades_huerfanas_sii(contenido)
    if contenido_purgado != contenido:
        contenido = contenido_purgado
        reparaciones.append('Unidades huérfanas purgadas para evitar errores de árbol en ATS.')

    return (contenido, reparaciones)


_RE_APERTURA_UNIDAD_SII = re.compile('^[a-zA-Z0-9_]+\\s*:\\s*[^\\s\\{\\"]+\\s*\\{$')
_RE_LLAVE_LINEA_RAPIDO = re.compile('^.*[\\{\\}].*$', re.M)
_RE_HEADER_SIINUNIT = re.compile('^\\ufeff?\\s*SiiNunit\\s*\\r?\\n\\s*\\{(?:\\r?\\n|$)')


def _diagnosticar_error_llaves_sii(contenido: str) -> tuple[bool, str]:
    """Recorre línea por línea para reportar con precisión la línea de cualquier desbalanceo SII."""
    if not contenido or not contenido.strip():
        return (False, 'El contenido SII está vacío.')

    profundidad = 0
    tiene_siinunit = False

    for num_linea, linea in enumerate(contenido.splitlines(), 1):
        s = linea.strip()
        if num_linea == 1:
            s = s.lstrip('﻿')
        if not s:
            continue
        if s == 'SiiNunit' and profundidad == 0:
            tiene_siinunit = True
            continue
        if s == '{' and profundidad == 0:
            if not tiene_siinunit:
                return (False, f"Llave de apertura '{{' inesperada antes de SiiNunit en línea {num_linea}.")
            profundidad = 1
            continue
        if _RE_APERTURA_UNIDAD_SII.match(s):
            if profundidad != 1:
                return (
                    False,
                    f'Bloque de unidad abierto sin cerrar el anterior en línea {num_linea} (profundidad={profundidad}): {s[:60]}',
                )
            profundidad = 2
            continue
        if s == '}':
            profundidad -= 1
            if profundidad < 0:
                return (False, f"Llave de cierre '}}' sobrante en línea {num_linea}.")
            continue
        if profundidad == 0:
            return (False, f'Contenido inesperado fuera de SiiNunit en línea {num_linea}: {s[:60]}')

    if not tiene_siinunit:
        return (False, 'Falta la cabecera SiiNunit.')
    if profundidad != 0:
        return (False, f'Llaves SII desbalanceadas al final del archivo (profundidad={profundidad}).')
    return (True, 'OK')


def verificar_integridad_llaves_sii(contenido: str) -> tuple[bool, str]:
    """Valida que game.sii mantenga el formato SiiNunit (nivel 1) y bloques de unidad balanceados (nivel 2)."""
    if not contenido or not contenido.strip():
        return (False, 'El contenido SII está vacío.')
    if not _RE_HEADER_SIINUNIT.match(contenido[:128]) or not contenido.rstrip().endswith('}'):
        return _diagnosticar_error_llaves_sii(contenido)

    profundidad = 0
    tiene_siinunit = False
    for linea in re_findall_por_trozos(_RE_LLAVE_LINEA_RAPIDO, contenido):
        s = linea.strip()
        if s == '{':
            if profundidad != 0 or tiene_siinunit:
                return _diagnosticar_error_llaves_sii(contenido)
            tiene_siinunit = True
            profundidad = 1
        elif s == '}':
            profundidad -= 1
            if profundidad < 0:
                return _diagnosticar_error_llaves_sii(contenido)
        elif _RE_APERTURA_UNIDAD_SII.match(s):
            if profundidad != 1:
                return _diagnosticar_error_llaves_sii(contenido)
            profundidad = 2

    if profundidad != 0 or not tiene_siinunit:
        return _diagnosticar_error_llaves_sii(contenido)
    return (True, 'OK')


def _guardar_contenido_partida_sano(
    f_game: str,
    contenido: str,
    ruta_guardado: str | None = None,
    sanear: bool = True,
) -> tuple[bool, str]:
    """Guarda game.sii tras verificar su integridad estructural SII (y sanearlo si corresponde)."""
    estaba_saneado = es_archivo_saneado_en_cache(f_game)
    if sanear:
        contenido_final, _ = sanear_y_reparar_partida_sii(contenido)
    else:
        contenido_final = contenido

    ok_llaves, msg_llaves = verificar_integridad_llaves_sii(contenido_final)
    if not ok_llaves:
        raise ValueError(f'Guardado abortado para proteger la partida: {msg_llaves}')

    try:
        lk = obtener_lock_archivo(f_game)
        with lk:
            with open(f_game, 'w', encoding='utf-8') as f:
                f.write(contenido_final)
            invalidar_cache_partida(f_game)
            if sanear or estaba_saneado:
                marcar_archivo_saneado_cache(f_game)
            if ruta_guardado:
                actualizar_metadatos_guardado(ruta_guardado)
        return (True, 'Guardado exitoso')
    except Exception as e:
        return (False, f'Error al guardar partida saneada: {e}')


def comprobar_y_reparar_partida_ats(ruta_guardado: str) -> tuple[bool, list[str], str]:
    """Comprueba la integridad de la partida guardada y repara automáticamente anomalías reales."""
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return (False, [], msg_juego)

    f_game = os.path.join(ruta_guardado, 'game.sii')
    if not os.path.exists(f_game):
        return (False, [], 'No se encontró el archivo game.sii en la partida.')

    todas_reparaciones = []

    try:
        lk = obtener_lock_archivo(f_game)
        with lk:
            desencriptar_archivo_sii(f_game)
            with open(f_game, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
            ok_llaves, msg_llaves = verificar_integridad_llaves_sii(contenido)
            if not ok_llaves:
                return (
                    False,
                    [],
                    f'La partida presenta corrupción estructural SII y no puede repararse automáticamente: {msg_llaves}',
                )
            nuevo_contenido, reps = sanear_y_reparar_partida_sii(contenido)
            if reps:
                ok_post, msg_post = verificar_integridad_llaves_sii(nuevo_contenido)
                if not ok_post:
                    return (False, [], f'La reparación fue abortada para proteger la partida: {msg_post}')
                with open(f_game, 'w', encoding='utf-8') as f:
                    f.write(nuevo_contenido)
                invalidar_cache_partida(f_game)
                actualizar_metadatos_guardado(ruta_guardado)
                todas_reparaciones.extend(reps)
            marcar_archivo_saneado_cache(f_game)
    except Exception as e:
        return (False, [], f'Error al comprobar y reparar partida: {e}')

    dir_save = os.path.dirname(ruta_guardado)
    for hermano in ('autosave', 'quicksave'):
        ruta_hermano = os.path.join(dir_save, hermano)
        f_hermano = os.path.join(ruta_hermano, 'game.sii')
        if os.path.abspath(ruta_hermano) != os.path.abspath(ruta_guardado) and os.path.exists(f_hermano):
            if es_archivo_saneado_en_cache(f_hermano):
                continue
            try:
                lk_h = obtener_lock_archivo(f_hermano)
                with lk_h:
                    desencriptar_archivo_sii(f_hermano)
                    with open(f_hermano, 'r', encoding='utf-8', errors='ignore') as f:
                        c_h = f.read()
                    if not verificar_integridad_llaves_sii(c_h)[0]:
                        continue
                    c_h_nuevo, reps_h = sanear_y_reparar_partida_sii(c_h)
                    if reps_h:
                        if not verificar_integridad_llaves_sii(c_h_nuevo)[0]:
                            continue
                        with open(f_hermano, 'w', encoding='utf-8') as f:
                            f.write(c_h_nuevo)
                        invalidar_cache_partida(f_hermano)
                        actualizar_metadatos_guardado(ruta_hermano)
                        for r in reps_h:
                            if r not in todas_reparaciones:
                                todas_reparaciones.append(r)
                    marcar_archivo_saneado_cache(f_hermano)
            except Exception:
                continue

    if todas_reparaciones:
        return (
            True,
            todas_reparaciones,
            f'Se aplicaron {len(todas_reparaciones)} correcciones de estabilidad a la partida.',
        )
    return (True, [], 'La partida se encuentra íntegra y sin anomalías.')


def saneamiento_pasivo_perfiles_locales_ats() -> list[str]:
    """Inspección preventiva de perfiles locales: sincroniza profile_name y sanea partidas clave sin competir con la UI."""
    juego_ok, _ = verificar_juego_cerrado()
    if not juego_ok:
        return []

    ruta_locales = obtener_ruta_ats('profiles')
    if not ruta_locales or not os.path.isdir(ruta_locales):
        return []

    resumen = []
    try:
        subcarpetas = [
            os.path.join(ruta_locales, d)
            for d in os.listdir(ruta_locales)
            if os.path.isdir(os.path.join(ruta_locales, d))
        ]
    except Exception:
        return []

    for ruta_p in subcarpetas:
        try:
            nombre_carpeta = os.path.basename(ruta_p)
            try:
                nombre_esperado = bytes.fromhex(nombre_carpeta).decode('utf-8', errors='ignore').strip()
            except Exception:
                nombre_esperado = None

            if nombre_esperado:
                for arch_prof in ('profile.sii', 'profile.bak.sii'):
                    fp = os.path.join(ruta_p, arch_prof)
                    if os.path.exists(fp) and not es_archivo_saneado_en_cache(fp):
                        desencriptar_archivo_sii(fp)
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            c = f.read()
                        m = re.search('profile_name:\\s*(?:"([^"]*)"|([^\\r\\n]+))', c)
                        nom_actual = (m.group(1) or m.group(2) or '').strip() if m else None
                        if nom_actual != nombre_esperado:
                            nuevo_val = f'profile_name: "{nombre_esperado}"'
                            if m:
                                c = re.sub('profile_name:\\s*.*', nuevo_val, c, count=1)
                            else:
                                m_up = re.search('(user_profile\\s*:\\s*[^{]+\\{)', c)
                                if m_up:
                                    c = c[:m_up.end()] + f'\n {nuevo_val}' + c[m_up.end():]
                            with open(fp, 'w', encoding='utf-8') as f:
                                f.write(c)
                            resumen.append(f"Nombre sincronizado en {arch_prof} para '{nombre_esperado}'")
                        marcar_archivo_saneado_cache(fp)

            dir_save = os.path.join(ruta_p, 'save')
            if os.path.isdir(dir_save):
                guardados_a_revisar = []
                for sub in ('autosave', 'quicksave'):
                    p_sub = os.path.join(dir_save, sub)
                    if os.path.isdir(p_sub) and os.path.exists(os.path.join(p_sub, 'game.sii')):
                        guardados_a_revisar.append(p_sub)
                if not guardados_a_revisar:
                    for sub in os.listdir(dir_save):
                        p_sub = os.path.join(dir_save, sub)
                        if os.path.isdir(p_sub) and os.path.exists(os.path.join(p_sub, 'game.sii')):
                            guardados_a_revisar.append(p_sub)
                            break

                for r_g in guardados_a_revisar:
                    f_g = os.path.join(r_g, 'game.sii')
                    if es_archivo_saneado_en_cache(f_g):
                        continue
                    lk_g = obtener_lock_archivo(f_g)
                    if not lk_g.acquire(blocking=False):
                        continue
                    try:
                        desencriptar_archivo_sii(f_g)
                        with open(f_g, 'r', encoding='utf-8', errors='ignore') as f:
                            c_g = f.read()
                        if not verificar_integridad_llaves_sii(c_g)[0]:
                            continue
                        c_g_nuevo, reps_g = sanear_y_reparar_partida_sii(c_g)
                        if reps_g:
                            ok_ll, _ = verificar_integridad_llaves_sii(c_g_nuevo)
                            if ok_ll:
                                with open(f_g, 'w', encoding='utf-8') as f:
                                    f.write(c_g_nuevo)
                                invalidar_cache_partida(f_g)
                                actualizar_metadatos_guardado(r_g)
                                resumen.extend(reps_g)
                        marcar_archivo_saneado_cache(f_g)
                    finally:
                        lk_g.release()
        except Exception as e:
            print(f"[WARN] Saneamiento pasivo en '{ruta_p}': {e}")

    return resumen

import re
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    CAPACIDADES_GARAJE,
    _desbloquear_pantallas_sii,
    _reemplazar_array_sii,
    abrir_partida_para_edicion,
    actualizar_metadatos_guardado,
    asegurar_y_resetear_driver_jobs_idle,
    es_archivo_saneado_en_cache,
    iterar_bloques_sii,
    obtener_contexto_jugador,
    transformar_bloques_sii,
)

_RE_GARAGE_HDR = re.compile(r'^garage\s*:\s*garage\.([^\s\{]+)\s*\{', re.M)
_RE_DRIVER_AI_HDR = re.compile(r'^driver_ai\s*:\s*(driver\.[^\s\{]+)\s*\{', re.M)


def _calcular_skills_por_calificacion(calificacion: float) -> tuple[int, int, int, int, int, int, int]:
    """Calcula (adr_mask, long_dist, heavy, fragile, urgent, mechanical, xp) para una calificación de 1.0 a 10.0."""
    calif = max(1.0, min(10.0, float(calificacion)))
    if calif >= 10.0:
        return 63, 6, 6, 6, 6, 6, 585000
    if calif <= 1.0:
        return 1, 0, 0, 0, 0, 0, 2500

    total_pts = max(1, min(36, int(round((calif - 0.8) / 9.2 * 36))))
    base = total_pts // 6
    rem = total_pts % 6
    puntos = [base + (1 if i < rem else 0) for i in range(6)]
    adr_mask = (1 << puntos[0]) - 1
    xp = max(2500, int(round(total_pts / 36.0 * 585000)))
    return adr_mask, puntos[1], puntos[2], puntos[3], puntos[4], puntos[5], xp


def _actualizar_arrays_player_conductores(
    contenido: str,
    pl_drivers: list[str],
    pl_flags: list[str],
    pl_readiness: list[str],
    pl_undrivable: list[str],
) -> str:
    m_pl = re.search(r'^(player\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
    if not m_pl:
        return contenido
    pl_body = m_pl.group(2)
    pl_body = _reemplazar_array_sii(pl_body, 'drivers', pl_drivers)
    pl_body = _reemplazar_array_sii(pl_body, 'driver_flags', pl_flags)
    pl_body = _reemplazar_array_sii(pl_body, 'driver_readiness_timer', pl_readiness)
    pl_body = _reemplazar_array_sii(pl_body, 'driver_undrivable_truck_timers', pl_undrivable)
    return contenido[:m_pl.start()] + m_pl.group(1) + pl_body + m_pl.group(3) + contenido[m_pl.end():]


def entrenar_conductores_ia(ruta_guardado: str, calificacion: float = 10.0) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        entrenados = 0
        adr_mask, l_dist, hvy, frg, urg, mech, target_xp = _calcular_skills_por_calificacion(calificacion)

        def _mejorar_driver(_m_hdr, pref, d_body, suf):
            nonlocal entrenados
            d_body = re.sub(r'\badr:\s*\d+', f'adr: {adr_mask}', d_body, count=1)
            d_body = re.sub(r'\blong_dist:\s*\d+', f'long_dist: {l_dist}', d_body, count=1)
            d_body = re.sub(r'\bheavy:\s*\d+', f'heavy: {hvy}', d_body, count=1)
            d_body = re.sub(r'\bfragile:\s*\d+', f'fragile: {frg}', d_body, count=1)
            d_body = re.sub(r'\burgent:\s*\d+', f'urgent: {urg}', d_body, count=1)
            d_body = re.sub(r'\bmechanical:\s*\d+', f'mechanical: {mech}', d_body, count=1)
            d_body = re.sub(r'\bexperience_points:\s*\d+', f'experience_points: {target_xp}', d_body, count=1)
            entrenados += 1
            return pref + d_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _mejorar_driver)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)
        return True, f'Se actualizaron las habilidades de {entrenados} conductores a Calificación {calificacion:.1f}.'
    except Exception as e:
        return False, f'Error al entrenar conductores: {e}'


def contratar_conductores_ia(
    ruta_guardado: str,
    cantidad: int | None = None,
    entrenar_max: bool = True,
    calificacion: float = 10.0,
) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        m_pl = re.search(r'^(player\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco or not m_pl:
            return False, 'No se encontraron los bloques economy/player en la partida.'

        eco_body = m_eco.group(2)
        pl_body = m_pl.group(2)
        ctx = obtener_contexto_jugador(contenido)
        hq_city = ctx['hq_city']
        player_driver_id = ctx['player_driver_id']
        veh_activo = ctx['veh_activo']

        pool_drivers = re.findall(r'driver_pool\[\d+\]:\s*([^\s\r\n]+)', eco_body)
        raw_offers = re.findall(r'drivers_offer\[\d+\]:\s*([^\s\r\n]+)', eco_body)
        pl_drivers = re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_flags = re.findall(r'driver_flags\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_readiness = re.findall(r'driver_readiness_timer\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_undrivable = re.findall(r'driver_undrivable_truck_timers\[\d+\]:\s*([^\s\r\n]+)', pl_body)

        disponibles = []
        vistos = set(pl_drivers)
        for d in raw_offers + pool_drivers:
            if d != 'null' and d not in vistos:
                disponibles.append(d)
                vistos.add(d)

        if not disponibles:
            return False, 'No hay más conductores disponibles en las agencias de empleo de esta partida.'

        slots_sin_camion = []
        slots_con_camion = []
        for m_g, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_GARAGE_HDR):
            ciudad_id = m_g.group(1)
            g_body = contenido[bs:be]
            m_st = re.search(r'\bstatus:\s*(\d+)', g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            if st not in (1, 2, 3, 6) or cap <= 0:
                continue
            v_pad = (re.findall(r'vehicles\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            d_pad = (re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            for idx in range(cap):
                if ciudad_id == hq_city and idx == 0 and (player_driver_id or veh_activo):
                    continue
                if d_pad[idx] == 'null':
                    if v_pad[idx] == 'null':
                        slots_sin_camion.append((ciudad_id, idx))
                    else:
                        slots_con_camion.append((ciudad_id, idx))

        slots_libres = slots_sin_camion + slots_con_camion
        if not slots_libres:
            return False, (
                'No tienes plazas libres para conductores en tus garajes. '
                'Compra o amplía un garaje primero en la pestaña Garajes.'
            )

        max_posible = min(len(slots_libres), len(disponibles))
        n_a_contratar = max_posible if cantidad is None else min(int(cantidad), max_posible)
        if n_a_contratar <= 0:
            return False, 'No se pudo contratar conductores.'

        elegidos = disponibles[:n_a_contratar]
        asignaciones = slots_libres[:n_a_contratar]

        por_ciudad = {}
        ciudad_de_driver = {}
        for d_id, (ciudad_id, slot_idx) in zip(elegidos, asignaciones):
            por_ciudad.setdefault(ciudad_id, {})[slot_idx] = d_id
            ciudad_de_driver[d_id] = ciudad_id

        def _actualizar_garaje_hire(m_hdr, pref, g_body, suf):
            c_id = m_hdr.group(1)
            if c_id not in por_ciudad:
                return None
            m_st = re.search(r'\bstatus:\s*(\d+)', g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            d_pad = (re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            for s_idx, drv_id in por_ciudad[c_id].items():
                if 0 <= s_idx < cap:
                    d_pad[s_idx] = drv_id
            g_body = _reemplazar_array_sii(g_body, 'drivers', d_pad)
            return pref + g_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _actualizar_garaje_hire)

        set_elegidos = set(elegidos)
        nuevo_pool = [d for d in pool_drivers if d not in set_elegidos]
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if m_eco:
            eco_body = _reemplazar_array_sii(m_eco.group(2), 'driver_pool', nuevo_pool)
            if raw_offers:
                nuevas_offers = ['null' if d in set_elegidos else d for d in raw_offers]
                eco_body = _reemplazar_array_sii(eco_body, 'drivers_offer', nuevas_offers)
            eco_body = _desbloquear_pantallas_sii(
                eco_body,
                {'screen.recruit', 'screen.recruit_map', 'screen.driverman', 'overview.compman_w'},
            )
            contenido = contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]

        pl_flags.extend(['0'] * max(0, len(pl_drivers) - len(pl_flags)))
        pl_readiness.extend(['0'] * max(0, len(pl_drivers) - len(pl_readiness)))
        pl_undrivable.extend(['0'] * max(0, len(pl_drivers) - len(pl_undrivable)))

        for d_id in elegidos:
            pl_drivers.append(d_id)
            pl_flags.append('0')
            pl_readiness.append('0')
            pl_undrivable.append('0')

        contenido = _actualizar_arrays_player_conductores(
            contenido, pl_drivers, pl_flags, pl_readiness, pl_undrivable
        )

        def _actualizar_driver_hire(m_hdr, pref, d_body, suf):
            d_id = m_hdr.group(1)
            if d_id not in ciudad_de_driver:
                return None
            c_id = ciudad_de_driver[d_id]
            d_body = re.sub(r'\bhometown:\s*[^\s\r\n]+', f'hometown: {c_id}', d_body, count=1)
            d_body = re.sub(r'\bcurrent_city:\s*[^\s\r\n]+', f'current_city: {c_id}', d_body, count=1)
            d_body = re.sub(r'\bassigned_truck:\s*[^\s\r\n]+', 'assigned_truck: null', d_body, count=1)
            d_body = re.sub(r'\bstate:\s*\d+', 'state: 1', d_body, count=1)
            d_body = re.sub(r'\bon_duty_timer:\s*[^\s\r\n]+', 'on_duty_timer: 0', d_body, count=1)
            if entrenar_max:
                adr_mask, l_dist, hvy, frg, urg, mech, xp_val = _calcular_skills_por_calificacion(calificacion)
                d_body = re.sub(r'\badr:\s*\d+', f'adr: {adr_mask}', d_body, count=1)
                d_body = re.sub(r'\blong_dist:\s*\d+', f'long_dist: {l_dist}', d_body, count=1)
                d_body = re.sub(r'\bheavy:\s*\d+', f'heavy: {hvy}', d_body, count=1)
                d_body = re.sub(r'\bfragile:\s*\d+', f'fragile: {frg}', d_body, count=1)
                d_body = re.sub(r'\burgent:\s*\d+', f'urgent: {urg}', d_body, count=1)
                d_body = re.sub(r'\bmechanical:\s*\d+', f'mechanical: {mech}', d_body, count=1)
                d_body = re.sub(r'\bexperience_points:\s*\d+', f'experience_points: {xp_val}', d_body, count=1)
            return pref + d_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _actualizar_driver_hire)
        contenido, _ = asegurar_y_resetear_driver_jobs_idle(
            contenido,
            target_driver_ids=set_elegidos,
            resetear_existentes=True,
        )

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)

        nota = f' con Calificación {calificacion:.1f}' if entrenar_max else ''
        return True, f'Se contrataron {n_a_contratar} conductores{nota} y se asignaron a tus garajes.'
    except Exception as e:
        return False, f'Error al contratar conductores: {e}'


def despedir_conductores_ia(ruta_guardado: str, solo_sin_camion: bool = True) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        m_pl = re.search(r'^(player\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco or not m_pl:
            return False, 'No se encontraron los bloques economy/player en la partida.'

        pl_body = m_pl.group(2)
        pl_drivers = re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_flags = re.findall(r'driver_flags\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_readiness = re.findall(r'driver_readiness_timer\[\d+\]:\s*([^\s\r\n]+)', pl_body)
        pl_undrivable = re.findall(r'driver_undrivable_truck_timers\[\d+\]:\s*([^\s\r\n]+)', pl_body)

        player_driver_id = pl_drivers[0] if pl_drivers else ''
        despedidos = []
        set_despedidos = set()

        def _limpiar_garaje_dismiss(_m_hdr, pref, g_body, suf):
            m_st = re.search(r'\bstatus:\s*(\d+)', g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            if st not in (1, 2, 3, 6) or cap <= 0:
                return None
            v_pad = (re.findall(r'vehicles\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            d_pad = (re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            cambio = False
            for idx in range(cap):
                d_id = d_pad[idx]
                if d_id != 'null' and d_id != player_driver_id:
                    if not solo_sin_camion or v_pad[idx] == 'null':
                        d_pad[idx] = 'null'
                        cambio = True
                        if d_id not in set_despedidos:
                            set_despedidos.add(d_id)
                            despedidos.append(d_id)
            if not cambio:
                return None
            g_body = _reemplazar_array_sii(g_body, 'drivers', d_pad)
            return pref + g_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _limpiar_garaje_dismiss)

        if not despedidos:
            if solo_sin_camion:
                return False, 'No tienes conductores sin camión asignado para despedir.'
            return False, 'No tienes conductores contratados para despedir.'

        pl_flags.extend(['0'] * max(0, len(pl_drivers) - len(pl_flags)))
        pl_readiness.extend(['0'] * max(0, len(pl_drivers) - len(pl_readiness)))
        pl_undrivable.extend(['0'] * max(0, len(pl_drivers) - len(pl_undrivable)))

        n_drv, n_flg, n_rdy, n_und = [], [], [], []
        for i, d_id in enumerate(pl_drivers):
            if i == 0 or d_id not in set_despedidos:
                n_drv.append(d_id)
                n_flg.append(pl_flags[i])
                n_rdy.append(pl_readiness[i])
                n_und.append(pl_undrivable[i])

        contenido = _actualizar_arrays_player_conductores(contenido, n_drv, n_flg, n_rdy, n_und)

        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if m_eco:
            eco_body = m_eco.group(2)
            pool_drivers = re.findall(r'driver_pool\[\d+\]:\s*([^\s\r\n]+)', eco_body)
            existentes = set(pool_drivers)
            for d_id in despedidos:
                if d_id not in existentes:
                    pool_drivers.append(d_id)
                    existentes.add(d_id)
            eco_body = _reemplazar_array_sii(eco_body, 'driver_pool', pool_drivers)
            contenido = contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]

        def _reset_driver_ai(m_hdr, pref, d_body, suf):
            d_id = m_hdr.group(1)
            if d_id not in set_despedidos:
                return None
            d_body = re.sub(r'\bhometown:\s*[^\s\r\n]+', 'hometown: ""', d_body, count=1)
            d_body = re.sub(r'\bcurrent_city:\s*[^\s\r\n]+', 'current_city: ""', d_body, count=1)
            d_body = re.sub(r'\bassigned_truck:\s*[^\s\r\n]+', 'assigned_truck: null', d_body, count=1)
            d_body = re.sub(r'\bstate:\s*\d+', 'state: 1', d_body, count=1)
            d_body = re.sub(r'\bon_duty_timer:\s*[^\s\r\n]+', 'on_duty_timer: 0', d_body, count=1)
            return pref + d_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _reset_driver_ai)
        contenido, _ = asegurar_y_resetear_driver_jobs_idle(
            contenido,
            target_driver_ids=set_despedidos,
            resetear_existentes=True,
        )

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)
        if solo_sin_camion:
            return True, f'Se despidieron {len(despedidos)} conductores sin camión asignado y regresaron a las agencias.'
        return True, f'Se despidieron {len(despedidos)} conductores contratados y regresaron a las agencias.'
    except Exception as e:
        return False, f'Error al despedir conductores: {e}'


def asignar_conductores_a_camiones(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        ctx = obtener_contexto_jugador(contenido)
        hired_ids = ctx['hired_ids']
        if not hired_ids:
            return False, 'No tienes conductores contratados en tu empresa para asignar.'

        hq_city = ctx['hq_city']
        player_driver_id = ctx['player_driver_id']
        veh_activo = ctx['veh_activo']

        driver_a_camion = {}
        camiones_ocupados = set()
        garajes_datos = {}
        candidatos_camiones_libres = []

        for m_g, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_GARAGE_HDR):
            c_id = m_g.group(1)
            g_body = contenido[bs:be]
            m_st = re.search(r'\bstatus:\s*(\d+)', g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            raw_v_all = re.findall(r'vehicles\[\d+\]:\s*([^\s\r\n]+)', g_body)
            raw_d_all = re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body)
            for d_p, v_p in zip(raw_d_all, raw_v_all):
                if d_p != 'null' and v_p != 'null':
                    driver_a_camion[d_p] = v_p
                    camiones_ocupados.add(v_p)

            if st not in (1, 2, 3, 6) or cap <= 0:
                continue
            raw_v = (raw_v_all + ['null'] * cap)[:cap]
            raw_d = (raw_d_all + ['null'] * cap)[:cap]
            garajes_datos[c_id] = {'cap': cap, 'vehs': raw_v, 'drvs': raw_d}

            for idx in range(cap):
                v_id = raw_v[idx]
                d_id = raw_d[idx]
                if v_id in ctx['vehs_personales'] or (c_id == hq_city and idx == 0 and (player_driver_id or veh_activo)):
                    continue
                if v_id != 'null' and d_id == 'null':
                    candidatos_camiones_libres.append((c_id, idx, v_id))

        choferes_libres = {d for d in hired_ids if d not in driver_a_camion}
        if not choferes_libres:
            return False, 'Todos tus conductores ya tienen un camión asignado.'

        camiones_libres_lista = [
            (c_id, idx, v_id)
            for c_id, idx, v_id in candidatos_camiones_libres
            if v_id not in camiones_ocupados
        ]
        if not camiones_libres_lista:
            return False, 'No hay camiones vacíos disponibles en tus garajes para asignar.'

        asignaciones = {}
        choferes_pendientes = set(choferes_libres)
        garajes_modificados = set()

        camiones_por_garaje = {}
        for c_id, idx_t, v_id in camiones_libres_lista:
            camiones_por_garaje.setdefault(c_id, []).append((idx_t, v_id))

        camiones_restantes = []
        for c_id, lista_t in camiones_por_garaje.items():
            drvs_en_g = garajes_datos[c_id]['drvs']
            for idx_t, v_id in lista_t:
                candidato_d = None
                idx_origen = None
                for idx_d, d_id in enumerate(drvs_en_g):
                    if d_id in choferes_pendientes:
                        candidato_d = d_id
                        idx_origen = idx_d
                        break
                if candidato_d and idx_origen is not None:
                    asignaciones[candidato_d] = (c_id, v_id)
                    choferes_pendientes.remove(candidato_d)
                    drvs_en_g[idx_origen] = 'null'
                    drvs_en_g[idx_t] = candidato_d
                    garajes_modificados.add(c_id)
                else:
                    camiones_restantes.append((c_id, idx_t, v_id))

        for c_id, idx_t, v_id in camiones_restantes:
            if not choferes_pendientes:
                break
            drv_id = next(iter(choferes_pendientes))
            choferes_pendientes.remove(drv_id)
            asignaciones[drv_id] = (c_id, v_id)
            for g_cid, g_info in garajes_datos.items():
                if drv_id in g_info['drvs']:
                    g_info['drvs'][g_info['drvs'].index(drv_id)] = 'null'
                    garajes_modificados.add(g_cid)
                    break
            garajes_datos[c_id]['drvs'][idx_t] = drv_id
            garajes_modificados.add(c_id)

        if not asignaciones:
            return False, 'No se pudo emparejar ningún conductor con los camiones disponibles.'

        def _actualizar_garaje(m_hdr, pref, g_body, suf):
            c_id = m_hdr.group(1)
            if c_id not in garajes_modificados:
                return None
            return pref + _reemplazar_array_sii(g_body, 'drivers', garajes_datos[c_id]['drvs']) + suf

        contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _actualizar_garaje)

        def _actualizar_drv_asig(m_hdr, pref, d_body, suf):
            d_id = m_hdr.group(1)
            if d_id not in asignaciones:
                return None
            nueva_c, _ = asignaciones[d_id]
            d_body = re.sub(r'\bhometown:\s*[^\s\r\n]+', f'hometown: {nueva_c}', d_body, count=1)
            d_body = re.sub(r'\bcurrent_city:\s*[^\s\r\n]+', f'current_city: {nueva_c}', d_body, count=1)
            d_body = re.sub(r'\bassigned_truck:\s*[^\s\r\n]+', 'assigned_truck: null', d_body, count=1)
            d_body = re.sub(r'\bon_duty_timer:\s*[^\s\r\n]+', 'on_duty_timer: 0', d_body, count=1)
            return pref + d_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _actualizar_drv_asig)
        contenido, _ = asegurar_y_resetear_driver_jobs_idle(
            contenido,
            target_driver_ids=set(asignaciones.keys()),
            resetear_existentes=False,
        )

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)
        return True, f'Se asignaron con éxito {len(asignaciones)} conductores a camiones disponibles.'
    except Exception as e:
        return False, f'Error al asignar conductores: {e}'


def desasignar_conductores_de_camiones(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        ctx = obtener_contexto_jugador(contenido)
        hired_ids = ctx['hired_ids']
        if not hired_ids:
            return False, 'No tienes conductores contratados para desasignar.'

        hq_city = ctx['hq_city']
        player_driver_id = ctx['player_driver_id']
        veh_activo = ctx['veh_activo']

        garajes_datos = {}
        plazas_vacias = []
        pares_activos = []

        for m_g, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_GARAGE_HDR):
            c_id = m_g.group(1)
            g_body = contenido[bs:be]
            m_st = re.search(r'\bstatus:\s*(\d+)', g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            if st not in (1, 2, 3, 6) or cap <= 0:
                continue
            raw_v = (re.findall(r'vehicles\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            raw_d = (re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body) + ['null'] * cap)[:cap]
            garajes_datos[c_id] = {'cap': cap, 'vehs': raw_v, 'drvs': raw_d}

            for idx in range(cap):
                if c_id == hq_city and idx == 0 and (player_driver_id or veh_activo):
                    continue
                if raw_v[idx] == 'null' and raw_d[idx] == 'null':
                    plazas_vacias.append((c_id, idx))
                elif raw_v[idx] != 'null' and raw_d[idx] in hired_ids:
                    pares_activos.append((c_id, idx, raw_d[idx]))

        drivers_desasignados = set()
        nueva_ciudad_drv = {}
        garajes_modificados = set()

        for (c_orig, idx_orig, d_id), (c_dest, idx_dest) in zip(pares_activos, plazas_vacias):
            garajes_datos[c_orig]['drvs'][idx_orig] = 'null'
            garajes_datos[c_dest]['drvs'][idx_dest] = d_id
            garajes_modificados.add(c_orig)
            garajes_modificados.add(c_dest)
            drivers_desasignados.add(d_id)
            nueva_ciudad_drv[d_id] = c_dest

        def _guardar_garajes(m_hdr, pref, g_body, suf):
            c_id = m_hdr.group(1)
            if c_id not in garajes_modificados:
                return None
            return pref + _reemplazar_array_sii(g_body, 'drivers', garajes_datos[c_id]['drvs']) + suf

        if drivers_desasignados:
            contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _guardar_garajes)

        legacy_count = 0

        def _desasignar_drv(m_hdr, pref, d_body, suf):
            nonlocal legacy_count
            d_id = m_hdr.group(1)
            if d_id not in hired_ids:
                return None
            m_trk = re.search(r'\bassigned_truck:\s*([^\s\r\n]+)', d_body)
            tiene_legacy = bool(m_trk and m_trk.group(1) != 'null')
            if not tiene_legacy and d_id not in drivers_desasignados:
                return None
            if tiene_legacy and d_id not in drivers_desasignados:
                legacy_count += 1
            drivers_desasignados.add(d_id)
            if d_id in nueva_ciudad_drv:
                nc = nueva_ciudad_drv[d_id]
                d_body = re.sub(r'\bhometown:\s*[^\s\r\n]+', f'hometown: {nc}', d_body, count=1)
                d_body = re.sub(r'\bcurrent_city:\s*[^\s\r\n]+', f'current_city: {nc}', d_body, count=1)
            d_body = re.sub(r'\bassigned_truck:\s*[^\s\r\n]+', 'assigned_truck: null', d_body, count=1)
            d_body = re.sub(r'\bon_duty_timer:\s*[^\s\r\n]+', 'on_duty_timer: 0', d_body, count=1)
            d_body = re.sub(r'\bstate:\s*\d+', 'state: 1', d_body, count=1)
            return pref + d_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _desasignar_drv)

        total_desasignados = len(drivers_desasignados)
        if total_desasignados == 0:
            if pares_activos and not plazas_vacias:
                return False, 'No hay plazas libres sin camión en tus garajes para reubicar conductores.'
            return False, 'Ninguno de tus conductores tenía un camión asignado.'

        contenido, _ = asegurar_y_resetear_driver_jobs_idle(
            contenido,
            target_driver_ids=drivers_desasignados,
            resetear_existentes=True,
        )

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)
        return True, f'Se desasignaron con éxito {total_desasignados} conductores de sus camiones.'
    except Exception as e:
        return False, f'Error al desasignar conductores: {e}'

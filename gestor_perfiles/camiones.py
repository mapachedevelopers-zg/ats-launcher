import random
import re
from gestor_perfiles.lectura import _extraer_info_camion
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    CAPACIDADES_GARAJE,
    MIRRORS_9_BLOQUE,
    _desbloquear_pantallas_sii,
    _reemplazar_array_sii,
    abrir_partida_para_edicion,
    actualizar_metadatos_guardado,
    asegurar_y_resetear_driver_jobs_idle,
    eliminar_bloques_por_id_sii,
    es_archivo_saneado_en_cache,
    extraer_bloques_por_ids_sii,
    generar_generador_ids_sii,
    iterar_bloques_sii,
    obtener_contexto_jugador,
    re_findall_por_trozos,
    transformar_bloques_sii,
)

_RE_GARAGE_HDR = re.compile(r"^garage\s*:\s*garage\.([^\s\{]+)\s*\{", re.M)
_RE_GARAGE_O_OFFER_HDR = re.compile(r"^(garage|used_truck_offer)\s*:\s*([^\s\{]+)\s*\{", re.M)
_RE_VEHICLE_HDR = re.compile(r"^vehicle\s*:\s*([^\s\{]+)\s*\{", re.M)
_RE_DRIVER_AI_HDR = re.compile(r"^driver_ai\s*:\s*(driver\.[^\s\{]+)\s*\{", re.M)
_RE_PROFIT_LOG_HDR = re.compile(r"^profit_log\s*:\s*(_nameless\.[0-9a-fA-F\.]+)\s*\{", re.M)
_RE_VEH_ACC_DP = re.compile(r'^vehicle_\w*accessory\s*:\s*([^\s\{]+)\s*\{\s*data_path:\s*"([^"]*)"', re.M)


def _recolectar_slots_y_ofertas_compra(
    contenido: str,
    hq_city: str,
    player_driver_id: str,
    veh_activo: str,
) -> tuple[list[tuple[str, int]], dict[str, dict]]:
    """Escanea en un solo paso por trozos los espacios libres en garajes y las ofertas de usados."""
    slots_vacios_sin_drv = []
    slots_vacios_con_drv = []
    ofertas_info = {}

    for m_hdr, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_GARAGE_O_OFFER_HDR):
        utype, uid = m_hdr.group(1), m_hdr.group(2)
        body = contenido[bs:be]
        if utype == "garage":
            cid = uid[7:] if uid.startswith("garage.") else uid
            m_st = re.search(r"\bstatus:\s*(\d+)", body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            if st not in (1, 2, 3, 6) or cap <= 0:
                continue
            raw_v = (re.findall(r"vehicles\[\d+\]:\s*([^\s\r\n]+)", body) + ["null"] * cap)[:cap]
            raw_d = (re.findall(r"drivers\[\d+\]:\s*([^\s\r\n]+)", body) + ["null"] * cap)[:cap]
            for idx in range(cap):
                if cid == hq_city and idx == 0 and (player_driver_id or veh_activo):
                    continue
                if raw_v[idx] == "null":
                    if raw_d[idx] == "null":
                        slots_vacios_sin_drv.append((cid, idx))
                    else:
                        slots_vacios_con_drv.append((cid, idx))
        else:
            mt = re.search(r"\btruck:\s*([^\s\r\n]+)", body)
            mp = re.search(r"\bprice:\s*(\d+)", body)
            if mt and mt.group(1) != "null":
                ofertas_info[uid] = {
                    "truck_id": mt.group(1),
                    "price": int(mp.group(1)) if mp else 0,
                }

    return slots_vacios_sin_drv + slots_vacios_con_drv, ofertas_info


def _ejecutar_compra_camiones_contenido(
    contenido: str,
    f_game: str,
    ruta_guardado: str,
    estaba_saneado: bool,
    compras: list[tuple[str, int]],
    saldo_actual: int,
    slots_disponibles: list[tuple[str, int]],
    ofertas_info: dict[str, dict],
) -> tuple[bool, str]:
    """Clona las plantillas de vehículos/accesorios y guarda las compras en un único pase."""
    unidades_a_crear = []
    costo_total = 0
    for oid, cant in compras:
        if cant <= 0 or oid not in ofertas_info:
            continue
        inf = ofertas_info[oid]
        for _ in range(cant):
            if len(unidades_a_crear) >= len(slots_disponibles):
                break
            if costo_total + inf["price"] > saldo_actual:
                break
            unidades_a_crear.append((inf["truck_id"], inf["price"]))
            costo_total += inf["price"]

    if not unidades_a_crear:
        return False, "No tienes suficiente saldo disponible o espacio en garajes para realizar esta compra."

    tids_solicitados = {tid for tid, _ in unidades_a_crear}
    bloques_veh = extraer_bloques_por_ids_sii(contenido, tids_solicitados, tipos_objetivo={"vehicle"})
    mapa_veh_compra = {uid: body for uid, (_t, body) in bloques_veh.items()}

    aids_necesarios = set()
    for vb_c in mapa_veh_compra.values():
        aids_necesarios.update(re.findall(r"accessories\[\d+\]:\s*([^\s\r\n]+)", vb_c))

    mapa_acc_bloques = {}
    if aids_necesarios:
        mapa_acc_bloques = extraer_bloques_por_ids_sii(contenido, aids_necesarios)

    plantillas_veh = {}
    for tid in tids_solicitados:
        vbody = mapa_veh_compra.get(tid)
        if not vbody:
            continue
        acc_ids = re.findall(r"accessories\[\d+\]:\s*([^\s\r\n]+)", vbody)
        acc_bloques = [
            (aid, *mapa_acc_bloques[aid]) for aid in acc_ids if aid in mapa_acc_bloques
        ]
        plantillas_veh[tid] = (vbody, acc_bloques)

    _nuevo_id_sii = generar_generador_ids_sii(contenido)
    bloques_nuevos = []
    nuevos_trucks_player = []
    nuevos_plogs_player = []
    asignacion_garajes = {}

    for (tid, _precio), (cid, slot_idx) in zip(unidades_a_crear, slots_disponibles):
        if tid not in plantillas_veh:
            continue
        vbody_base, acc_bloques = plantillas_veh[tid]
        new_vid = _nuevo_id_sii()
        new_plog = _nuevo_id_sii()

        nuevos_acc_ids = []
        for _old_aid, tipo_acc, acc_body in acc_bloques:
            new_aid = _nuevo_id_sii()
            nuevos_acc_ids.append(new_aid)
            acc_body = acc_body.replace("/def/vehicle/r_cover/aero_lt.sii", "/def/vehicle/r_cover/rear_hub_cover_01.sii")
            bloques_nuevos.append(f"{tipo_acc} : {new_aid} {{{acc_body}}}")

        vbody_clon = _reemplazar_array_sii(vbody_base, "accessories", nuevos_acc_ids)
        vbody_clon = re.sub(r"\bfuel_relative:\s*[^\s\r\n]+", "fuel_relative: 1", vbody_clon)
        for campo_w in (
            "engine_wear", "transmission_wear", "cabin_wear", "chassis_wear",
            "engine_wear_unfixable", "transmission_wear_unfixable",
            "cabin_wear_unfixable", "chassis_wear_unfixable",
        ):
            vbody_clon = re.sub(f"\\b{campo_w}:\\s*[^\\s\\r\\n]+", f"{campo_w}: 0", vbody_clon)
        vbody_clon = re.sub(r"(wheels_wear\[\d+\]:)\s*[^\s\r\n]+", r"\1 0", vbody_clon)
        vbody_clon = re.sub(r"(wheels_wear_unfixable\[\d+\]:)\s*[^\s\r\n]+", r"\1 0", vbody_clon)
        vbody_clon = re.sub(r"\bpurchase_time:\s*\d+", "purchase_time: 0", vbody_clon)

        m_rot_base = re.search(r"^[ \t]*user_mirror_rot:\s*(\d+)", vbody_clon, re.M)
        rot_base_val = int(m_rot_base.group(1)) if m_rot_base else 0
        if rot_base_val == 0:
            if m_rot_base:
                vbody_clon = re.sub(
                    r"^[ \t]*user_mirror_rot:\s*\d+(?:\r?\n[ \t]*user_mirror_rot\[\d+\]:\s*[^\r\n]+)*",
                    MIRRORS_9_BLOQUE,
                    vbody_clon,
                    count=1,
                    flags=re.M,
                )
            else:
                vbody_clon = MIRRORS_9_BLOQUE + "\n" + vbody_clon

        placa_clon = f"ATS{random.randint(100, 999)}|california"
        if re.search(r'\blicense_plate:\s*"[^"]*"', vbody_clon):
            vbody_clon = re.sub(r'\blicense_plate:\s*"[^"]*"', f'license_plate: "{placa_clon}"', vbody_clon, count=1)
        else:
            vbody_clon = vbody_clon.rstrip() + f'\n license_plate: "{placa_clon}"\n'

        bloques_nuevos.append(f"vehicle : {new_vid} {{{vbody_clon}}}")
        bloques_nuevos.append(
            f"profit_log : {new_plog} {{\n stats_data: 0\n acc_distance_free: 0\n acc_distance_on_job: 0\n history_age: nil\n}}"
        )

        nuevos_trucks_player.append(new_vid)
        nuevos_plogs_player.append(new_plog)
        asignacion_garajes.setdefault(cid, {})[slot_idx] = new_vid

    if not nuevos_trucks_player:
        return False, "No se pudieron generar los camiones seleccionados."

    def _poner_camiones_garaje(m_hdr, pref, g_body, suf):
        c_id = m_hdr.group(1)
        if c_id not in asignacion_garajes:
            return None
        m_st = re.search(r"\bstatus:\s*(\d+)", g_body)
        st = int(m_st.group(1)) if m_st else 0
        cap = CAPACIDADES_GARAJE.get(st, 0)
        raw_v = (re.findall(r"vehicles\[\d+\]:\s*([^\s\r\n]+)", g_body) + ["null"] * cap)[:cap]
        for s_idx, n_vid in asignacion_garajes[c_id].items():
            if 0 <= s_idx < cap:
                raw_v[s_idx] = n_vid
        g_body = _reemplazar_array_sii(g_body, "vehicles", raw_v)
        return pref + g_body + suf

    contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _poner_camiones_garaje)

    m_pl = re.search(r"^(player\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
    if m_pl:
        pl_body = m_pl.group(2)
        pl_trucks = re.findall(r"trucks\[\d+\]:\s*([^\s\r\n]+)", pl_body)
        pl_plogs = re.findall(r"truck_profit_logs\[\d+\]:\s*([^\s\r\n]+)", pl_body)
        pl_trucks.extend(nuevos_trucks_player)
        pl_plogs.extend(nuevos_plogs_player)
        pl_body = _reemplazar_array_sii(pl_body, "trucks", pl_trucks)
        pl_body = _reemplazar_array_sii(pl_body, "truck_profit_logs", pl_plogs)
        contenido = contenido[:m_pl.start()] + m_pl.group(1) + pl_body + m_pl.group(3) + contenido[m_pl.end():]

    nuevo_saldo = max(0, saldo_actual - costo_total)
    contenido = re.sub(r"\bmoney_account:\s*-?\d+", f"money_account: {nuevo_saldo}", contenido, count=1)

    m_eco = re.search(r"^(economy\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
    if m_eco:
        eco_body = _desbloquear_pantallas_sii(
            m_eco.group(2),
            {"truck.dealer_map", "truck.eshop", "truck.eshop.used_trucks", "overview.compman_w", "screen.truckman", "screen.garageman"},
        )
        contenido = contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]

    pos_cierre = contenido.rfind("}")
    if pos_cierre != -1:
        texto_bloques = "\n\n" + "\n\n".join(bloques_nuevos) + "\n"
        contenido = contenido[:pos_cierre] + texto_bloques + contenido[pos_cierre:]

    _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
    actualizar_metadatos_guardado(ruta_guardado, dinero=nuevo_saldo)

    return (
        True,
        f"Se compraron {len(nuevos_trucks_player)} camiones por ${costo_total:,} y se ubicaron en los espacios libres de tus garajes.",
    )


def comprar_camiones_usados(
    ruta_guardado: str,
    compras: list[tuple[str, int]],
) -> tuple[bool, str]:
    """Compra copias de camiones usados disponibles y los ubica en espacios libres de garajes comprados."""
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        m_bank = re.search(r"^(bank\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
        m_money = re.search(r"\bmoney_account:\s*(-?\d+)", m_bank.group(2) if m_bank else contenido)
        saldo_actual = max(0, int(m_money.group(1))) if m_money else 0

        ctx = obtener_contexto_jugador(contenido)
        slots_disponibles, ofertas_info = _recolectar_slots_y_ofertas_compra(
            contenido,
            ctx["hq_city"],
            ctx["player_driver_id"],
            ctx["veh_activo"],
        )
        if not slots_disponibles:
            return False, "No tienes espacios libres para camiones en tus garajes comprados. Compra o mejora garajes en la pestaña Garajes para almacenar más camiones."

        return _ejecutar_compra_camiones_contenido(
            contenido,
            f_game,
            ruta_guardado,
            estaba_saneado,
            compras,
            saldo_actual,
            slots_disponibles,
            ofertas_info,
        )
    except Exception as e:
        return False, f"Error al comprar camiones usados: {e}"


def comprar_camiones_usados_variados(ruta_guardado: str) -> tuple[bool, str]:
    """Compra todos los camiones posibles variando entre los distintos modelos usados disponibles."""
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        m_bank = re.search(r"^(bank\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
        m_money = re.search(r"\bmoney_account:\s*(-?\d+)", m_bank.group(2) if m_bank else contenido)
        saldo = max(0, int(m_money.group(1))) if m_money else 0

        ctx = obtener_contexto_jugador(contenido)
        slots_disponibles, ofertas_info = _recolectar_slots_y_ofertas_compra(
            contenido,
            ctx["hq_city"],
            ctx["player_driver_id"],
            ctx["veh_activo"],
        )
        if not ofertas_info:
            return False, "No se detectaron ofertas de camiones usados en esta partida."
        free_slots = len(slots_disponibles)
        if free_slots <= 0:
            return False, "No tienes espacios libres para camiones en tus garajes comprados."

        lista_ofertas = list(ofertas_info.items())
        precio_min = min(inf["price"] for _oid, inf in lista_ofertas)
        if saldo < precio_min:
            return False, f"No tienes suficiente dinero disponible (${saldo:,}) para comprar camiones usados."

        conteo_por_oferta = {oid: 0 for oid, _inf in lista_ofertas}
        gasto_acumulado = 0
        total_elegidos = 0

        while total_elegidos < free_slots:
            progreso = False
            for oid, inf in lista_ofertas:
                if total_elegidos >= free_slots:
                    break
                if gasto_acumulado + inf["price"] <= saldo:
                    conteo_por_oferta[oid] += 1
                    gasto_acumulado += inf["price"]
                    total_elegidos += 1
                    progreso = True
            if not progreso:
                break

        compras = [(oid, cant) for oid, cant in conteo_por_oferta.items() if cant > 0]
        if not compras:
            return False, "No tienes suficiente saldo disponible para comprar camiones."

        return _ejecutar_compra_camiones_contenido(
            contenido,
            f_game,
            ruta_guardado,
            estaba_saneado,
            compras,
            saldo,
            slots_disponibles,
            ofertas_info,
        )
    except Exception as e:
        return False, f"Error al comprar camiones usados variados: {e}"


def vender_camiones_flota(
    ruta_guardado: str,
    brand_id: str | None = None,
    model_id: str | None = None,
    cantidad: int | None = None,
    precio_unitario: int = 35000,
) -> tuple[bool, str]:
    """Vende camiones de los garajes de la empresa manteniendo intacto el camión del jugador."""
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        ctx = obtener_contexto_jugador(contenido)
        hq_city = ctx["hq_city"]
        player_driver_id = ctx["player_driver_id"]
        vehs_personales_jugador = ctx["vehs_personales"]

        raw_candidatos = []
        ofertas_precio = []
        driver_a_camion = {}

        for m_hdr, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_GARAGE_O_OFFER_HDR):
            utype, uid = m_hdr.group(1), m_hdr.group(2)
            body = contenido[bs:be]
            if utype == "garage":
                cid = uid[7:] if uid.startswith("garage.") else uid
                m_st = re.search(r"\bstatus:\s*(\d+)", body)
                st = int(m_st.group(1)) if m_st else 0
                cap = CAPACIDADES_GARAJE.get(st, 0)
                if st not in (1, 2, 3, 6) or cap <= 0:
                    continue
                raw_v = (re.findall(r"vehicles\[\d+\]:\s*([^\s\r\n]+)", body) + ["null"] * cap)[:cap]
                raw_d = (re.findall(r"drivers\[\d+\]:\s*([^\s\r\n]+)", body) + ["null"] * cap)[:cap]
                for idx in range(cap):
                    vid = raw_v[idx]
                    drv_id = raw_d[idx]
                    if drv_id != "null" and vid != "null":
                        driver_a_camion[drv_id] = vid
                    if vid == "null" or vid in vehs_personales_jugador:
                        continue
                    if cid == hq_city and idx == 0 and (drv_id == player_driver_id or drv_id == "null"):
                        continue
                    raw_candidatos.append((cid, idx, vid, drv_id))
            else:
                mt = re.search(r"\btruck:\s*([^\s\r\n]+)", body)
                mp = re.search(r"\bprice:\s*(\d+)", body)
                if mt and mt.group(1) != "null":
                    ofertas_precio.append((mt.group(1), int(mp.group(1)) if mp else 45000))

        if not raw_candidatos:
            return False, "No hay camiones en la flota disponibles para vender (tu camión personal activo se mantiene protegido)."

        vids_necesarios = {vid for _, _, vid, _ in raw_candidatos} | {tid for tid, _p in ofertas_precio}
        if len(vids_necesarios) <= 25:
            bloques_v = extraer_bloques_por_ids_sii(contenido, vids_necesarios, tipos_objetivo={"vehicle"})
            mapa_veh = {uid: b for uid, (_t, b) in bloques_v.items()}
        else:
            mapa_veh = {
                m_h.group(1): contenido[bs:be]
                for m_h, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_VEHICLE_HDR)
                if m_h.group(1) in vids_necesarios
            }

        aids_usados = set()
        for vb_u in mapa_veh.values():
            aids_usados.update(re.findall(r"accessories\[\d+\]:\s*([^\s\r\n]+)", vb_u))

        mapa_acc = {}
        if aids_usados:
            if len(aids_usados) <= 25:
                bloques_acc = extraer_bloques_por_ids_sii(contenido, aids_usados)
                for aid, (_tacc, bacc) in bloques_acc.items():
                    m_dp = re.search(r'^\s*data_path:\s*"([^"]*)"', bacc)
                    if m_dp:
                        mapa_acc[aid] = m_dp.group(1)
            else:
                mapa_acc = dict(re_findall_por_trozos(_RE_VEH_ACC_DP, contenido))

        precios_modelo = {}
        for tid_u, p_u in ofertas_precio:
            vb_u = mapa_veh.get(tid_u)
            if vb_u:
                ic = _extraer_info_camion(contenido, vb_u, mapa_acc)
                precios_modelo[(ic["brand_id"], ic["model_id"])] = max(10000, int(p_u * 0.7))

        candidatos = []
        for cid, idx, vid, drv_id in raw_candidatos:
            vb_c = mapa_veh.get(vid)
            if not vb_c:
                continue
            ic = _extraer_info_camion(contenido, vb_c, mapa_acc)
            clave_mod = (ic["brand_id"], ic["model_id"])
            if brand_id is not None and model_id is not None and clave_mod != (brand_id, model_id):
                continue
            tiene_drv = drv_id != "null" and drv_id != player_driver_id
            val_v = precios_modelo.get(clave_mod, max(15000, int(precio_unitario * 0.7)))
            candidatos.append((cid, idx, vid, tiene_drv, drv_id, val_v))

        if not candidatos:
            return False, "No hay camiones en la flota disponibles para vender (tu camión personal activo se mantiene protegido)."

        candidatos.sort(key=lambda x: 1 if x[3] else 0)
        n_vender = len(candidatos) if cantidad is None else min(len(candidatos), max(0, int(cantidad)))
        if n_vender <= 0:
            return False, "Selecciona al menos 1 camión para vender."

        elegidos = candidatos[:n_vender]
        vids_vendidos = {e[2] for e in elegidos}
        slots_por_garaje = {}
        conductores_afectados = set()
        reembolso_total = 0
        for cid, idx, _vid, td, d_id, val_v in elegidos:
            slots_por_garaje.setdefault(cid, set()).add(idx)
            if td and d_id != "null":
                conductores_afectados.add(d_id)
            reembolso_total += val_v

        for d_k, v_k in driver_a_camion.items():
            if v_k in vids_vendidos:
                conductores_afectados.add(d_k)

        def _quitar_camion_garaje(m_hdr, pref, g_body, suf):
            c_id = m_hdr.group(1)
            if c_id not in slots_por_garaje:
                return None
            m_st = re.search(r"\bstatus:\s*(\d+)", g_body)
            st = int(m_st.group(1)) if m_st else 0
            cap = CAPACIDADES_GARAJE.get(st, 0)
            raw_v = (re.findall(r"vehicles\[\d+\]:\s*([^\s\r\n]+)", g_body) + ["null"] * cap)[:cap]
            for s_idx in slots_por_garaje[c_id]:
                if 0 <= s_idx < cap:
                    raw_v[s_idx] = "null"
            g_body = _reemplazar_array_sii(g_body, "vehicles", raw_v)
            return pref + g_body + suf

        contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _quitar_camion_garaje)

        conductores_reales_afectados = set()

        def _desasignar_drv_de_vendido(m_hdr, pref, d_body, suf):
            d_id = m_hdr.group(1)
            m_at = re.search(r"\bassigned_truck:\s*([^\s\r\n]+)", d_body)
            camion_asignado = m_at.group(1) if m_at else ""
            if d_id in conductores_afectados or camion_asignado in vids_vendidos:
                conductores_reales_afectados.add(d_id)
                d_body = re.sub(r"\bassigned_truck:\s*[^\s\r\n]+", "assigned_truck: null", d_body, count=1)
                d_body = re.sub(r"\bon_duty_timer:\s*[^\s\r\n]+", "on_duty_timer: 0", d_body, count=1)
                d_body = re.sub(r"\bstate:\s*\d+", "state: 1", d_body, count=1)
                return pref + d_body + suf
            return None

        contenido = transformar_bloques_sii(contenido, _RE_DRIVER_AI_HDR, _desasignar_drv_de_vendido)
        if conductores_reales_afectados:
            contenido, _ = asegurar_y_resetear_driver_jobs_idle(
                contenido,
                target_driver_ids=conductores_reales_afectados,
                resetear_existentes=True,
            )

        plogs_vendidos = set()
        m_pl = re.search(r"^(player\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
        if m_pl:
            pl_body = m_pl.group(2)
            pl_trucks = re.findall(r"trucks\[\d+\]:\s*([^\s\r\n]+)", pl_body)
            pl_plogs = re.findall(r"truck_profit_logs\[\d+\]:\s*([^\s\r\n]+)", pl_body)
            nuevos_t = []
            nuevos_p = []
            for i, tid in enumerate(pl_trucks):
                if tid not in vids_vendidos:
                    nuevos_t.append(tid)
                    if i < len(pl_plogs):
                        nuevos_p.append(pl_plogs[i])
                elif i < len(pl_plogs) and pl_plogs[i] != "null":
                    plogs_vendidos.add(pl_plogs[i])
            pl_body = _reemplazar_array_sii(pl_body, "trucks", nuevos_t)
            if pl_plogs:
                pl_body = _reemplazar_array_sii(pl_body, "truck_profit_logs", nuevos_p)
            contenido = contenido[:m_pl.start()] + m_pl.group(1) + pl_body + m_pl.group(3) + contenido[m_pl.end():]

        ids_borrar = set(vids_vendidos) | plogs_vendidos
        for vid in vids_vendidos:
            vb_del = mapa_veh.get(vid, "")
            if vb_del:
                ids_borrar.update(re.findall(r"accessories\[\d+\]:\s*(_nameless\.[0-9a-fA-F\.]+)", vb_del))
        if plogs_vendidos:
            if len(plogs_vendidos) <= 20:
                bloques_plog = extraer_bloques_por_ids_sii(
                    contenido,
                    plogs_vendidos,
                    tipos_objetivo={"profit_log"},
                )
                for _pid, (_pt, pbody) in bloques_plog.items():
                    ids_borrar.update(re.findall(r"stats_data\[\d+\]:\s*(_nameless\.[0-9a-fA-F\.]+)", pbody))
            else:
                for m_hdr, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_PROFIT_LOG_HDR):
                    if m_hdr.group(1) in plogs_vendidos:
                        ids_borrar.update(re.findall(r"stats_data\[\d+\]:\s*(_nameless\.[0-9a-fA-F\.]+)", contenido[bs:be]))

        if ids_borrar:
            contenido = eliminar_bloques_por_id_sii(contenido, ids_borrar)
            if "\n\n\n" in contenido:
                contenido = re.sub(r"\n{3,}", "\n\n", contenido)

        m_bank = re.search(r"^(bank\s*:\s*[^\{]+\{)(.*?)^(})", contenido, re.M | re.S)
        m_money = re.search(r"\bmoney_account:\s*(-?\d+)", m_bank.group(2) if m_bank else contenido)
        saldo_actual = max(0, int(m_money.group(1))) if m_money else 0
        nuevo_saldo = saldo_actual + reembolso_total
        contenido = re.sub(r"\bmoney_account:\s*-?\d+", f"money_account: {nuevo_saldo}", contenido, count=1)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado, dinero=nuevo_saldo)
        return True, f"Se vendieron {len(vids_vendidos)} camiones por ${reembolso_total:,} y se liberaron sus espacios en los garajes."
    except Exception as e:
        return False, f"Error al vender camiones: {e}"

import copy
import os
import re
from download_manager import obtener_ruta_ats
from gestor_perfiles.saneador import _guardar_contenido_partida_sano, sanear_y_reparar_partida_sii
from gestor_perfiles.sii_io import (
    CAPACIDADES_GARAJE,
    _encontrar_vehiculo_activo_id,
    _parse_sii_float,
    desencriptar_archivo_sii,
    es_archivo_saneado_en_cache,
    extraer_bloques_por_ids_sii,
    guardar_cache_datos_partida,
    iterar_bloques_sii,
    marcar_archivo_saneado_cache,
    obtener_cache_datos_partida,
    obtener_lock_archivo,
    obtener_ruta_sii_decrypt,
    re_findall_por_trozos,
)

_RE_INFO_NAME = re.compile(r'\bname:\s*\"?([^\r\n\"]*)\"?')
_RE_INFO_TIME = re.compile(r"\bfile_time:\s*(\d+)")
_RE_BLOQUE_ECONOMY = re.compile(r"^economy\s*:\s*[^\{]+\{(.*?)^\}", re.M | re.S)
_RE_BLOQUE_BANK = re.compile(r"^bank\s*:\s*[^\{]+\{(.*?)^\}", re.M | re.S)
_RE_BLOQUE_BANK_LOAN = re.compile(r"^bank_loan\s*:\s*[^\s\{]+\s*\{(.*?)^\}", re.M | re.S)
_RE_BLOQUE_PLAYER = re.compile(r"^player\s*:\s*[^\{]+\{(.*?)^\}", re.M | re.S)
_RE_BLOQUE_DRIVER_AI = re.compile(r"^driver_ai\s*:\s*([^\s\{]+)\s*\{(.*?)^\}", re.M | re.S)
_RE_VEH_ACC = re.compile(r'^vehicle_\w*accessory\s*:\s*([^\s\{]+)\s*\{\s*data_path:\s*"([^"]*)"', re.M)
_RE_BLOQUE_VEHICLE = re.compile(r"^vehicle\s*:\s*([^\s\{]+)\s*\{(.*?)^\}", re.M | re.S)
_RE_BLOQUE_GARAGE = re.compile(r"^garage\s*:\s*garage\.([^\s\{]+)\s*\{(.*?)^\}", re.M | re.S)
_RE_LECTURA_BLOQUES_HDR = re.compile(r"^(bank_loan|garage|driver_ai|used_truck_offer)\s*:\s*([^\s\{]+)\s*\{", re.M)
_RE_VEHICLE_HDR = re.compile(r"^vehicle\s*:\s*([^\s\{]+)\s*\{", re.M)

_MARCAS_OFICIALES_ATS = {
    "kenworth": "Kenworth",
    "peterbilt": "Peterbilt",
    "volvo": "Volvo",
    "freightliner": "Freightliner",
    "intl": "International",
    "intnational": "International",
    "international": "International",
    "mack": "Mack",
    "westernstar": "Western Star",
    "western": "Western Star",
}


def formatear_nombre_ciudad(ciudad_id: str) -> str:
    if not ciudad_id:
        return ""
    return ciudad_id.replace("_", " ").title()


def _extraer_todas_las_ciudades(bloque_eco: str) -> list[str]:
    ciudades = set()
    for c in re.findall(r"companies\[\d+\]:\s*company\.volatile\.[^.\s]+\.([^\s\r\n]+)", bloque_eco):
        ciudades.add(c)
    for c in re.findall(r"garages\[\d+\]:\s*garage\.([^\s\r\n]+)", bloque_eco):
        ciudades.add(c)
    for c in re.findall(r"visited_cities\[\d+\]:\s*([^\s\r\n]+)", bloque_eco):
        ciudades.add(c)
    for c in re.findall(r"unlocked_dealers\[\d+\]:\s*([^\s\r\n]+)", bloque_eco):
        ciudades.add(c)
    for c in re.findall(r"unlocked_recruitments\[\d+\]:\s*([^\s\r\n]+)", bloque_eco):
        ciudades.add(c)
    return sorted(ciudades)


def _bonito_token(token: str) -> str:
    if re.fullmatch(r"\d+x\d+", token):
        return token
    if re.fullmatch(r"\d+[a-z]?", token):
        return token
    if re.fullmatch(r"[a-z]{1,2}\d+[a-z]?", token):
        return token.upper()
    m = re.fullmatch(r"([a-z]{1,3})(\d{4})", token)
    if m:
        return f"{m.group(1).upper()} {m.group(2)}"
    m = re.fullmatch(r"([a-z]{4,})(\d{4})", token)
    if m:
        return f"{m.group(1).title()} {m.group(2)}"
    if re.fullmatch(r"[a-z]{1,3}", token):
        return token.upper()
    return token.title()


def _bonito_id(valor: str) -> str:
    """Convierte ids tipo 'cascadia2018' o 'mp8_445' en texto legible."""
    if not valor:
        return ""
    return " ".join(_bonito_token(t) for t in re.split(r"[_\s]+", valor.lower()) if t)


def _extraer_info_camion(contenido: str, vb: str, mapa_acc: dict | None = None) -> dict:
    """Detecta marca/modelo y componentes del camión leyendo los data_path de sus accesorios."""
    info = {
        "brand_id": "",
        "model_id": "",
        "brand_name": "",
        "model_name": "",
        "is_mod": False,
        "engine": "",
        "transmission": "",
        "chassis": "",
        "cabin": "",
    }
    ids_lista = re.findall(r"accessories\[\d+\]:\s*([^\s\r\n]+)", vb)
    if not ids_lista:
        return info

    if mapa_acc is not None:
        rutas = [mapa_acc[i] for i in ids_lista if i in mapa_acc]
    else:
        ids = set(ids_lista)
        rutas = []
        for m in re.finditer(r'^vehicle_\w*accessory\s*:\s*([^\s\{]+)\s*\{\s*data_path:\s*"([^"]*)"', contenido, re.M):
            if m.group(1) in ids:
                rutas.append(m.group(2))

    for ruta in rutas:
        m = re.match(r"/def/vehicle/truck/([^/]+)/(.+)\.sii$", ruta)
        if not m:
            continue
        carpeta, resto = m.group(1), m.group(2)
        if resto == "data" and not info["brand_id"]:
            marca, _, modelo = carpeta.partition(".")
            info["brand_id"], info["model_id"] = marca, modelo
        elif resto.startswith("engine/") and not info["engine"]:
            info["engine"] = resto.split("/", 1)[1].replace("_", " ").upper()
        elif resto.startswith("transmission/") and not info["transmission"]:
            info["transmission"] = _bonito_id(resto.split("/", 1)[1])
        elif resto.startswith("chassis/") and not info["chassis"]:
            info["chassis"] = _bonito_id(resto.split("/", 1)[1])
        elif resto.startswith("cabin/") and not info["cabin"]:
            info["cabin"] = resto.split("/", 1)[1].replace("_", " ").title()
        if not info["brand_id"] and "/" in resto:
            marca, _, modelo = carpeta.partition(".")
            info["brand_id"], info["model_id"] = marca, modelo

    marca = info["brand_id"]
    if marca:
        info["is_mod"] = marca not in _MARCAS_OFICIALES_ATS
        info["brand_name"] = _MARCAS_OFICIALES_ATS.get(marca, _bonito_id(marca))
        info["model_name"] = _bonito_id(info["model_id"])
    return info


def listar_perfiles_ats() -> list[dict]:
    """Lista los perfiles locales (editables) y de Steam Cloud (solo lectura) en Documentos/ATS."""
    ruta_base = obtener_ruta_ats("")
    perfiles = []

    for subcarpeta, origen, es_cloud in (
        ("profiles", "Local", False),
        ("steam_profiles", "Steam Cloud", True),
    ):
        dir_p = os.path.join(ruta_base, subcarpeta)
        if not os.path.exists(dir_p):
            continue
        for c in os.listdir(dir_p):
            if (es_cloud and c.endswith(".bak")) or c.endswith("_PRUEBA_DESBLOQUEO"):
                continue
            ruta_c = os.path.join(dir_p, c)
            if not os.path.isdir(ruta_c):
                continue
            try:
                nombre = bytes.fromhex(c).decode("utf-8", errors="ignore")
            except Exception:
                nombre = c
            perfiles.append({
                "id_hex": c,
                "nombre": nombre.strip() if nombre.strip() else c,
                "origen": origen,
                "ruta": ruta_c,
                "es_steam_cloud": es_cloud,
            })

    return perfiles


def listar_guardados_de_perfil(ruta_perfil: str) -> list[dict]:
    """Enumera y ordena cronológicamente los guardados disponibles dentro de un perfil."""
    dir_save = os.path.join(ruta_perfil, "save")
    if not os.path.exists(dir_save):
        return []

    sii_decrypt = obtener_ruta_sii_decrypt()
    guardados = []

    with os.scandir(dir_save) as it:
        for entry in it:
            if not entry.is_dir():
                continue

            elem = entry.name
            ruta_i = entry.path
            info_p = os.path.join(ruta_i, "info.sii")
            nombre_legible = elem
            file_time = 0

            try:
                with open(info_p, "r", encoding="utf-8", errors="ignore") as f:
                    c = f.read(4096)
                if "SiiNunit" not in c and sii_decrypt:
                    desencriptar_archivo_sii(info_p)
                    with open(info_p, "r", encoding="utf-8", errors="ignore") as f:
                        c = f.read(4096)

                m_n = _RE_INFO_NAME.search(c)
                if m_n:
                    raw_n = m_n.group(1).strip()
                    if raw_n.startswith("@@noname_save_game@@"):
                        num = raw_n.replace("@@noname_save_game@@", "").strip()
                        nombre_legible = f"Partida {num}" if num else (f"Partida {elem}" if elem.isdigit() else elem)
                    elif raw_n:
                        nombre_legible = raw_n

                m_t = _RE_INFO_TIME.search(c)
                file_time = int(m_t.group(1)) if m_t else int(entry.stat().st_mtime)
            except Exception:
                try:
                    file_time = int(entry.stat().st_mtime)
                except Exception:
                    file_time = 0

            if elem == "autosave":
                nombre_legible = "Autoguardado"
            elif elem == "quicksave":
                nombre_legible = "Guardado Rápido"
            elif elem.startswith("autosave_drive"):
                sufijo = elem.replace("autosave_drive", "").replace("_", " ").strip()
                nombre_legible = f"Autoguardado en ruta {sufijo}".strip()
            elif elem.startswith("autosave_job"):
                sufijo = elem.replace("autosave_job", "").replace("_", " ").strip()
                nombre_legible = f"Autoguardado de trabajo {sufijo}".strip()
            elif elem.startswith("multiplayer_backup"):
                sufijo = elem.replace("multiplayer_backup", "").replace("_", " ").strip()
                nombre_legible = f"Autoguardado Convoy {sufijo}".strip()
            elif elem.isdigit() and nombre_legible == elem:
                nombre_legible = f"Partida {elem}"

            guardados.append({
                "id": elem,
                "nombre": nombre_legible,
                "nombre_base": nombre_legible,
                "ruta": ruta_i,
                "time": file_time,
            })

    guardados.sort(key=lambda x: -x["time"])
    if guardados:
        guardados[0]["es_mas_reciente"] = True
        guardados[0]["nombre"] = f"[Más reciente] {guardados[0]['nombre_base']}"
    return guardados


def leer_datos_partida(ruta_guardado: str, sanear: bool = True) -> dict:
    """Desencripta y extrae el estado completo de economía, garajes, conductores y flota de game.sii."""
    datos = {
        "money": 0,
        "xp": 0,
        "skills": {
            "adr": 0,
            "long_dist": 0,
            "heavy": 0,
            "fragile": 0,
            "urgent": 0,
            "mechanical": 0,
        },
        "loans_count": 0,
        "loans_amount": 0,
        "overdraft": False,
        "garages": [],
        "hq_city": "",
        "all_cities": [],
        "visited_cities_count": 0,
        "total_cities_count": 0,
        "unlocked_dealers_count": 0,
        "unlocked_recruitments_count": 0,
        "cutscenes_count": 0,
        "cutscenes_completed_count": 0,
        "tourist_atlas_count": 0,
        "hired_drivers_count": 0,
        "pool_drivers_count": 0,
        "free_driver_slots": 0,
        "idle_hired_drivers_count": 0,
        "empty_trucks_count": 0,
        "drivers_with_truck_count": 0,
        "free_truck_slots": 0,
        "avg_driver_rating": 5.0,
        "company_trucks_count": 0,
        "used_trucks": [],
        "truck": {
            "found": False,
            "id": "",
            "fuel_pct": 100,
            "max_wear_pct": 0.0,
            "max_unfixable_pct": 0.0,
            "odometer": 0,
            "plate_raw": "",
            "plate_text": "",
            "plate_state": "",
            "brand_id": "",
            "model_id": "",
            "brand_name": "",
            "model_name": "",
            "is_mod": False,
            "engine": "",
            "transmission": "",
            "chassis": "",
            "cabin": "",
            "trip_km": 0,
            "trip_fuel_l": 0,
            "trip_min": 0,
        },
    }

    f_game = os.path.join(ruta_guardado, "game.sii")
    if not os.path.exists(f_game):
        return datos

    cached = obtener_cache_datos_partida(f_game, sanear)
    if cached is not None:
        return copy.deepcopy(cached)

    parse_ok = False
    saneado_verificado = False
    try:
        lock = obtener_lock_archivo(f_game)
        with lock:
            desencriptar_archivo_sii(f_game)
            with open(f_game, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
            saneado_verificado = sanear and es_archivo_saneado_en_cache(f_game)

        if sanear and not saneado_verificado:
            contenido_saneado, reparaciones_auto = sanear_y_reparar_partida_sii(contenido)
            if reparaciones_auto:
                try:
                    _guardar_contenido_partida_sano(f_game, contenido_saneado, ruta_guardado, sanear=False)
                    contenido = contenido_saneado
                    saneado_verificado = True
                    print(
                        f"[AUTO-REPARAR] Se corrigieron automáticamente {len(reparaciones_auto)} anomalías en "
                        f"{os.path.basename(ruta_guardado)}: {reparaciones_auto}"
                    )
                except Exception as e:
                    print(f"[AUTO-REPARAR] Error al guardar reparación: {e}")
            else:
                marcar_archivo_saneado_cache(f_game)
                saneado_verificado = True

        m_eco = _RE_BLOQUE_ECONOMY.search(contenido)
        eco = m_eco.group(1) if m_eco else ""

        m_xp = re.search(r"\bexperience_points:\s*(\d+)", eco or contenido)
        if m_xp:
            datos["xp"] = int(m_xp.group(1))

        if eco:
            m_adr = re.search(r"\badr:\s*(\d+)", eco)
            if m_adr:
                datos["skills"]["adr"] = min(63, max(0, int(m_adr.group(1))))
            for sk in ("long_dist", "heavy", "fragile", "urgent", "mechanical"):
                m_sk = re.search(f"\\b{sk}:\\s*(\\d+)", eco)
                if m_sk:
                    datos["skills"][sk] = min(6, max(0, int(m_sk.group(1))))

            todas_ciudades = _extraer_todas_las_ciudades(eco)
            datos["all_cities"] = todas_ciudades
            datos["total_cities_count"] = len(todas_ciudades)

            for clave_cnt, campo_eco in (
                ("visited_cities_count", "visited_cities"),
                ("unlocked_dealers_count", "unlocked_dealers"),
                ("unlocked_recruitments_count", "unlocked_recruitments"),
                ("cutscenes_count", "discovered_cutscene_items"),
                ("tourist_atlas_count", "tourist_atlas_log_units"),
            ):
                m_val = re.search(f"\\b{campo_eco}:\\s*(\\d+)", eco)
                datos[clave_cnt] = int(m_val.group(1)) if m_val else 0

            states_cs = re.findall(r"discovered_cutscene_items_states\[\d+\]:\s*(\d+)", eco)
            datos["cutscenes_completed_count"] = sum(1 for s in states_cs if s == "2")

        m_bank = _RE_BLOQUE_BANK.search(contenido)
        bank = m_bank.group(1) if m_bank else ""
        m_money = re.search(r"\bmoney_account:\s*(-?\d+)", bank or contenido)
        if m_money:
            datos["money"] = max(0, int(m_money.group(1)))

        if bank:
            m_loans = re.search(r"\bloans:\s*(\d+)", bank)
            datos["loans_count"] = int(m_loans.group(1)) if m_loans else 0
            m_ov = re.search(r"\boverdraft:\s*(true|false)", bank)
            datos["overdraft"] = m_ov.group(1) == "true" if m_ov else False

        necesita_loans = datos["loans_count"] > 0
        total_deuda = 0

        m_pl = _RE_BLOQUE_PLAYER.search(contenido)
        pl = m_pl.group(1) if m_pl else ""
        player_driver_id = ""
        hq_city = ""
        veh_id = _encontrar_vehiculo_activo_id(contenido, pl)
        hired_ids = set()

        if pl:
            m_hq = re.search(r"\bhq_city:\s*([^\s\r\n]+)", pl)
            if m_hq and m_hq.group(1) != "null":
                datos["hq_city"] = m_hq.group(1)
                hq_city = m_hq.group(1)

            m_pdrv0 = re.search(r"drivers\[0\]:\s*([^\s\r\n]+)", pl)
            if m_pdrv0:
                player_driver_id = m_pdrv0.group(1)

            m_drv = re.search(r"\bdrivers:\s*(\d+)", pl)
            if m_drv:
                datos["hired_drivers_count"] = max(0, int(m_drv.group(1)) - 1)

            pl_drvs_all = re.findall(r"drivers\[\d+\]:\s*([^\s\r\n]+)", pl)
            hired_ids = {d for d in pl_drvs_all[1:] if d != "null" and d != player_driver_id}

        raw_pool = re.findall(r"driver_pool\[\d+\]:\s*([^\s\r\n]+)", eco) if eco else []
        raw_offers = re.findall(r"drivers_offer\[\d+\]:\s*([^\s\r\n]+)", eco) if eco else []
        pl_drvs_set = set(hired_ids)
        if player_driver_id:
            pl_drvs_set.add(player_driver_id)
        pool_set = {d for d in raw_pool + raw_offers if d != "null"} - pl_drvs_set
        datos["pool_drivers_count"] = len(pool_set)

        garajes_lista = []
        free_slots = 0
        free_truck_slots = 0
        total_camiones_empresa = 0
        conteo_modelos_propios = {}
        driver_a_camion = {}
        camiones_asignados_a_ia = set()
        legacy_driver_a_camion = {}
        legacy_camiones_asignados = set()
        vehiculos_slot_sin_driver = []
        vids_para_conteo_modelos = []
        ofertas_crudo = []

        suma_calif = 0.0
        contados = 0

        for m_hdr, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_LECTURA_BLOQUES_HDR):
            utype, uid = m_hdr.group(1), m_hdr.group(2)
            body = contenido[bs:be]

            if utype == "bank_loan":
                if necesita_loans:
                    m_amt = re.search(r"\bamount:\s*(\d+)", body)
                    if m_amt:
                        total_deuda += int(m_amt.group(1))
            elif utype == "garage":
                g_id = uid[7:] if uid.startswith("garage.") else uid
                m_st = re.search(r"\bstatus:\s*(\d+)", body)
                st = int(m_st.group(1)) if m_st else 0
                raw_vehs = re.findall(r"vehicles\[\d+\]:\s*([^\s\r\n]+)", body)
                raw_drvs = re.findall(r"drivers\[\d+\]:\s*([^\s\r\n]+)", body)
                vehs = [v for v in raw_vehs if v != "null"]
                drvs = [d for d in raw_drvs if d != "null"]
                cap = CAPACIDADES_GARAJE.get(st, 0)

                for v_p, d_p in zip(raw_vehs, raw_drvs):
                    if v_p != "null" and d_p != "null":
                        driver_a_camion[d_p] = v_p
                        camiones_asignados_a_ia.add(v_p)

                if st in (1, 2, 3, 6) and cap > 0:
                    v_pad = (raw_vehs + ["null"] * cap)[:cap]
                    d_pad = (raw_drvs + ["null"] * cap)[:cap]
                    for s_idx, (v_s, d_s) in enumerate(zip(v_pad, d_pad)):
                        if v_s != "null" and v_s != veh_id:
                            total_camiones_empresa += 1
                            vids_para_conteo_modelos.append(v_s)

                        es_slot_jugador = g_id == hq_city and s_idx == 0 and (player_driver_id or veh_id)
                        if not es_slot_jugador:
                            if d_s == "null":
                                free_slots += 1
                            if v_s == "null":
                                free_truck_slots += 1
                            elif v_s != veh_id and d_s == "null":
                                vehiculos_slot_sin_driver.append(v_s)

                garajes_lista.append({
                    "id": g_id,
                    "nombre": formatear_nombre_ciudad(g_id),
                    "status": st,
                    "vehicles_ocupados": len(vehs),
                    "drivers_ocupados": len(drvs),
                    "capacidad": cap,
                })
            elif utype == "driver_ai":
                if "assigned_truck:" in body and "assigned_truck: null" not in body:
                    m_at = re.search(r"\bassigned_truck:\s*([^\s\r\n]+)", body)
                    if m_at and m_at.group(1) != "null":
                        tid = m_at.group(1)
                        legacy_driver_a_camion[uid] = tid
                        legacy_camiones_asignados.add(tid)

                if uid in hired_ids:
                    m_adr_d = re.search(r"\badr:\s*(\d+)", body)
                    adr_b = int(m_adr_d.group(1)) if m_adr_d else 0
                    pts = bin(adr_b & 63).count("1")
                    for sk_d in ("long_dist", "heavy", "fragile", "urgent", "mechanical"):
                        ms_d = re.search(f"\\b{sk_d}:\\s*(\\d+)", body)
                        if ms_d:
                            pts += min(6, max(0, int(ms_d.group(1))))
                    cal_d = max(1.0, min(10.0, 0.8 + pts / 36.0 * 9.2))
                    suma_calif += cal_d
                    contados += 1
            else:
                mt = re.search(r"\btruck:\s*([^\s\r\n]+)", body)
                mp = re.search(r"\bprice:\s*(\d+)", body)
                if mt and mt.group(1) != "null":
                    ofertas_crudo.append((uid, mt.group(1), int(mp.group(1)) if mp else 0))

        if necesita_loans:
            datos["loans_amount"] = total_deuda

        if hired_ids or vehiculos_slot_sin_driver:
            for did, tid in legacy_driver_a_camion.items():
                if did not in driver_a_camion:
                    driver_a_camion[did] = tid
            camiones_asignados_a_ia.update(legacy_camiones_asignados)
            if contados > 0:
                datos["avg_driver_rating"] = round(suma_calif / contados, 1)

        vids_necesarios = set(vids_para_conteo_modelos) | {vid for _oid, vid, _p in ofertas_crudo}
        if veh_id:
            vids_necesarios.add(veh_id)

        mapa_veh = {}
        if vids_necesarios:
            if len(vids_necesarios) <= 25:
                bloques_v = extraer_bloques_por_ids_sii(contenido, vids_necesarios, tipos_objetivo={"vehicle"})
                mapa_veh = {uid: b for uid, (_t, b) in bloques_v.items()}
            else:
                mapa_veh = {
                    m_v.group(1): contenido[bs:be]
                    for m_v, _s, bs, be, _ce in iterar_bloques_sii(contenido, _RE_VEHICLE_HDR)
                    if m_v.group(1) in vids_necesarios
                }

        aids_necesarios = set()
        for vb_r in mapa_veh.values():
            aids_necesarios.update(re.findall(r"accessories\[\d+\]:\s*([^\s\r\n]+)", vb_r))

        mapa_acc = {}
        if aids_necesarios:
            if len(aids_necesarios) <= 30:
                bloques_a = extraer_bloques_por_ids_sii(contenido, aids_necesarios)
                for aid, (_ta, ba) in bloques_a.items():
                    m_dp = re.search(r'^\s*data_path:\s*"([^"]*)"', ba)
                    if m_dp:
                        mapa_acc[aid] = m_dp.group(1)
            else:
                mapa_acc = dict(re_findall_por_trozos(_RE_VEH_ACC, contenido))

        for v_s in vids_para_conteo_modelos:
            vb_o = mapa_veh.get(v_s)
            if vb_o:
                inf_o = _extraer_info_camion(contenido, vb_o, mapa_acc)
                clave_m = (inf_o["brand_id"], inf_o["model_id"])
                conteo_modelos_propios[clave_m] = conteo_modelos_propios.get(clave_m, 0) + 1

        drivers_con_camion = sum(1 for d in hired_ids if d in driver_a_camion)
        empty_trucks = sum(1 for v_s in vehiculos_slot_sin_driver if v_s not in camiones_asignados_a_ia)

        garajes_lista.sort(key=lambda x: (0 if x["status"] in (1, 2, 3, 6) else 1, x["nombre"]))
        datos["garages"] = garajes_lista
        datos["free_driver_slots"] = free_slots
        datos["free_truck_slots"] = free_truck_slots
        datos["idle_hired_drivers_count"] = max(0, len(hired_ids) - drivers_con_camion)
        datos["empty_trucks_count"] = empty_trucks
        datos["drivers_with_truck_count"] = drivers_con_camion
        datos["company_trucks_count"] = total_camiones_empresa

        # Camión activo del jugador
        if veh_id and veh_id in mapa_veh:
            vb = mapa_veh[veh_id]
            datos["truck"]["found"] = True
            datos["truck"]["id"] = veh_id

            m_fuel = re.search(r"\bfuel_relative:\s*([^\s\r\n]+)", vb)
            if m_fuel:
                f_val = _parse_sii_float(m_fuel.group(1))
                datos["truck"]["fuel_pct"] = max(0, min(100, int(round(f_val * 100))))

            wears = []
            for wk in ("engine_wear", "transmission_wear", "cabin_wear", "chassis_wear"):
                mw = re.search(f"\\b{wk}:\\s*([^\\s\\r\\n]+)", vb)
                if mw:
                    wears.append(_parse_sii_float(mw.group(1)))
            for mw in re.findall(r"wheels_wear\[\d+\]:\s*([^\s\r\n]+)", vb):
                wears.append(_parse_sii_float(mw))
            if wears:
                datos["truck"]["max_wear_pct"] = round(max(wears) * 100, 1)

            unfixables = []
            for uk in (
                "engine_wear_unfixable",
                "transmission_wear_unfixable",
                "cabin_wear_unfixable",
                "chassis_wear_unfixable",
            ):
                mu = re.search(f"\\b{uk}:\\s*([^\\s\\r\\n]+)", vb)
                if mu:
                    unfixables.append(_parse_sii_float(mu.group(1)))
            for mu in re.findall(r"wheels_wear_unfixable\[\d+\]:\s*([^\s\r\n]+)", vb):
                unfixables.append(_parse_sii_float(mu))
            if unfixables:
                datos["truck"]["max_unfixable_pct"] = round(max(unfixables) * 100, 1)

            m_odo = re.search(r"\bodometer:\s*(\d+)", vb)
            if m_odo:
                datos["truck"]["odometer"] = int(m_odo.group(1))

            m_plate = re.search(r'\blicense_plate:\s*"([^"]*)"', vb)
            if m_plate:
                raw_plate = m_plate.group(1)
                datos["truck"]["plate_raw"] = raw_plate
                partes = raw_plate.split("|", 1)
                left_part = partes[0]
                state_part = partes[1] if len(partes) > 1 else ""
                m_font = re.search(r"<font[^>]*>([^<]+)</font>", left_part)
                if m_font:
                    datos["truck"]["plate_text"] = m_font.group(1).strip()
                else:
                    datos["truck"]["plate_text"] = re.sub(r"<[^>]+>", "", left_part).strip()
                datos["truck"]["plate_state"] = state_part.strip()

            datos["truck"].update(_extraer_info_camion(contenido, vb, mapa_acc))

            for clave_dato, clave_sii in (
                ("trip_km", "trip_distance_km"),
                ("trip_fuel_l", "trip_fuel_l"),
                ("trip_min", "trip_time_min"),
            ):
                m_trip = re.search(f"\\b{clave_sii}:\\s*(-?\\d+)", vb)
                if m_trip:
                    datos["truck"][clave_dato] = int(m_trip.group(1))

        usados = []
        for oid, vid, precio in ofertas_crudo:
            vbody = mapa_veh.get(vid)
            if not vbody:
                continue
            info_c = _extraer_info_camion(contenido, vbody, mapa_acc)
            m_odo_u = re.search(r"\bodometer:\s*(\d+)", vbody)
            odo_u = int(m_odo_u.group(1)) if m_odo_u else 0
            nombre_completo = f"{info_c['brand_name']} {info_c['model_name']}".strip() or "Camión Usado"
            clave_u = (info_c["brand_id"], info_c["model_id"])
            en_flota = conteo_modelos_propios.get(clave_u, 0)
            usados.append({
                "offer_id": oid,
                "truck_id": vid,
                "price": precio,
                "name": nombre_completo,
                "brand_id": info_c["brand_id"],
                "model_id": info_c["model_id"],
                "brand_name": info_c["brand_name"],
                "model_name": info_c["model_name"],
                "engine": info_c["engine"] or "Estándar",
                "transmission": info_c["transmission"] or "Estándar",
                "chassis": info_c["chassis"] or "Estándar",
                "cabin": info_c["cabin"] or "Estándar",
                "odometer": odo_u,
                "owned_count": en_flota,
            })
        datos["used_trucks"] = usados
        parse_ok = True
    except Exception as e:
        print(f"[PERFILES] Error leyendo datos de partida: {e}")

    if parse_ok:
        guardar_cache_datos_partida(f_game, saneado_verificado, copy.deepcopy(datos))

    return datos

import re
from gestor_perfiles.lectura import formatear_nombre_ciudad
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    CAPACIDADES_GARAJE,
    _desbloquear_pantallas_sii,
    _reemplazar_array_sii,
    abrir_partida_para_edicion,
    actualizar_metadatos_guardado,
    obtener_contexto_jugador,
    transformar_bloques_sii,
)


_RE_GARAGE_HDR = re.compile(r'^garage\s*:\s*garage\.([^\s\{]+)\s*\{', re.M)


def _transformar_cuerpo_garaje(g_body: str, nuevo_status: int) -> tuple[bool, str]:
    """Redimensiona el tamaño y las listas vehicles/drivers de un garaje protegiendo plazas ocupadas."""
    slots = CAPACIDADES_GARAJE.get(nuevo_status, 0)

    vehs = re.findall(r'vehicles\[\d+\]:\s*([^\s\r\n]+)', g_body)
    drvs = re.findall(r'drivers\[\d+\]:\s*([^\s\r\n]+)', g_body)
    max_len = max(len(vehs), len(drvs))
    vehs.extend(['null'] * (max_len - len(vehs)))
    drvs.extend(['null'] * (max_len - len(drvs)))

    ocupados = [(v, d) for v, d in zip(vehs, drvs) if v != 'null' or d != 'null']
    if len(ocupados) > slots:
        return False, g_body

    if slots >= max_len:
        nuevos_vehs = vehs + ['null'] * (slots - len(vehs))
        nuevos_drvs = drvs + ['null'] * (slots - len(drvs))
    elif all(vehs[i] == 'null' and drvs[i] == 'null' for i in range(slots, max_len)):
        nuevos_vehs = vehs[:slots]
        nuevos_drvs = drvs[:slots]
    else:
        nuevos_vehs = [v for v, _ in ocupados] + ['null'] * (slots - len(ocupados))
        nuevos_drvs = [d for _, d in ocupados] + ['null'] * (slots - len(ocupados))

    g_body_nuevo = _reemplazar_array_sii(g_body, 'vehicles', nuevos_vehs)
    g_body_nuevo = _reemplazar_array_sii(g_body_nuevo, 'drivers', nuevos_drvs)
    g_body_nuevo = re.sub(r'\bstatus:\s*\d+', f'status: {nuevo_status}', g_body_nuevo, count=1)
    return True, g_body_nuevo


def _desbloquear_pantallas_garajes(contenido: str) -> str:
    m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
    if not m_eco:
        return contenido
    eco_body = _desbloquear_pantallas_sii(
        m_eco.group(2),
        {'screen.garageman', 'screen.real_estate', 'overview.compman_w'},
    )
    return contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]


def modificar_garaje_individual(ruta_guardado: str, ciudad_id: str, nuevo_status: int) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        patron = rf'^(garage\s*:\s*garage\.{re.escape(ciudad_id)}\s*\{{)(.*?)^(}})'
        m_g = re.search(patron, contenido, re.M | re.S)
        if not m_g:
            return False, f"No se encontró el garaje de '{formatear_nombre_ciudad(ciudad_id)}'."

        hq_city = obtener_contexto_jugador(contenido)['hq_city']
        if nuevo_status == 0 and ciudad_id == hq_city:
            return False, (
                f'No se puede vender ni desactivar el garaje de {formatear_nombre_ciudad(ciudad_id)} '
                f'porque es la sede principal (HQ) de tu empresa en este perfil.'
            )

        ok_t, nuevo_cuerpo = _transformar_cuerpo_garaje(m_g.group(2), nuevo_status)
        if not ok_t:
            if nuevo_status == 0:
                return False, (
                    f'No se puede vender el garaje de {formatear_nombre_ciudad(ciudad_id)} '
                    f'porque todavía tiene camiones o conductores asignados.'
                )
            return False, (
                f'No se puede reducir el garaje de {formatear_nombre_ciudad(ciudad_id)} '
                f'porque tiene más camiones o conductores asignados que la nueva capacidad.'
            )

        contenido = contenido[:m_g.start()] + m_g.group(1) + nuevo_cuerpo + m_g.group(3) + contenido[m_g.end():]
        if nuevo_status > 0:
            contenido = _desbloquear_pantallas_garajes(contenido)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado)
        actualizar_metadatos_guardado(ruta_guardado)
        if nuevo_status == 0:
            return True, f'Garaje de {formatear_nombre_ciudad(ciudad_id)} vendido correctamente.'
        return True, f'Garaje de {formatear_nombre_ciudad(ciudad_id)} actualizado correctamente.'
    except Exception as e:
        return False, f'Error al modificar garaje: {e}'


def modificar_todos_los_garajes(ruta_guardado: str, nuevo_status: int) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        hq_city = obtener_contexto_jugador(contenido)['hq_city']
        modificados = 0
        omitidos = 0

        def _reemplazar_garaje(m_hdr, pref, g_body, suf):
            nonlocal modificados, omitidos
            cid = m_hdr.group(1)
            if nuevo_status == 0 and cid == hq_city:
                omitidos += 1
                return None
            ok_t, nuevo_cuerpo = _transformar_cuerpo_garaje(g_body, nuevo_status)
            if ok_t:
                modificados += 1
                return pref + nuevo_cuerpo + suf
            omitidos += 1
            return None

        contenido = transformar_bloques_sii(contenido, _RE_GARAGE_HDR, _reemplazar_garaje)

        if nuevo_status > 0 and modificados > 0:
            contenido = _desbloquear_pantallas_garajes(contenido)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado)
        actualizar_metadatos_guardado(ruta_guardado)

        if nuevo_status == 0:
            msg = f'Se vendieron/desactivaron {modificados} garajes vacíos.'
            if omitidos > 0:
                sede_txt = (
                    f' (Se mantuvo protegida la sede principal en {formatear_nombre_ciudad(hq_city)} y garajes ocupados).'
                    if hq_city
                    else f' ({omitidos} garajes se mantuvieron por tener camiones o conductores asignados).'
                )
                msg += sede_txt
            return True, msg

        etiqueta = 'Grande' if nuevo_status == 3 else 'Mediano' if nuevo_status == 2 else 'Pequeño'
        msg = f'Se actualizaron {modificados} garajes a tamaño {etiqueta}.'
        if omitidos > 0:
            msg += f' ({omitidos} garajes se mantuvieron en su tamaño actual por tener camiones/conductores ocupados).'
        return True, msg
    except Exception as e:
        return False, f'Error al actualizar garajes: {e}'


def cambiar_sede_hq(ruta_guardado: str, nueva_ciudad: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_pl = re.search(r'^(player\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_pl:
            return False, 'No se encontró el bloque player en la partida.'

        pl_body = re.sub(r'\bhq_city:\s*[^\s\r\n]+', f'hq_city: {nueva_ciudad}', m_pl.group(2), count=1)
        contenido = contenido[:m_pl.start()] + m_pl.group(1) + pl_body + m_pl.group(3) + contenido[m_pl.end():]

        patron_g = rf'^(garage\s*:\s*garage\.{re.escape(nueva_ciudad)}\s*\{{)(.*?)^(}})'
        m_g = re.search(patron_g, contenido, re.M | re.S)
        if m_g:
            m_st = re.search(r'\bstatus:\s*(\d+)', m_g.group(2))
            if m_st and int(m_st.group(1)) == 0:
                ok_t, nuevo_cuerpo = _transformar_cuerpo_garaje(m_g.group(2), 3)
                if ok_t:
                    contenido = contenido[:m_g.start()] + m_g.group(1) + nuevo_cuerpo + m_g.group(3) + contenido[m_g.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado)
        actualizar_metadatos_guardado(ruta_guardado)
        return True, f'Sede central (HQ) trasladada a {formatear_nombre_ciudad(nueva_ciudad)}.'
    except Exception as e:
        return False, f'Error al cambiar sede HQ: {e}'

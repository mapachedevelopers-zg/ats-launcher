import re
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    _encontrar_vehiculo_activo_id,
    abrir_partida_para_edicion,
)


def _localizar_camion_activo(contenido: str) -> tuple[re.Match | None, str]:
    """Devuelve el Match del bloque vehicle activo del jugador o mensaje de error."""
    m_pl = re.search(r'^player\s*:\s*[^\{]+\{(.*?)^\}', contenido, re.M | re.S)
    pl = m_pl.group(1) if m_pl else ''
    veh_id = _encontrar_vehiculo_activo_id(contenido, pl)
    if not veh_id:
        return None, 'No se detectó un camión activo en esta partida.'

    patron_veh = rf'^(vehicle\s*:\s*{re.escape(veh_id)}\s*\{{)(.*?)^(}})'
    m_veh = re.search(patron_veh, contenido, re.M | re.S)
    if not m_veh:
        return None, 'No se encontró el bloque del camión activo.'
    return m_veh, ''


def reparar_vehiculos_partida(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        contenido = re.sub(
            r'\b(engine_wear|transmission_wear|cabin_wear|chassis_wear|trailer_body_wear)(_unfixable)?:\s*[^\s\r\n]+',
            r'\1\2: 0',
            contenido,
        )
        contenido = re.sub(
            r'\b(wheels_wear(?:_unfixable)?\[\d+\]):\s*[^\s\r\n]+',
            r'\1: 0',
            contenido,
        )

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, 'Camiones y remolques reparados al 100% (0% daño y 0% desgaste permanente).'
    except Exception as e:
        return False, f'Error al reparar vehículos: {e}'


def llenar_combustible_partida(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        contenido = re.sub(r'\bfuel_relative:\s*[^\s\r\n]+', 'fuel_relative: 1', contenido)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, 'Tanque de combustible llenado al 100%.'
    except Exception as e:
        return False, f'Error al llenar combustible: {e}'


def cambiar_placa_camion(ruta_guardado: str, nuevo_texto: str, nuevo_estado: str = '') -> tuple[bool, str]:
    texto_limpio = nuevo_texto.strip().replace('"', '')
    estado_limpio = (nuevo_estado or '').strip().replace('"', '').lower()
    if not texto_limpio:
        return False, 'El texto de la placa no puede estar vacío.'

    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_veh, err = _localizar_camion_activo(contenido)
        if not m_veh:
            return False, err

        vb = m_veh.group(2)
        m_plate = re.search(r'\blicense_plate:\s*"([^"]*)"', vb)
        if m_plate:
            partes = m_plate.group(1).split('|', 1)
            left_actual = partes[0]
            state_original = partes[1] if len(partes) > 1 else 'california'
            state_final = estado_limpio if estado_limpio else state_original
            if '<font' in left_actual:
                nuevo_left = re.sub(r'(<font[^>]*>)([^<]+)(</font>)', rf'\g<1>{texto_limpio}\g<3>', left_actual, count=1)
            else:
                nuevo_left = texto_limpio
            nueva_placa_valor = f'{nuevo_left}|{state_final}'
            vb_nuevo = re.sub(r'\blicense_plate:\s*"[^"]*"', f'license_plate: "{nueva_placa_valor}"', vb, count=1)
        else:
            state_final = estado_limpio if estado_limpio else 'california'
            nueva_placa_valor = f'{texto_limpio}|{state_final}'
            vb_nuevo = vb.rstrip() + f'\n license_plate: "{nueva_placa_valor}"\n'
        contenido = contenido[:m_veh.start()] + m_veh.group(1) + vb_nuevo + m_veh.group(3) + contenido[m_veh.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, f"Matrícula actualizada a '{texto_limpio}' ({state_final})."
    except Exception as e:
        return False, f'Error al cambiar matrícula: {e}'


def cambiar_odometro_camion(ruta_guardado: str, nuevo_odometro: int) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_veh, err = _localizar_camion_activo(contenido)
        if not m_veh:
            return False, err

        vb = m_veh.group(2)
        val = max(0, int(nuevo_odometro))
        vb = re.sub(r'\bodometer:\s*\d+', f'odometer: {val}', vb, count=1)
        vb = re.sub(r'\bodometer_float_part:\s*[^\s\r\n]+', 'odometer_float_part: 0', vb, count=1)
        vb = re.sub(r'\bintegrity_odometer:\s*\d+', f'integrity_odometer: {val}', vb, count=1)
        vb = re.sub(r'\bintegrity_odometer_float_part:\s*[^\s\r\n]+', 'integrity_odometer_float_part: 0', vb, count=1)

        contenido = contenido[:m_veh.start()] + m_veh.group(1) + vb + m_veh.group(3) + contenido[m_veh.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, f'Odómetro actualizado a {val:,} km/mi.'
    except Exception as e:
        return False, f'Error al cambiar odómetro: {e}'


def restablecer_viaje_camion(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_veh, err = _localizar_camion_activo(contenido)
        if not m_veh:
            return False, err

        vb = m_veh.group(2)
        for campo in (
            'trip_fuel_l', 'trip_fuel',
            'trip_recuperation_kwh', 'trip_recuperation',
            'trip_distance_km', 'trip_distance',
            'trip_time_min', 'trip_time',
        ):
            vb = re.sub(rf'\b{campo}:\s*[^\s\r\n]+', f'{campo}: 0', vb, count=1)

        contenido = contenido[:m_veh.start()] + m_veh.group(1) + vb + m_veh.group(3) + contenido[m_veh.end():]
        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, 'Contador de viaje del camión reiniciado.'
    except Exception as e:
        return False, f'Error al reiniciar el viaje: {e}'

import re
from gestor_perfiles.lectura import _extraer_todas_las_ciudades
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    _reemplazar_array_sii,
    abrir_partida_para_edicion,
    actualizar_metadatos_guardado,
    es_archivo_saneado_en_cache,
)


def desbloquear_exploracion_partida(
    ruta_guardado: str,
    ciudades: bool = False,
    concesionarios: bool = False,
    agencias: bool = False,
    miradores: bool = False,
) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco:
            return False, 'No se encontró el bloque economy en la partida.'

        eco_body = m_eco.group(2)
        todas_ciudades = _extraer_todas_las_ciudades(eco_body)
        if not todas_ciudades and (ciudades or concesionarios or agencias):
            return False, 'No se detectaron ciudades registradas en esta partida.'

        acciones = []
        if ciudades and todas_ciudades:
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities', todas_ciudades)
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities_count', [1] * len(todas_ciudades))
            acciones.append(f'{len(todas_ciudades)} ciudades visitadas')

        if concesionarios and todas_ciudades:
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_dealers', todas_ciudades)
            acciones.append('todos los concesionarios')

        if agencias and todas_ciudades:
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_recruitments', todas_ciudades)
            acciones.append('todas las agencias de contratación')

        if miradores:
            m_cs = re.search(r'\bdiscovered_cutscene_items:\s*(\d+)', eco_body)
            total_cs = int(m_cs.group(1)) if m_cs else 0
            if total_cs > 0:
                eco_body = _reemplazar_array_sii(eco_body, 'discovered_cutscene_items_states', [2] * total_cs)
                acciones.append(f'{total_cs} miradores cinemáticos en galería')
            elif not (ciudades or concesionarios or agencias):
                return False, 'No hay miradores cinemáticos registrados en este mapa o partida.'

        if not acciones:
            return False, 'No se seleccionó ninguna acción de exploración.'

        nuevo_eco = m_eco.group(1) + eco_body + m_eco.group(3)
        contenido = contenido[:m_eco.start()] + nuevo_eco + contenido[m_eco.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, f"Se desbloquearon con éxito: {', '.join(acciones)}."
    except Exception as e:
        return False, f'Error al desbloquear exploración: {e}'


def bloquear_exploracion_partida(
    ruta_guardado: str,
    ciudades: bool = False,
    concesionarios: bool = False,
    agencias: bool = False,
    miradores: bool = False,
) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        estaba_saneado = es_archivo_saneado_en_cache(f_game)
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco:
            return False, 'No se encontró el bloque economy en la partida.'

        eco_body = m_eco.group(2)
        acciones = []

        if ciudades:
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities', [])
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities_count', [])
            acciones.append('ciudades descubiertas')

        if concesionarios:
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_dealers', [])
            acciones.append('concesionarios')

        if agencias:
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_recruitments', [])
            acciones.append('agencias de contratación')

        if miradores:
            m_cs = re.search(r'\bdiscovered_cutscene_items:\s*(\d+)', eco_body)
            total_cs = int(m_cs.group(1)) if m_cs else 0
            if total_cs > 0:
                eco_body = _reemplazar_array_sii(eco_body, 'discovered_cutscene_items_states', [1] * total_cs)
                acciones.append('miradores como no vistos')

        nuevo_eco = m_eco.group(1) + eco_body + m_eco.group(3)
        contenido = contenido[:m_eco.start()] + nuevo_eco + contenido[m_eco.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=not estaba_saneado)
        actualizar_metadatos_guardado(ruta_guardado)
        return True, f"Se bloquearon/reiniciaron con éxito: {', '.join(acciones)}."
    except Exception as e:
        return False, f'Error al bloquear exploración: {e}'


def desbloquear_miradores_partida(ruta_guardado: str) -> tuple[bool, str]:
    """Marca todos los miradores y cinemáticas del mapa descubiertos como vistos (estado 2)."""
    return desbloquear_exploracion_partida(
        ruta_guardado=ruta_guardado,
        ciudades=False,
        concesionarios=False,
        agencias=False,
        miradores=True,
    )


def ajustar_exploracion_partida(
    ruta_guardado: str,
    n_ciudades: int | None = None,
    n_concesionarios: int | None = None,
    n_agencias: int | None = None,
) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco:
            return False, 'No se encontró el bloque economy en la partida.'

        eco_body = m_eco.group(2)
        todas_ciudades = _extraer_todas_las_ciudades(eco_body)
        if not todas_ciudades:
            return False, 'No se detectaron ciudades registradas en esta partida.'

        def _recortar_o_ampliar(actuales: list[str], cantidad_obj: int) -> list[str]:
            n = max(0, min(len(todas_ciudades), int(cantidad_obj)))
            if n == 0:
                return []
            if len(actuales) >= n:
                return actuales[:n]
            vistos = set(actuales)
            resultado = list(actuales)
            for c in todas_ciudades:
                if c not in vistos:
                    resultado.append(c)
                    vistos.add(c)
                    if len(resultado) >= n:
                        break
            return resultado

        acciones = []
        if n_ciudades is not None:
            act_vc = re.findall(r'visited_cities\[\d+\]:\s*([^\s\r\n]+)', eco_body)
            nuevas_vc = _recortar_o_ampliar(act_vc, n_ciudades)
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities', nuevas_vc)
            eco_body = _reemplazar_array_sii(eco_body, 'visited_cities_count', [1] * len(nuevas_vc))
            acciones.append(f'ciudades descubiertas: {len(nuevas_vc)}')

        if n_concesionarios is not None:
            act_ud = re.findall(r'unlocked_dealers\[\d+\]:\s*([^\s\r\n]+)', eco_body)
            nuevos_ud = _recortar_o_ampliar(act_ud, n_concesionarios)
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_dealers', nuevos_ud)
            acciones.append(f'concesionarios: {len(nuevos_ud)}')

        if n_agencias is not None:
            act_ur = re.findall(r'unlocked_recruitments\[\d+\]:\s*([^\s\r\n]+)', eco_body)
            nuevas_ur = _recortar_o_ampliar(act_ur, n_agencias)
            eco_body = _reemplazar_array_sii(eco_body, 'unlocked_recruitments', nuevas_ur)
            acciones.append(f'agencias: {len(nuevas_ur)}')

        nuevo_eco = m_eco.group(1) + eco_body + m_eco.group(3)
        contenido = contenido[:m_eco.start()] + nuevo_eco + contenido[m_eco.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, f"Exploración actualizada ({', '.join(acciones)})."
    except Exception as e:
        return False, f'Error al ajustar exploración: {e}'

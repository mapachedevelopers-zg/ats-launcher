import re
from gestor_perfiles.saneador import _guardar_contenido_partida_sano
from gestor_perfiles.sii_io import (
    _desbloquear_pantallas_sii,
    abrir_partida_para_edicion,
    actualizar_metadatos_guardado,
)


_LIMITES_XP_NIVEL_1_A_30 = [
    200, 700, 1400, 2300, 3400, 4700, 6200, 7900, 9800, 11900,
    14200, 16700, 19400, 22300, 25400, 28700, 32200, 35900, 39900, 44200,
    48800, 53700, 58900, 64400, 70200, 76300, 82700, 89400, 96400, 103700,
]


def formatear_saldo_usd(monto: int) -> str:
    """Devuelve el monto formateado con comas y el sufijo USD."""
    return f'{monto:,.0f} USD'


def calcular_nivel_ats(xp: int) -> tuple[int, int, int]:
    """Retorna (nivel, xp_en_nivel_actual, xp_requerida_para_subir) usando la tabla oficial de ATS."""
    if xp <= 0:
        return 0, 0, 200

    if xp < _LIMITES_XP_NIVEL_1_A_30[-1]:
        acumulado_previo = 0
        for nivel, limite in enumerate(_LIMITES_XP_NIVEL_1_A_30):
            if xp < limite:
                return nivel, xp - acumulado_previo, limite - acumulado_previo
            acumulado_previo = limite

    xp_base_lvl30 = _LIMITES_XP_NIVEL_1_A_30[-1]
    xp_restante = xp - xp_base_lvl30
    niveles_extra = xp_restante // 7300
    xp_progreso = xp_restante % 7300
    return 30 + niveles_extra, xp_progreso, 7300


def calcular_xp_para_nivel(nivel_objetivo: int) -> int:
    """Devuelve la cantidad exacta de XP necesaria para alcanzar el nivel objetivo en ATS."""
    if nivel_objetivo <= 0:
        return 0
    if nivel_objetivo <= 30:
        return _LIMITES_XP_NIVEL_1_A_30[nivel_objetivo - 1]
    return _LIMITES_XP_NIVEL_1_A_30[-1] + (nivel_objetivo - 30) * 7300


def guardar_dinero_partida(ruta_guardado: str, dinero: int) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        contenido = re.sub(r'\bmoney_account:\s*-?\d+', f'money_account: {dinero}', contenido, count=1)
        _guardar_contenido_partida_sano(f_game, contenido, None, sanear=False)
        actualizar_metadatos_guardado(ruta_guardado, dinero=dinero)
        return True, 'Saldo en cuenta actualizado con éxito.'
    except Exception as e:
        return False, f'Error al guardar saldo: {e}'


def guardar_xp_partida(ruta_guardado: str, xp: int) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if m_eco:
            eco_body = re.sub(r'\bexperience_points:\s*\d+', f'experience_points: {xp}', m_eco.group(2), count=1)
            if xp >= 200:
                eco_body = _desbloquear_pantallas_sii(
                    eco_body,
                    {
                        'screen.bank',
                        'screen.mail',
                        'screen.skills',
                        'truck.dealer_map',
                        'truck.eshop.used_trucks',
                        'truck.upgrades',
                        'trailer.upgrades',
                    },
                )
            contenido = contenido[:m_eco.start()] + m_eco.group(1) + eco_body + m_eco.group(3) + contenido[m_eco.end():]
        else:
            contenido = re.sub(r'\bexperience_points:\s*\d+', f'experience_points: {xp}', contenido, count=1)

        _guardar_contenido_partida_sano(f_game, contenido, None, sanear=False)
        actualizar_metadatos_guardado(ruta_guardado, xp=xp)
        return True, 'Puntos de experiencia actualizados con éxito.'
    except Exception as e:
        return False, f'Error al guardar XP: {e}'


def guardar_skills_partida(ruta_guardado: str, skills: dict) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_eco = re.search(r'^(economy\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_eco:
            return False, 'No se encontró el bloque economy en la partida.'

        eco_body = m_eco.group(2)
        adr_mask = max(0, min(63, int(skills.get('adr', 0))))
        eco_body = re.sub(r'\badr:\s*\d+', f'adr: {adr_mask}', eco_body, count=1)

        tiene_alguna = adr_mask > 0
        for sk in ('long_dist', 'heavy', 'fragile', 'urgent', 'mechanical'):
            if sk in skills:
                val = max(0, min(6, int(skills[sk])))
                if val > 0:
                    tiene_alguna = True
                eco_body = re.sub(rf'\b{sk}:\s*\d+', f'{sk}: {val}', eco_body, count=1)

        if tiene_alguna:
            eco_body = _desbloquear_pantallas_sii(eco_body, {'screen.skills'})
            m_xp = re.search(r'\bexperience_points:\s*(\d+)', eco_body)
            if m_xp and int(m_xp.group(1)) < 200:
                eco_body = re.sub(r'\bexperience_points:\s*\d+', 'experience_points: 200', eco_body, count=1)

        nuevo_eco = m_eco.group(1) + eco_body + m_eco.group(3)
        contenido = contenido[:m_eco.start()] + nuevo_eco + contenido[m_eco.end():]

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, 'Habilidades del conductor actualizadas correctamente.'
    except Exception as e:
        return False, f'Error al guardar habilidades: {e}'


def liquidar_prestamos_partida(ruta_guardado: str) -> tuple[bool, str]:
    ok, contenido, f_game = abrir_partida_para_edicion(ruta_guardado)
    if not ok:
        return False, contenido

    try:
        m_bank = re.search(r'^(bank\s*:\s*[^\{]+\{)(.*?)^(})', contenido, re.M | re.S)
        if not m_bank:
            return False, 'No se encontró el bloque bancario en la partida.'

        bank_body = m_bank.group(2)
        bank_body = re.sub(
            r'^[ \t]*loans:\s*\d+(?:\r?\n[ \t]*loans\[\d+\]:\s*[^\r\n]+)*',
            ' loans: 0',
            bank_body,
            count=1,
            flags=re.M,
        )
        bank_body = re.sub(r'\boverdraft:\s*(true|false)', 'overdraft: false', bank_body)
        bank_body = re.sub(r'\boverdraft_timer:\s*[^\s\r\n]+', 'overdraft_timer: 0', bank_body)
        bank_body = re.sub(r'\boverdraft_warn_count:\s*\d+', 'overdraft_warn_count: 0', bank_body)
        bank_body = re.sub(r'\bsell_players_truck_later:\s*(true|false)', 'sell_players_truck_later: false', bank_body)
        bank_body = re.sub(r'\bsell_players_trailer_later:\s*(true|false)', 'sell_players_trailer_later: false', bank_body)

        nuevo_bank = m_bank.group(1) + bank_body + m_bank.group(3)
        contenido = contenido[:m_bank.start()] + nuevo_bank + contenido[m_bank.end():]
        contenido = re.sub(r'^bank_loan\s*:\s*[^\s\{]+\s*\{.*?^\}\r?\n?', '', contenido, flags=re.M | re.S)

        _guardar_contenido_partida_sano(f_game, contenido, ruta_guardado, sanear=False)
        return True, 'Todos los préstamos y deudas bancarias han sido liquidados.'
    except Exception as e:
        return False, f'Error al liquidar préstamos: {e}'

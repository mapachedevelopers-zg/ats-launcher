import os
import re
from gestor_perfiles.sii_io import verificar_juego_cerrado

OPCIONES_ESTABILIDAD = [
    ("g_truck_stability", "Estabilidad del camión", "1.0", "0.5"),
    ("g_trailer_stability", "Estabilidad del remolque", "1.0", "0.5"),
    ("g_suspension_stiffness", "Rigidez de suspensión", "1.0", "0.5"),
    ("g_cabin_suspension_stiffness", "Rigidez de la cabina", "1.0", "0.5"),
]


def _ruta_config_perfil(ruta_guardado: str) -> str:
    ruta_perfil = os.path.dirname(os.path.dirname(os.path.abspath(ruta_guardado)))
    return os.path.join(ruta_perfil, "config.cfg")


def obtener_valores_estabilidad_perfil(ruta_guardado: str) -> dict[str, str]:
    """Obtiene los valores actuales de estabilidad y rigidez del config.cfg del perfil."""
    valores = {
        "g_truck_stability": "0.5",
        "g_trailer_stability": "0.5",
        "g_suspension_stiffness": "0.5",
        "g_cabin_suspension_stiffness": "0.5",
    }
    try:
        cfg = _ruta_config_perfil(ruta_guardado)
        if os.path.exists(cfg):
            with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
            for clave in valores:
                m = re.search(f'uset\\s+{clave}\\s+"([^"]*)"', contenido)
                if m:
                    valores[clave] = m.group(1)
    except Exception:
        pass
    return valores


def modificar_parametro_config_perfil(ruta_guardado: str, clave: str, valor: str) -> tuple[bool, str]:
    """Modifica un parámetro específico dentro del config.cfg del perfil seleccionado."""
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    try:
        cfg = _ruta_config_perfil(ruta_guardado)
        if not os.path.exists(cfg):
            return False, "No se encontró el archivo 'config.cfg' del perfil."

        with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()

        nuevas = []
        modificado = False
        for lin in lineas:
            if lin.strip().startswith(f"uset {clave}"):
                nuevas.append(f'uset {clave} "{valor}"\n')
                modificado = True
            else:
                nuevas.append(lin)

        if not modificado:
            nuevas.append(f'uset {clave} "{valor}"\n')

        with open(cfg, "w", encoding="utf-8") as f:
            f.writelines(nuevas)

        return True, "Parámetro actualizado correctamente."
    except Exception as e:
        return False, f"Error al modificar config.cfg: {e}"


def modificar_todos_parametros_estabilidad(ruta_guardado: str, activar: bool) -> tuple[bool, str]:
    """Activa al máximo (1.0) o restablece a normal (0.5) todos los parámetros de estabilidad del perfil."""
    juego_ok, msg_juego = verificar_juego_cerrado()
    if not juego_ok:
        return False, msg_juego

    try:
        cfg = _ruta_config_perfil(ruta_guardado)
        if not os.path.exists(cfg):
            return False, "No se encontró el archivo 'config.cfg' del perfil."

        val = "1.0" if activar else "0.5"
        claves = {clave: val for clave, _, _, _ in OPCIONES_ESTABILIDAD}

        with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()

        nuevas = []
        modificadas = set()
        for lin in lineas:
            l_str = lin.strip()
            coincide = False
            for k, v in claves.items():
                if l_str.startswith(f"uset {k}"):
                    nuevas.append(f'uset {k} "{v}"\n')
                    modificadas.add(k)
                    coincide = True
                    break
            if not coincide:
                nuevas.append(lin)

        for k, v in claves.items():
            if k not in modificadas:
                nuevas.append(f'uset {k} "{v}"\n')

        with open(cfg, "w", encoding="utf-8") as f:
            f.writelines(nuevas)

        return True, ("Todos los parámetros activados al 100%" if activar else "Parámetros restablecidos a normales (50%)")
    except Exception as e:
        return False, f"Error al modificar config.cfg: {e}"


def obtener_estado_estabilidad_perfil(ruta_guardado: str) -> bool:
    """Verifica si el perfil actual tiene la estabilidad antivuelco al 100% en su config.cfg."""
    try:
        vals = obtener_valores_estabilidad_perfil(ruta_guardado)
        return (
            float(vals.get("g_truck_stability", 0)) >= 1.0
            and float(vals.get("g_trailer_stability", 0)) >= 1.0
        )
    except Exception:
        return False


def alternar_estabilidad_perfil(ruta_guardado: str, activar: bool) -> tuple[bool, str]:
    return modificar_todos_parametros_estabilidad(ruta_guardado, activar)

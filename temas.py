import os
import sys
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon, QRadialGradient, QPolygonF
from PySide6.QtCore import Qt, QPointF
from download_manager import cargar_config_usuario, guardar_config_usuario

TEMA_POR_DEFECTO = "Dorado Chasis"

TEMAS = {
    "Dorado Chasis": {
        "acento": "#E5A93C",
        "hover": "#F1C40F",
        "borde_oscuro": "#C58922",
        "fondo_suave": "#2D2517",
        "texto_claro": "#FFC86B",
        "contraste": "#0F172A",
        "circulo_luz": "#FFFBEB",
        "circulo_base": "#F59E0B",
        "circulo_borde": "#D97706",
        "fondo_principal": "#0F1115",
        "fondo_tarjeta": "#181A20",
        "fondo_sidebar": "#0B0C0E",
        "fondo_boton_menu": "#181A20",
        "fondo_boton_hover": "#232731",
        "fondo_input": "#1E1E1E",
        "borde_suave": "#1F222A",
        "borde_tarjeta": "#262932",
    },
    "Azul Eléctrico": {
        "acento": "#3B82F6",
        "hover": "#60A5FA",
        "borde_oscuro": "#1D4ED8",
        "fondo_suave": "#111D33",
        "texto_claro": "#93C5FD",
        "contraste": "#FFFFFF",
        "circulo_luz": "#BFDBFE",
        "circulo_base": "#3B82F6",
        "circulo_borde": "#2563EB",
        "fondo_principal": "#090D14",
        "fondo_tarjeta": "#0F1724",
        "fondo_sidebar": "#06090F",
        "fondo_boton_menu": "#121C2B",
        "fondo_boton_hover": "#1A283D",
        "fondo_input": "#101927",
        "borde_suave": "#152236",
        "borde_tarjeta": "#1D2D46",
    },
    "Rojo Racing": {
        "acento": "#EF4444",
        "hover": "#F87171",
        "borde_oscuro": "#B91C1C",
        "fondo_suave": "#2A1318",
        "texto_claro": "#FCA5A5",
        "contraste": "#FFFFFF",
        "circulo_luz": "#FECACA",
        "circulo_base": "#EF4444",
        "circulo_borde": "#DC2626",
        "fondo_principal": "#120A0C",
        "fondo_tarjeta": "#1A0F13",
        "fondo_sidebar": "#0A0506",
        "fondo_boton_menu": "#221217",
        "fondo_boton_hover": "#301821",
        "fondo_input": "#1C1014",
        "borde_suave": "#281319",
        "borde_tarjeta": "#381923",
    },
    "Verde Esmeralda": {
        "acento": "#10B981",
        "hover": "#34D399",
        "borde_oscuro": "#047857",
        "fondo_suave": "#0F241C",
        "texto_claro": "#6EE7B7",
        "contraste": "#0F172A",
        "circulo_luz": "#A7F3D0",
        "circulo_base": "#10B981",
        "circulo_borde": "#059669",
        "fondo_principal": "#070F0C",
        "fondo_tarjeta": "#0D1914",
        "fondo_sidebar": "#040907",
        "fondo_boton_menu": "#11211A",
        "fondo_boton_hover": "#182F25",
        "fondo_input": "#0E1C16",
        "borde_suave": "#142920",
        "borde_tarjeta": "#1C3A2D",
    },
    "Púrpura Neón": {
        "acento": "#A855F7",
        "hover": "#C084FC",
        "borde_oscuro": "#7E22CE",
        "fondo_suave": "#25143C",
        "texto_claro": "#D8B4FE",
        "contraste": "#FFFFFF",
        "circulo_luz": "#F3E8FF",
        "circulo_base": "#A855F7",
        "circulo_borde": "#9333EA",
        "fondo_principal": "#0E0916",
        "fondo_tarjeta": "#160F23",
        "fondo_sidebar": "#08050D",
        "fondo_boton_menu": "#1E1330",
        "fondo_boton_hover": "#2B1A44",
        "fondo_input": "#191027",
        "borde_suave": "#23173A",
        "borde_tarjeta": "#332154",
    },
    "Blanco Titanio": {
        "acento": "#E2E8F0",
        "hover": "#FFFFFF",
        "borde_oscuro": "#94A3B8",
        "fondo_suave": "#1C2028",
        "texto_claro": "#F8FAFC",
        "contraste": "#0F172A",
        "circulo_luz": "#FFFFFF",
        "circulo_base": "#E2E8F0",
        "circulo_borde": "#94A3B8",
        "fondo_principal": "#0B0C0E",
        "fondo_tarjeta": "#14161A",
        "fondo_sidebar": "#070809",
        "fondo_boton_menu": "#1A1D23",
        "fondo_boton_hover": "#262A33",
        "fondo_input": "#17191E",
        "borde_suave": "#1D2027",
        "borde_tarjeta": "#2C313C",
    },
    "Rosa Sakura": {
        "acento": "#F472B6",
        "hover": "#FB7185",
        "borde_oscuro": "#DB2777",
        "fondo_suave": "#2E1424",
        "texto_claro": "#FCE7F3",
        "contraste": "#FFFFFF",
        "circulo_luz": "#FDF2F8",
        "circulo_base": "#F472B6",
        "circulo_borde": "#DB2777",
        "fondo_principal": "#130911",
        "fondo_tarjeta": "#1C0F1A",
        "fondo_sidebar": "#0C050B",
        "fondo_boton_menu": "#241221",
        "fondo_boton_hover": "#33172F",
        "fondo_input": "#1E0F1B",
        "borde_suave": "#2A1426",
        "borde_tarjeta": "#3C1B37",
    },
    "Cian Cyberpunk": {
        "acento": "#06B6D4",
        "hover": "#22D3EE",
        "borde_oscuro": "#0891B2",
        "fondo_suave": "#0D2228",
        "texto_claro": "#CFFAFE",
        "contraste": "#0B131B",
        "circulo_luz": "#E0F2FE",
        "circulo_base": "#06B6D4",
        "circulo_borde": "#0891B2",
        "fondo_principal": "#070F13",
        "fondo_tarjeta": "#0D1920",
        "fondo_sidebar": "#050A0D",
        "fondo_boton_menu": "#112028",
        "fondo_boton_hover": "#182C37",
        "fondo_input": "#0F1A21",
        "borde_suave": "#142530",
        "borde_tarjeta": "#1C3545",
    },
    "Naranja Sunset": {
        "acento": "#F97316",
        "hover": "#FB923C",
        "borde_oscuro": "#EA580C",
        "fondo_suave": "#2C180E",
        "texto_claro": "#FFEDD5",
        "contraste": "#FFFFFF",
        "circulo_luz": "#FFF7ED",
        "circulo_base": "#F97316",
        "circulo_borde": "#EA580C",
        "fondo_principal": "#110A07",
        "fondo_tarjeta": "#1A0F0A",
        "fondo_sidebar": "#0A0503",
        "fondo_boton_menu": "#24140D",
        "fondo_boton_hover": "#331C13",
        "fondo_input": "#1C100A",
        "borde_suave": "#28160E",
        "borde_tarjeta": "#3B2014",
    },
    "Lavanda Mística": {
        "acento": "#818CF8",
        "hover": "#A5B4FC",
        "borde_oscuro": "#6366F1",
        "fondo_suave": "#191A35",
        "texto_claro": "#E0E7FF",
        "contraste": "#FFFFFF",
        "circulo_luz": "#EEF2FF",
        "circulo_base": "#818CF8",
        "circulo_borde": "#6366F1",
        "fondo_principal": "#0B0C16",
        "fondo_tarjeta": "#121422",
        "fondo_sidebar": "#07070E",
        "fondo_boton_menu": "#181B2E",
        "fondo_boton_hover": "#222640",
        "fondo_input": "#141626",
        "borde_suave": "#1B1E34",
        "borde_tarjeta": "#272B4B",
    },
    "Menta Fresca": {
        "acento": "#14B8A6",
        "hover": "#2DD4BF",
        "borde_oscuro": "#0D9488",
        "fondo_suave": "#0E2320",
        "texto_claro": "#CCFBF1",
        "contraste": "#0B1A17",
        "circulo_luz": "#F0FDFA",
        "circulo_base": "#14B8A6",
        "circulo_borde": "#0F766E",
        "fondo_principal": "#070F0D",
        "fondo_tarjeta": "#0D1A16",
        "fondo_sidebar": "#040A08",
        "fondo_boton_menu": "#11221D",
        "fondo_boton_hover": "#173029",
        "fondo_input": "#0E1B17",
        "borde_suave": "#142721",
        "borde_tarjeta": "#1B3930",
    },
    "Rubí Imperial": {
        "acento": "#E11D48",
        "hover": "#F43F5E",
        "borde_oscuro": "#BE123C",
        "fondo_suave": "#2A0E16",
        "texto_claro": "#FFE4E6",
        "contraste": "#FFFFFF",
        "circulo_luz": "#FFF1F2",
        "circulo_base": "#E11D48",
        "circulo_borde": "#BE123C",
        "fondo_principal": "#12070B",
        "fondo_tarjeta": "#1A0A10",
        "fondo_sidebar": "#090306",
        "fondo_boton_menu": "#220D15",
        "fondo_boton_hover": "#30121D",
        "fondo_input": "#1A0A10",
        "borde_suave": "#280E19",
        "borde_tarjeta": "#3B1425",
    },
}


def obtener_ruta_recurso(nombre_archivo: str) -> str:
    """Devuelve la ruta absoluta normalizada con '/' de un archivo en recursos."""
    if hasattr(sys, "_MEIPASS"):
        ruta = os.path.join(sys._MEIPASS, "recursos", nombre_archivo)
    else:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos", nombre_archivo)
    return os.path.abspath(ruta).replace("\\", "/")


def asegurar_flechas_dropdown():
    """Garantiza la existencia de las flechas triangulares invertidas para las listas desplegables."""
    ruta_normal = obtener_ruta_recurso("arrow_down.png")
    ruta_hover = obtener_ruta_recurso("arrow_down_hover.png")

    if not os.path.exists(ruta_normal) or not os.path.exists(ruta_hover):
        os.makedirs(os.path.dirname(ruta_normal), exist_ok=True)
        for ruta, color in ((ruta_normal, "#94A3B8"), (ruta_hover, "#FFFFFF")):
            pm = QPixmap(16, 16)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            p.setBrush(QColor(color))
            p.setPen(Qt.NoPen)
            poly = QPolygonF([QPointF(3.5, 6.0), QPointF(12.5, 6.0), QPointF(8.0, 11.0)])
            p.drawPolygon(poly)
            p.end()
            pm.save(ruta)


def obtener_nombre_tema_actual() -> str:
    """Devuelve el nombre del tema guardado en la configuración del usuario."""
    config = cargar_config_usuario()
    nombre = config.get("tema_launcher", TEMA_POR_DEFECTO)
    if nombre not in TEMAS:
        return TEMA_POR_DEFECTO
    return nombre


def obtener_tema_actual() -> dict:
    """Devuelve el diccionario de colores del tema activo."""
    return TEMAS[obtener_nombre_tema_actual()]


def guardar_tema_actual(nombre_tema: str) -> None:
    """Guarda el tema elegido por el usuario en user_config.json."""
    if nombre_tema not in TEMAS:
        nombre_tema = TEMA_POR_DEFECTO
    config = cargar_config_usuario()
    config["tema_launcher"] = nombre_tema
    guardar_config_usuario(config)


def crear_icono_tema(nombre_tema: str, size: int = 16) -> QIcon:
    """Dibuja un círculo de color con degradado suave y borde nítido para el selector de temas."""
    datos = TEMAS.get(nombre_tema, TEMAS[TEMA_POR_DEFECTO])
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    pintor = QPainter(pixmap)
    pintor.setRenderHint(QPainter.Antialiasing)

    grad = QRadialGradient(QPointF(size * 0.35, size * 0.32), size * 0.65)
    grad.setColorAt(0.0, QColor(datos["circulo_luz"]))
    grad.setColorAt(0.7, QColor(datos["circulo_base"]))
    grad.setColorAt(1.0, QColor(datos["acento"]))

    pluma = QPen(QColor(datos["circulo_borde"]), 1.2)
    pintor.setPen(pluma)
    pintor.setBrush(grad)
    pintor.drawEllipse(2, 2, size - 4, size - 4)
    pintor.end()

    return QIcon(pixmap)

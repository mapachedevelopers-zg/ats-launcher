from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from utils import aplicar_sombra
from i18n import tr
from constantes import REDES

# CAMBIO: los enlaces ya no estan escritos aqui; se leen de config_launcher.json
# (seccion "redes"). Enlace vacio = botones desactivados.

class PaginaRedes(QWidget):
    def __init__(self):
        super().__init__()
        self._redes_ui = []
        diseño = QVBoxLayout(self)
        diseño.setContentsMargins(40, 20, 40, 20)
        diseño.setSpacing(15)

        # Título y subtítulo
        self.titulo = QLabel(tr("MIS REDES SOCIALES"))
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignCenter)
        diseño.addWidget(self.titulo)

        self.subtitulo = QLabel(
            tr("Únete a nuestra comunidad oficial para enterarte de actualizaciones, noticias y nuevos lanzamientos.")
        )
        self.subtitulo.setAlignment(Qt.AlignCenter)
        self.subtitulo.setStyleSheet(
            "color: #94A3B8; font-size: 12px; font-weight: 600; background: transparent;")
        diseño.addWidget(self.subtitulo)

        diseño.addSpacing(10)

        # Fila superior: YouTube y Facebook
        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(25)
        fila_superior.setAlignment(Qt.AlignCenter)

        t_youtube = self._crear_tarjeta_red(
            "YouTube", "CANAL DE YOUTUBE", "Tutoriales, mods, mapas y más.",
            REDES.get("youtube", "")
        )
        t_facebook = self._crear_tarjeta_red(
            "Facebook", "PÁGINA DE FACEBOOK", "Noticias, publicaciones y comunidad.",
            REDES.get("facebook", "")
        )

        fila_superior.addWidget(t_youtube)
        fila_superior.addWidget(t_facebook)
        diseño.addLayout(fila_superior)

        # Fila inferior: Discord
        fila_inferior = QHBoxLayout()
        fila_inferior.setAlignment(Qt.AlignCenter)

        t_discord = self._crear_tarjeta_red(
            "Discord", "SERVIDOR DE DISCORD", "Soporte técnico, charlas y ayudas.",
            REDES.get("discord", "")
        )

        fila_inferior.addWidget(t_discord)
        diseño.addLayout(fila_inferior)

        diseño.addStretch()

    def _crear_tarjeta_red(self, nombre, titulo_red, desc_red, enlace):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        tarjeta.setFixedSize(300, 210)
        aplicar_sombra(tarjeta)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(18, 14, 18, 14)
        layout_tarjeta.setSpacing(8)

        btn_logo = QPushButton()
        btn_logo.setObjectName("paypal")
        btn_logo.setFixedSize(250, 80)
        btn_logo.setCursor(Qt.PointingHandCursor)
        btn_logo.setProperty("recurso", f"red:{nombre}")
        btn_logo.clicked.connect(
            lambda _, u=enlace: QDesktopServices.openUrl(QUrl(u)))

        lbl_titulo = QLabel(tr(titulo_red))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet(
            "color: #F8FAFC; font-size: 13px; font-weight: 800; background: transparent;")

        lbl_desc = QLabel(tr(desc_red))
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;")

        btn_unirse = QPushButton(tr("ABRIR ENLACE ↗"))
        btn_unirse.setCursor(Qt.PointingHandCursor)
        btn_unirse.setFixedHeight(32)
        btn_unirse.clicked.connect(
            lambda _, u=enlace: QDesktopServices.openUrl(QUrl(u)))

        if not enlace:
            btn_logo.setEnabled(False)
            btn_unirse.setEnabled(False)
            btn_unirse.setToolTip("Enlace sin configurar (config_launcher.json)")

        layout_tarjeta.addWidget(btn_logo, alignment=Qt.AlignCenter)
        layout_tarjeta.addWidget(lbl_titulo)
        layout_tarjeta.addWidget(lbl_desc)
        layout_tarjeta.addWidget(btn_unirse)

        self._redes_ui.append({
            "lbl_titulo": lbl_titulo,
            "lbl_desc": lbl_desc,
            "btn_unirse": btn_unirse,
            "titulo_red": titulo_red,
            "desc_red": desc_red,
        })

        return tarjeta

    def actualizar_textos_idioma(self):
        """Actualiza los títulos y botones de la sección de redes sociales."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("MIS REDES SOCIALES"))
        if hasattr(self, "subtitulo"):
            self.subtitulo.setText(tr("Únete a nuestra comunidad oficial para enterarte de actualizaciones, noticias y nuevos lanzamientos."))
        for item in getattr(self, "_redes_ui", []):
            item["lbl_titulo"].setText(tr(item["titulo_red"]))
            item["lbl_desc"].setText(tr(item["desc_red"]))
            item["btn_unirse"].setText(tr("ABRIR ENLACE ↗"))

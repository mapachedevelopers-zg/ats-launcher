from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt
from utils import aplicar_sombra
from i18n import tr


class PaginaOrden(QWidget):
    def __init__(self):
        super().__init__()
        diseño_principal = QVBoxLayout(self)
        diseño_principal.setContentsMargins(40, 25, 40, 25)
        diseño_principal.setSpacing(14)

        # Título
        self.titulo = QLabel(tr("ORDEN DE LOS MODS"))
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignCenter)
        diseño_principal.addWidget(self.titulo)

        self.lbl_subtitulo = QLabel(
            tr("💡 Coloca los mods en este orden exacto dentro del Gestor de mods.")
        )
        self.lbl_subtitulo.setAlignment(Qt.AlignCenter)
        self.lbl_subtitulo.setStyleSheet("""
            QLabel {
                color: #94A3B8;
                font-size: 12px;
                font-weight: 600;
                background: #181A20;
                border: 1px solid #262932;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)
        diseño_principal.addWidget(self.lbl_subtitulo)

        # Tarjeta con la imagen de la guía de orden
        tarjeta_imagen = QFrame()
        tarjeta_imagen.setObjectName("marcoOrden")
        tarjeta_imagen.setStyleSheet("""
            QFrame#marcoOrden {
                background: #1A1C23;
                border: 1px solid #262932;
                border-radius: 10px;
            }
        """)
        aplicar_sombra(tarjeta_imagen)

        layout_tarjeta = QVBoxLayout(tarjeta_imagen)
        layout_tarjeta.setContentsMargins(15, 15, 15, 15)

        self.scroll_orden = QScrollArea()
        self.scroll_orden.setWidgetResizable(True)
        self.scroll_orden.setFrameShape(QFrame.NoFrame)
        self.scroll_orden.setStyleSheet("background: transparent;")

        contenedor_inner = QWidget()
        layout_inner = QVBoxLayout(contenedor_inner)
        layout_inner.setContentsMargins(0, 0, 0, 0)
        layout_inner.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.imagen_orden = QLabel("⏳ Carga de guía de orden...")
        self.imagen_orden.setAlignment(Qt.AlignCenter)
        self.imagen_orden.setStyleSheet(
            "color: #64748B; font-weight: 600; font-size: 13px; background: transparent;"
        )
        layout_inner.addWidget(self.imagen_orden, alignment=Qt.AlignCenter)

        self.scroll_orden.setWidget(contenedor_inner)
        layout_tarjeta.addWidget(self.scroll_orden)

        diseño_principal.addWidget(tarjeta_imagen, 1)

    def actualizar_textos_idioma(self):
        """Actualiza títulos y avisos del orden de mods."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("ORDEN DE LOS MODS"))
        if hasattr(self, "lbl_subtitulo"):
            self.lbl_subtitulo.setText(tr("💡 Coloca los mods en este orden exacto dentro del Gestor de mods."))
        if hasattr(self, "imagen_orden") and self.imagen_orden.text():
            self.imagen_orden.setText(tr("⏳ Carga de guía de orden..."))

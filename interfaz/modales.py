from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRect, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from i18n import tr
from interfaz.barra_titulo import ScrollVerticalModal
from temas import obtener_tema_actual


class _BaseModalAnimado(QWidget):
    """Base compartida para modales centrales con animación de apertura/cierre."""

    _nombre_objeto = "tarjetaModal"
    _ancho_modal = 520
    _alto_modal = 400

    def __init__(self, parent, icono_header: str, titulo_header: str, texto_boton: str,
                 origen_pos=None, al_cerrar_callback=None):
        super().__init__(parent)
        self.al_cerrar_callback = al_cerrar_callback
        self.origen_pos = origen_pos or QPoint(parent.width() // 2, parent.height() // 2)
        self.setGeometry(0, 0, parent.width(), parent.height())

        self.recuadro = QFrame(self)
        self.recuadro.setObjectName(self._nombre_objeto)
        self.recuadro.setStyleSheet(f"""
            #{self._nombre_objeto} {{
                background: #14161D;
                border: 1px solid #2D313E;
                border-radius: 12px;
            }}
        """)

        self.layout_recuadro = QVBoxLayout(self.recuadro)
        self.layout_recuadro.setContentsMargins(0, 0, 0, 16)
        self.layout_recuadro.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            background: #1C1F2B;
            border-bottom: 1px solid #2D313E;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        layout_header = QHBoxLayout(header)
        layout_header.setContentsMargins(20, 14, 16, 14)

        lbl_icon = QLabel(icono_header)
        lbl_icon.setStyleSheet("font-size: 18px; background: transparent;")

        lbl_titulo = QLabel(titulo_header)
        lbl_titulo.setStyleSheet("""
            color: #F1F5F9;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: transparent;
        """)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background: #E11D48;
            }
        """)
        btn_x.clicked.connect(self.cerrar_con_animacion)

        layout_header.addWidget(lbl_icon)
        layout_header.addSpacing(6)
        layout_header.addWidget(lbl_titulo)
        layout_header.addStretch()
        layout_header.addWidget(btn_x)
        self.layout_recuadro.addWidget(header)

        self.contenedor_scroll = QWidget()
        self.contenedor_scroll.setStyleSheet("background: transparent;")
        self.layout_scroll = QVBoxLayout(self.contenedor_scroll)
        self.layout_scroll.setContentsMargins(20, 16, 20, 16)

        self.scroll_area = ScrollVerticalModal()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #14161D;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2D313E;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #E5A93C; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.scroll_area.setWidget(self.contenedor_scroll)
        self.layout_recuadro.addWidget(self.scroll_area, 1)

        contenedor_btn = QWidget()
        contenedor_btn.setStyleSheet("background: transparent;")
        layout_btn_inf = QHBoxLayout(contenedor_btn)
        layout_btn_inf.setContentsMargins(20, 6, 20, 0)

        btn_aceptar = QPushButton(texto_boton)
        btn_aceptar.setFixedHeight(36)
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        tema_actual = obtener_tema_actual()
        btn_aceptar.setStyleSheet(f"""
            QPushButton {{
                background: {tema_actual['acento']};
                color: {tema_actual['contraste']};
                font-size: 12px;
                font-weight: 900;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background: {tema_actual['hover']};
            }}
        """)
        btn_aceptar.clicked.connect(self.cerrar_con_animacion)
        layout_btn_inf.addWidget(btn_aceptar)
        self.layout_recuadro.addWidget(contenedor_btn)

        self.setStyleSheet(f"{type(self).__name__} {{ background-color: rgba(0, 0, 0, 0.55); }}")

        self.target_rect = QRect(
            (parent.width() - self._ancho_modal) // 2,
            (parent.height() - self._alto_modal) // 2,
            self._ancho_modal,
            self._alto_modal,
        )
        self.start_rect = QRect(self.origen_pos.x(), self.origen_pos.y(), 10, 10)

        self.anim = QPropertyAnimation(self.recuadro, b"geometry")
        self.anim.setDuration(280)
        self.anim.setStartValue(self.start_rect)
        self.anim.setEndValue(self.target_rect)
        self.anim.setEasingCurve(QEasingCurve.OutBack)
        self.anim.start()

    def mousePressEvent(self, event):
        if not self.recuadro.geometry().contains(event.position().toPoint()):
            self.cerrar_con_animacion()
        super().mousePressEvent(event)

    def cerrar_con_animacion(self):
        self.anim_close = QPropertyAnimation(self.recuadro, b"geometry")
        self.anim_close.setDuration(200)
        self.anim_close.setStartValue(self.recuadro.geometry())
        self.anim_close.setEndValue(self.start_rect)
        self.anim_close.setEasingCurve(QEasingCurve.InBack)

        def _finalizar():
            if self.al_cerrar_callback:
                self.al_cerrar_callback()
            self.deleteLater()

        self.anim_close.finished.connect(_finalizar)
        self.anim_close.start()


class ModalNovedades(_BaseModalAnimado):
    """Modal de novedades con diseño pulido tipo Patch Notes y tarjetas estructuradas."""

    _nombre_objeto = "tarjetaNovedades"
    _ancho_modal = 520
    _alto_modal = 400

    def __init__(self, parent, titulo_version, texto_novedades, origen_pos=None, al_cerrar_callback=None):
        super().__init__(
            parent,
            icono_header="🚀",
            titulo_header=f"{tr('NOTAS DE LA VERSIÓN')} {titulo_version}",
            texto_boton=tr("¡ENTENDIDO!"),
            origen_pos=origen_pos or QPoint(parent.width() - 80, parent.height() - 60),
            al_cerrar_callback=al_cerrar_callback,
        )
        self.layout_scroll.setSpacing(8)

        for linea in [l.strip() for l in texto_novedades.split("\n") if l.strip()]:
            texto_clean = linea.lstrip("•-* ").strip()
            bloque = QFrame()
            bloque.setStyleSheet("""
                QFrame {
                    background: #1C202B;
                    border: 1px solid #262A37;
                    border-radius: 8px;
                }
                QFrame:hover { border-color: #3B4254; }
            """)
            layout_bloque = QHBoxLayout(bloque)
            layout_bloque.setContentsMargins(12, 10, 12, 10)
            layout_bloque.setSpacing(10)

            dot = QLabel("⚡")
            dot.setStyleSheet("font-size: 11px; background: transparent;")

            txt = QLabel(tr(texto_clean))
            txt.setWordWrap(True)
            txt.setStyleSheet("color: #CBD5E1; font-size: 12px; line-height: 1.3; background: transparent;")

            layout_bloque.addWidget(dot, 0, Qt.AlignTop)
            layout_bloque.addWidget(txt, 1)
            self.layout_scroll.addWidget(bloque)

        self.layout_scroll.addStretch()


class ModalTerminos(_BaseModalAnimado):
    """Modal de términos y condiciones con diseño pulido y tarjetas estructuradas."""

    _nombre_objeto = "tarjetaTerminos"
    _ancho_modal = 640
    _alto_modal = 480

    def __init__(self, parent, origen_pos=None, al_cerrar_callback=None):
        super().__init__(
            parent,
            icono_header="📜",
            titulo_header=tr("TÉRMINOS Y CONDICIONES DE USO"),
            texto_boton=tr("¡ENTENDIDO Y ACEPTADO!"),
            origen_pos=origen_pos,
            al_cerrar_callback=al_cerrar_callback,
        )
        self.layout_scroll.setSpacing(12)

        secciones = (
            (
                "1. Naturaleza del Proyecto y Propiedad Intelectual",
                "🛡️",
                "El Launcher de CHASIS es una herramienta comunitaria e independiente desarrollada por aficionados (fan-made) con el fin de facilitar la gestión y descarga de modificaciones para American Truck Simulator.\n\n"
                "American Truck Simulator y sus respectivos logotipos, marcas y contenidos son propiedad exclusiva de SCS Software. Este software no está afiliado, respaldado ni patrocinado por SCS Software ni por los fabricantes reales de vehículos o accesorios representados en el juego. Todas las marcas registradas pertenecen a sus respectivos dueños.",
            ),
            (
                '2. Exención de Responsabilidad ("TAL CUAL" / AS IS)',
                "⚠️",
                'El software y los mods se proporcionan "tal cual" y "según disponibilidad", sin garantías de ningún tipo respecto a su compatibilidad, rendimiento o estabilidad.\n\n'
                "Los desarrolladores no serán responsables por pérdidas de partidas, corrupción de perfiles de juego, incompatibilidades tras actualizaciones oficiales de ATS o errores de sistema derivados del uso de este software o los mods administrados.\n\n"
                "Recomendación: Se aconseja a los usuarios realizar copias de seguridad periódicas de su carpeta de perfiles (profiles).",
            ),
            (
                "3. Gestión y Modificación de Archivos Locales",
                "📁",
                "Para cumplir sus funciones, el launcher cuenta con la autorización del usuario para leer, escribir, descargar, reemplazar y ajustar atributos en las rutas locales relacionadas con el juego (carpeta mod, perfiles y archivos de configuración como config.cfg).",
            ),
            (
                "4. Donaciones y Apoyo al Proyecto",
                "🤍",
                "Cualquier aportación económica recibida a través de PayPal o códigos QR constituye una donación voluntaria y a fondo perdido destinada al soporte y mantenimiento de la herramienta.\n\n"
                "Dichas donaciones no representan un pago comercial por la compra del juego, de los mods o de licencias de software, ni otorgan derechos comerciales sobre los mismos.",
            ),
            (
                "5. Privacidad y Seguridad",
                "🔒",
                "El Launcher de CHASIS no recopila, no comercializa ni almacena información personal sensible. Las conexiones de red realizadas tienen por único fin la comprobación de versiones, descarga de datos del servidor y descarga segura de contenidos públicos.",
            ),
        )

        for titulo_sec, icono_sec, texto_sec in secciones:
            bloque = QFrame()
            bloque.setStyleSheet("""
                QFrame {
                    background: #1C202B;
                    border: 1px solid #262A37;
                    border-radius: 8px;
                }
                QFrame:hover { border-color: #3B4254; }
            """)
            layout_bloque = QVBoxLayout(bloque)
            layout_bloque.setContentsMargins(14, 12, 14, 12)
            layout_bloque.setSpacing(6)

            fila_tit = QHBoxLayout()
            fila_tit.setSpacing(8)
            lbl_ic = QLabel(icono_sec)
            lbl_ic.setStyleSheet("font-size: 15px; background: transparent;")
            lbl_sub = QLabel(tr(titulo_sec))
            lbl_sub.setStyleSheet("color: #F8FAFC; font-weight: 700; font-size: 12px; background: transparent;")
            fila_tit.addWidget(lbl_ic)
            fila_tit.addWidget(lbl_sub)
            fila_tit.addStretch()

            lbl_txt = QLabel(tr(texto_sec))
            lbl_txt.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.4; background: transparent;")
            lbl_txt.setWordWrap(True)

            layout_bloque.addLayout(fila_tit)
            layout_bloque.addWidget(lbl_txt)
            self.layout_scroll.addWidget(bloque)

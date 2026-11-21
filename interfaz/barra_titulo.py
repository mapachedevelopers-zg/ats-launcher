from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea

from constantes import VERSION_ACTUAL
from i18n import tr


class BarraTituloCustom(QFrame):
    """Barra de título personalizada sin marco de Windows."""

    def __init__(self, parent_window, titulo=None):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self._drag_pos = QPoint()
        self._click_local_y = 0

        self.setObjectName("barraTituloCustom")
        self.setFixedHeight(35)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 0, 0)
        layout.setSpacing(0)

        tit_real = titulo or tr("LAUNCHER DE XTRINK {version}").format(version=VERSION_ACTUAL)
        self.lbl_titulo = QLabel(tit_real)
        self.lbl_titulo.setObjectName("tituloAppCustom")

        self.btn_minimizar = QPushButton("\u2014")
        self.btn_minimizar.setObjectName("btnTituloMin")
        self.btn_minimizar.setFixedSize(45, 35)
        self.btn_minimizar.setCursor(Qt.PointingHandCursor)
        self.btn_minimizar.clicked.connect(self.parent_window.minimizar_con_animacion)

        self.btn_maximizar = QPushButton("\u2610")
        self.btn_maximizar.setObjectName("btnTituloMax")
        self.btn_maximizar.setFixedSize(45, 35)
        self.btn_maximizar.setCursor(Qt.PointingHandCursor)
        self.btn_maximizar.clicked.connect(self.parent_window.alternar_maximizacion)

        self.btn_cerrar = QPushButton("\u2715")
        self.btn_cerrar.setObjectName("btnTituloCerrar")
        self.btn_cerrar.setFixedSize(45, 35)
        self.btn_cerrar.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.parent_window.close)

        layout.addWidget(self.lbl_titulo)
        layout.addStretch()
        layout.addWidget(self.btn_minimizar)
        layout.addWidget(self.btn_maximizar)
        layout.addWidget(self.btn_cerrar)

    def actualizar_icono_max(self):
        """Sincroniza el símbolo del botón según el estado visual real."""
        if self.parent_window.esta_maximizada():
            self.btn_maximizar.setText("\U0001f5d7")
        else:
            self.btn_maximizar.setText("\u2610")

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Doble clic en la barra para maximizar o restaurar."""
        if event.button() == Qt.LeftButton:
            self.parent_window.alternar_maximizacion()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            self._click_local_y = event.position().y()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            global_pos = event.globalPosition().toPoint()
            if self.parent_window.esta_maximizada():
                ancho_max = self.parent_window.width()
                self.parent_window.restaurar_custom()
                ancho_norm = self.parent_window.width()
                proporcion = global_pos.x() / ancho_max if ancho_max > 0 else 0.5
                nuevo_x = max(0, min(int(ancho_norm * proporcion), ancho_norm))
                self._drag_pos = QPoint(nuevo_x, int(self._click_local_y))

            self.parent_window.move(global_pos - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Detecta si se soltó el clic en el borde superior de la pantalla para maximizar."""
        if event.button() == Qt.LeftButton and event.globalPosition().y() <= 3:
            if not self.parent_window.esta_maximizada():
                self.parent_window.maximizar_custom()
        super().mouseReleaseEvent(event)


class ScrollVerticalModal(QScrollArea):
    """QScrollArea adaptado para responder a la rueda del ratón verticalmente."""

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta)

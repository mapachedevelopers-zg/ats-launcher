import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QImage
from PySide6.QtWidgets import (
    QFrame, QLabel, QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from i18n import tr

COLOR_TARJETA = "#2B2B2B"
COLOR_AZUL = "#2980B9"
COLOR_VERDE = "#218C53"
COLOR_AMARILLO = "#CFA90F"
COLOR_ROJO = "#E74C3C"


class SpinnerSerpiente(QWidget):
    def __init__(self):
        super().__init__()
        self.angulo = 0
        self.setFixedSize(112, 112)

    def avanzar(self):
        self.angulo = (self.angulo - 8) % 360
        self.update()

    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)
        pluma = QPen(QColor(COLOR_AZUL), 10, Qt.SolidLine, Qt.RoundCap)
        pintor.setPen(pluma)
        pintor.drawArc(self.rect().adjusted(10, 10, -10, -10),
                       self.angulo * 16, 285 * 16)


class CapaAgua(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.porcentaje = 0
        self.fase = 0.0
        self.radio_burbuja = 0.0
        self.opacidad_burbuja = 0.0
        self.animando_burbuja = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, 180, 245)

    def establecer_progreso(self, porcentaje):
        self.porcentaje = max(0, min(100, porcentaje))
        self.update()

    def avanzar(self):
        self.fase += 0.18
        if self.animando_burbuja:
            self.radio_burbuja += 6.5
            self.opacidad_burbuja = max(0.0, self.opacidad_burbuja - 0.07)
            if self.opacidad_burbuja <= 0:
                self.animando_burbuja = False
        self.update()

    def iniciar_explosion(self):
        self.animando_burbuja = True
        self.radio_burbuja = 10.0
        self.opacidad_burbuja = 0.95
        self.update()

    def paintEvent(self, evento):
        alto = self.height()
        ancho = self.width()
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)

        if self.porcentaje > 0:
            nivel = alto * (1 - self.porcentaje / 100)
            ruta = QPainterPath()
            ruta.moveTo(0, nivel)
            for x in range(0, ancho + 1, 2):
                ola1 = math.sin(x / 22 + self.fase) * 5
                ola2 = math.sin(x / 11 + self.fase * 1.7) * 2
                y = nivel + ola1 + ola2
                ruta.lineTo(x, y)
            ruta.lineTo(ancho, alto)
            ruta.lineTo(0, alto)
            ruta.closeSubpath()

            pintor.fillPath(ruta, QColor(25, 150, 255, 160))
            pluma = QPen(QColor(153, 216, 245, 190), 1.5)
            pintor.setPen(pluma)
            pintor.drawPath(ruta)

        # Burbuja de explosión al completar
        if self.animando_burbuja and self.opacidad_burbuja > 0:
            cx = ancho / 2.0
            cy = alto / 2.0
            alfa = int(255 * self.opacidad_burbuja)

            pintor.setBrush(QColor(56, 189, 248, int(alfa * 0.35)))
            pluma_burbuja = QPen(QColor(224, 242, 254, alfa), 2.5)
            pintor.setPen(pluma_burbuja)
            pintor.drawEllipse(cx - self.radio_burbuja, cy - self.radio_burbuja,
                               self.radio_burbuja * 2, self.radio_burbuja * 2)

            # Anillo exterior
            if self.radio_burbuja > 16:
                r_ext = self.radio_burbuja * 1.25
                alfa_ext = int(alfa * 0.6)
                pluma_ext = QPen(QColor(125, 211, 252, alfa_ext), 1.5)
                pintor.setPen(pluma_ext)
                pintor.setBrush(Qt.NoBrush)
                pintor.drawEllipse(cx - r_ext, cy - r_ext, r_ext * 2, r_ext * 2)


class GaleriaScroll(QScrollArea):
    def wheelEvent(self, evento):
        pasos = evento.angleDelta().y() or evento.angleDelta().x()
        if pasos:
            barra = self.horizontalScrollBar()
            barra.setValue(barra.value() - pasos // 3)
            evento.accept()
        else:
            super().wheelEvent(evento)


class TarjetaMod(QFrame):
    def __init__(self, mod, ruta_archivo, descargar, cancelar, eliminar=None):
        super().__init__()
        self.mod = mod
        self.ruta_archivo = ruta_archivo
        self._descargar = descargar
        self._cancelar = cancelar
        self._eliminar = eliminar
        self.estado_actual = "validando"
        self._descargando = False
        self._iniciar_arrastre = None
        self._arrastrar = None
        self.setFixedSize(220, 385)
        self.setObjectName("tarjetaMod")

        diseño = QVBoxLayout(self)
        diseño.setContentsMargins(10, 10, 10, 10)
        diseño.setSpacing(6)

        titulo = QLabel(mod["nombre"].upper())
        titulo.setObjectName("tituloTarjeta")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setWordWrap(True)
        titulo.setAttribute(Qt.WA_TransparentForMouseEvents)
        diseño.addWidget(titulo, 0)

        self.imagen = QLabel("Cargando imagen…")
        self.imagen.setAlignment(Qt.AlignCenter)
        self.imagen.setFixedSize(180, 245)
        self.imagen.setObjectName("imagenMod")
        self.imagen.setAttribute(Qt.WA_TransparentForMouseEvents)
        diseño.addWidget(self.imagen, 0, Qt.AlignHCenter)

        self.capa_descarga = CapaAgua(self.imagen)
        self.capa_descarga.setObjectName("capaDescarga")
        self.capa_descarga.hide()
        self.texto_progreso = QLabel("", self.capa_descarga)
        self.texto_progreso.setObjectName("textoProgreso")
        self.texto_progreso.setAlignment(Qt.AlignCenter)
        self.texto_progreso.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.texto_progreso.setGeometry(0, 0, 180, 28)
        self.timer_agua = QTimer(self)
        self.timer_agua.timeout.connect(self.capa_descarga.avanzar)

        self.progreso = QProgressBar()
        self.progreso.setRange(0, 100)
        self.progreso.setValue(0)
        self.progreso.setTextVisible(False)
        self.progreso.hide()
        diseño.addWidget(self.progreso)

        self.boton = QPushButton("Validando…")
        self.boton.setFocusPolicy(Qt.NoFocus)
        self.boton.setEnabled(False)
        self.boton.setFixedHeight(28)

        # Un solo botón: descarga o cancela según el estado actual
        self.boton.clicked.connect(self._procesar_click)
        diseño.addWidget(self.boton)

        # Botón para eliminar el mod descargado
        self.boton_eliminar = QPushButton("Eliminar mod")
        self.boton_eliminar.setFocusPolicy(Qt.NoFocus)
        self.boton_eliminar.setCursor(Qt.PointingHandCursor)
        self.boton_eliminar.setFixedHeight(28)
        self.boton_eliminar.clicked.connect(self._procesar_eliminar)
        self._aplicar_estilo_eliminar(False)
        diseño.addWidget(self.boton_eliminar)

    def _aplicar_estilo_eliminar(self, habilitado: bool):
        self.boton_eliminar.setEnabled(habilitado)
        if habilitado:
            self.boton_eliminar.setCursor(Qt.PointingHandCursor)
            self.boton_eliminar.setStyleSheet("""
                QPushButton {
                    background: #8B1D24;
                    color: #FFFFFF;
                    border: 1px solid #991B1B;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: #A8242C;
                    border-color: #EF4444;
                }
            """)
        else:
            self.boton_eliminar.setCursor(Qt.ArrowCursor)
            self.boton_eliminar.setStyleSheet("""
                QPushButton {
                    background: #181A20;
                    color: #475569;
                    border: 1px solid #232731;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }
            """)

    def _procesar_click(self):
        if getattr(self, "_descargando", False) or self.boton.text() == "CANCELAR":
            self.ocultar_progreso()
            self._cancelar(self.mod)
            self.actualizar_estado(self.estado_actual)
        else:
            self._descargar()

    def _procesar_eliminar(self):
        if self._eliminar:
            self._eliminar(self.mod)

    def configurar_arrastre(self, iniciar, mover):
        self._iniciar_arrastre = iniciar
        self._arrastrar = mover

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton and self._iniciar_arrastre:
            self._iniciar_arrastre(evento.globalPosition().toPoint())
        super().mousePressEvent(evento)

    def mouseMoveEvent(self, evento):
        if evento.buttons() & Qt.LeftButton and self._arrastrar:
            self._arrastrar(evento.globalPosition().toPoint())
        super().mouseMoveEvent(evento)

    def poner_imagen(self, imagen, en_color):
        if not en_color:
            imagen = imagen.convertToFormat(QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(imagen).scaled(
            180, 245, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.imagen.setPixmap(pixmap)
        self.imagen.setText("")
        self.capa_descarga.raise_()

    def mostrar_progreso(self, porcentaje):
        altura = math.ceil(245 * max(0, min(100, porcentaje)) / 100)
        nivel = 245 - altura
        self.capa_descarga.establecer_progreso(porcentaje)
        self.texto_progreso.setGeometry(0, max(0, nivel - 14), 180, 28)
        self.texto_progreso.setText(f"{porcentaje}%" if altura >= 28 else "")
        self.capa_descarga.show()
        self.capa_descarga.raise_()

        self._descargando = True

        self.boton.setText("CANCELAR")
        self.boton.setStyleSheet(
            f"background: {COLOR_ROJO}; font-weight: bold;")
        self.boton.setEnabled(True)
        self._aplicar_estilo_eliminar(False)

        if not self.timer_agua.isActive():
            self.timer_agua.start(33)

    def ocultar_progreso(self):
        self._descargando = False
        self.timer_agua.stop()
        self.capa_descarga.hide()
        self.capa_descarga.establecer_progreso(0)

    def animar_explosion_completado(self):
        """Dispara la animación visual de explosión de burbuja al completar la descarga."""
        self.capa_descarga.establecer_progreso(0)
        self.capa_descarga.iniciar_explosion()
        self.capa_descarga.show()
        if not self.timer_agua.isActive():
            self.timer_agua.start(25)

        QTimer.singleShot(600, self.ocultar_progreso)

    def actualizar_textos_idioma(self):
        if hasattr(self, "boton_eliminar"):
            self.boton_eliminar.setText(tr("Eliminar mod"))
        if getattr(self, "_descargando", False):
            self.boton.setText(tr("CANCELAR"))
        else:
            self.actualizar_estado(self.estado_actual)

    def actualizar_estado(self, estado):
        self.estado_actual = estado
        if estado == "actualizado":
            self.boton.setText(tr("Actualizado"))
            self.boton.setStyleSheet(f"background: {COLOR_VERDE};")
            self.boton.setEnabled(False)
            self._aplicar_estilo_eliminar(True)
        elif estado == "actualizar":
            self.boton.setEnabled(True)
            self.boton.setText(tr("Actualizar"))
            self.boton.setStyleSheet(f"background: {COLOR_AMARILLO};")
            self._aplicar_estilo_eliminar(True)
        else:
            self.boton.setEnabled(True)
            self.boton.setText(tr("Descargar"))
            self.boton.setStyleSheet("background: #3E3E3E;")
            self._aplicar_estilo_eliminar(False)

import os
import subprocess
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QToolButton, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from ui_widgets import GaleriaScroll
from download_manager import obtener_ruta_exe_ats, esta_juego_ejecutandose, LOCAL_MODS_DIR
from i18n import tr
from temas import obtener_tema_actual


class PaginaMapas(QWidget):
    _señal_listo_lanzar = Signal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._esperando_lanzar_juego = False
        self._señal_listo_lanzar.connect(self._ejecutar_exe_tras_espera)

        diseño = QVBoxLayout(self)
        diseño.setContentsMargins(20, 18, 20, 20)
        diseño.setSpacing(8)

        # Título de la sección
        self.titulo = QLabel(tr("MAPAS"))
        self.titulo.setObjectName("tituloSeccion")
        diseño.addWidget(self.titulo, 0, Qt.AlignHCenter)

        self.subtitulo = QLabel(tr("Descarga e instala el mapa oficial directamente en tu carpeta de mods."))
        self.subtitulo.setObjectName("subtituloSeccion")
        self.subtitulo.setStyleSheet("color: #94A3B8; font-size: 13px;")
        diseño.addWidget(self.subtitulo, 0, Qt.AlignHCenter)

        # Contenedor de mapas
        self.contenedor_mapas = QWidget()
        layout_mapas = QVBoxLayout(self.contenedor_mapas)
        layout_mapas.setContentsMargins(0, 0, 0, 0)
        layout_mapas.setSpacing(8)

        # Galería horizontal de tarjetas
        self.galeria = QFrame()
        self.galeria.setObjectName("galeria")
        self.galeria.setMinimumHeight(415)
        layout_mapas.addWidget(self.galeria, 1)

        interior = QVBoxLayout(self.galeria)
        interior.setContentsMargins(22, 0, 22, 0)
        self.scroll = GaleriaScroll()
        self.scroll.setWidgetResizable(False)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.contenido = QWidget()
        self.fila = QHBoxLayout(self.contenido)
        self.fila.setContentsMargins(8, 10, 8, 18)
        self.fila.setSpacing(12)
        self.scroll.setWidget(self.contenido)
        interior.addWidget(self.scroll)

        self.anterior = self._crear_flecha("‹")
        self.siguiente = self._crear_flecha("›")
        self.anterior.clicked.connect(lambda: self._mover(-1))
        self.siguiente.clicked.connect(lambda: self._mover(1))

        # Botón para ejecutar el juego
        self.boton_juego = QPushButton("▶  " + tr("Ejecutar juego"))
        self.boton_juego.setObjectName("botonJuego")
        self.boton_juego.setFixedSize(170, 36)
        self.boton_juego.setCursor(Qt.PointingHandCursor)
        self.boton_juego.setStyleSheet("""
            #botonJuego {
                background: #181A20;
                color: #FFFFFF;
                font-weight: 700;
                border: 1px solid #262932;
                border-radius: 6px;
            }
            #botonJuego:hover {
                background: #232731;
                border-color: #3B82F6;
                color: #FFFFFF;
            }
        """)
        self.boton_juego.clicked.connect(self._lanzar_juego)

        # Botón para validar mapa
        self.boton_validar = QPushButton("↻  " + tr("Validar archivos"))
        self.boton_validar.setObjectName("botonValidar")
        self.boton_validar.setFixedSize(170, 36)
        self.boton_validar.clicked.connect(self.main_window.recargar_interfaz)

        # Botón para abrir la carpeta de mods
        self.boton_abrir_carpeta = QPushButton("📁  " + tr("Carpeta de mods"))
        self.boton_abrir_carpeta.setObjectName("botonAbrirCarpeta")
        self.boton_abrir_carpeta.setFixedSize(170, 36)
        self.boton_abrir_carpeta.setCursor(Qt.PointingHandCursor)
        self.boton_abrir_carpeta.clicked.connect(self._abrir_carpeta_mods)

        fila_botones = QHBoxLayout()
        fila_botones.setContentsMargins(0, 12, 0, 0)
        fila_botones.addStretch()
        fila_botones.addWidget(self.boton_juego)
        fila_botones.addSpacing(10)
        fila_botones.addWidget(self.boton_validar)
        fila_botones.addSpacing(10)
        fila_botones.addWidget(self.boton_abrir_carpeta)
        layout_mapas.addLayout(fila_botones)

        diseño.addWidget(self.contenedor_mapas, 1)

        self._posicion_arrastre = QPoint()
        self._valor_arrastre = 0
        self.actualizar_estilo_tema()

    def _crear_flecha(self, texto):
        boton = QToolButton(self.galeria)
        boton.setText(texto)
        boton.setObjectName("flechaGaleria")
        boton.setFixedSize(42, 70)
        boton.raise_()
        return boton

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        QTimer.singleShot(10, self._colocar_flechas)

    def showEvent(self, evento):
        super().showEvent(evento)
        QTimer.singleShot(10, self._colocar_flechas)

    def _colocar_flechas(self):
        tarjeta = self.fila.itemAt(0).widget() if self.fila.count() else None
        if tarjeta and tarjeta.height() < 50:
            QTimer.singleShot(10, self._colocar_flechas)
            return

        if tarjeta:
            arriba = tarjeta.mapTo(self.galeria, QPoint(0, 0)).y()
            y = arriba + (tarjeta.height() - self.anterior.height()) // 2
        else:
            y = 150

        self.anterior.move(0, max(0, y))
        self.siguiente.move(self.galeria.width() - self.siguiente.width(), max(0, y))

    def _mover(self, direccion):
        barra = self.scroll.horizontalScrollBar()
        barra.setValue(barra.value() + direccion * 232)

    def agregar_tarjeta(self, tarjeta):
        tarjeta.configurar_arrastre(self.iniciar_arrastre, self.arrastrar)
        self.fila.addWidget(tarjeta)
        cantidad = self.fila.count()
        self.contenido.setFixedSize(
            16 + cantidad * 220 + max(0, cantidad - 1) * 12, 405)
        QTimer.singleShot(0, self._colocar_flechas)

    def iniciar_arrastre(self, posicion):
        self._posicion_arrastre = posicion
        self._valor_arrastre = self.scroll.horizontalScrollBar().value()

    def arrastrar(self, posicion):
        diferencia = posicion.x() - self._posicion_arrastre.x()
        self.scroll.horizontalScrollBar().setValue(self._valor_arrastre - diferencia)

    def _abrir_carpeta_mods(self):
        try:
            if os.path.exists(LOCAL_MODS_DIR):
                os.startfile(LOCAL_MODS_DIR)
            else:
                os.makedirs(LOCAL_MODS_DIR, exist_ok=True)
                os.startfile(LOCAL_MODS_DIR)
        except Exception as e:
            QMessageBox.warning(self, tr("Carpeta de mods"), f"{tr('No se pudo abrir la carpeta')}: {e}")

    def _lanzar_juego(self):
        if self._esperando_lanzar_juego:
            return

        if esta_juego_ejecutandose():
            QMessageBox.warning(self, tr("Juego en ejecución"),
                                tr("American Truck Simulator ya se encuentra abierto."))
            return

        ruta_exe = obtener_ruta_exe_ats()

        if not ruta_exe or not os.path.exists(ruta_exe):
            QMessageBox.critical(
                self,
                tr("Error al ejecutar"),
                tr("No se encontró el ejecutable 'amtrucks.exe'.\n\nPor favor, ve a Configuración y selecciona la ubicación del juego manualmente.")
            )
            return

        perfiles_page = getattr(self.main_window, "pagina_perfiles", None)
        if perfiles_page and getattr(perfiles_page, "hay_operaciones_pendientes", None):
            if perfiles_page.hay_operaciones_pendientes():
                self._esperando_lanzar_juego = True
                self.boton_juego.setEnabled(False)
                self.boton_juego.setText("⏳  " + tr("Esperando perfil..."))

                def _esperar():
                    perfiles_page.esperar_operaciones(timeout=10.0)
                    self._señal_listo_lanzar.emit(ruta_exe)

                threading.Thread(target=_esperar, daemon=True).start()
                return

        self._ejecutar_exe(ruta_exe)

    def _ejecutar_exe_tras_espera(self, ruta_exe):
        self._esperando_lanzar_juego = False
        self.boton_juego.setEnabled(True)
        self.boton_juego.setText("▶  " + tr("Ejecutar juego"))
        self._ejecutar_exe(ruta_exe)

    def _ejecutar_exe(self, ruta_exe):
        try:
            directorio_juego = os.path.dirname(ruta_exe)
            subprocess.Popen([ruta_exe], cwd=directorio_juego)
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("Error"),
                f"{tr('No se pudo iniciar el juego:')}\n{str(e)}"
            )

    def actualizar_estilo_tema(self):
        tema = obtener_tema_actual()
        acento = tema.get("acento", "#3B82F6")
        fondo_boton = tema.get("fondo_tarjeta", "#181A20")
        borde_tarjeta = tema.get("borde_tarjeta", "#262932")
        fondo_hover = tema.get("fondo_hover", "#232731")

        if hasattr(self, "boton_juego"):
            self.boton_juego.setStyleSheet(f"""
                #botonJuego {{
                    background: {fondo_boton};
                    color: #FFFFFF;
                    font-weight: 700;
                    border: 1px solid {borde_tarjeta};
                    border-radius: 6px;
                }}
                #botonJuego:hover {{
                    background: {fondo_hover};
                    border-color: {acento};
                    color: #FFFFFF;
                }}
            """)

        if hasattr(self, "boton_validar"):
            self.boton_validar.setStyleSheet(f"""
                #botonValidar {{
                    background: {fondo_boton};
                    color: #FFFFFF;
                    font-weight: 700;
                    border: 1px solid {borde_tarjeta};
                    border-radius: 6px;
                }}
                #botonValidar:hover {{
                    background: {fondo_hover};
                    border-color: {acento};
                    color: #FFFFFF;
                }}
            """)

        if hasattr(self, "boton_abrir_carpeta"):
            self.boton_abrir_carpeta.setStyleSheet(f"""
                #botonAbrirCarpeta {{
                    background: {fondo_boton};
                    color: #FFFFFF;
                    font-weight: 700;
                    border: 1px solid {borde_tarjeta};
                    border-radius: 6px;
                }}
                #botonAbrirCarpeta:hover {{
                    background: {fondo_hover};
                    border-color: {acento};
                    color: #FFFFFF;
                }}
            """)

    def actualizar_textos_idioma(self):
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("MAPAS"))
        if hasattr(self, "subtitulo"):
            self.subtitulo.setText(tr("Descarga e instala el mapa oficial directamente en tu carpeta de mods."))
        if hasattr(self, "boton_juego"):
            if self._esperando_lanzar_juego:
                self.boton_juego.setText("⏳  " + tr("Esperando perfil..."))
            else:
                self.boton_juego.setText("▶  " + tr("Ejecutar juego"))
        if hasattr(self, "boton_validar"):
            self.boton_validar.setText("↻  " + tr("Validar archivos"))
        if hasattr(self, "boton_abrir_carpeta"):
            self.boton_abrir_carpeta.setText("📁  " + tr("Carpeta de mods"))

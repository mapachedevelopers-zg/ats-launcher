import os
import subprocess
import threading

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QToolButton, QMessageBox
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from ui_widgets import SpinnerSerpiente, GaleriaScroll
from download_manager import obtener_ruta_exe_ats, esta_juego_ejecutandose
from i18n import tr


class PaginaMods(QWidget):
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
        self.titulo = QLabel(tr("MIS MODS"))
        self.titulo.setObjectName("tituloSeccion")
        diseño.addWidget(self.titulo, 0, Qt.AlignHCenter)

        # Botón de aviso de nueva versión del launcher (oculto por defecto)
        self.boton_actualizar_launcher = QPushButton(
            "🚀 ¡NUEVA VERSIÓN DEL LAUNCHER DISPONIBLE! CLICK AQUÍ PARA ACTUALIZAR")
        self.boton_actualizar_launcher.setObjectName("botonActualizarLauncher")
        self.boton_actualizar_launcher.setCursor(Qt.PointingHandCursor)
        self.boton_actualizar_launcher.hide()
        diseño.addWidget(self.boton_actualizar_launcher)

        # Capa de carga (spinner + texto)
        self.capa_carga = QWidget()
        layout_carga = QVBoxLayout(self.capa_carga)
        layout_carga.setAlignment(Qt.AlignCenter)
        self.spinner = SpinnerSerpiente()
        self.spinner.setObjectName("spinner")
        self.texto_carga = QLabel("VALIDANDO ARCHIVOS")
        self.texto_carga.setObjectName("textoCarga")
        self.texto_carga.setAlignment(Qt.AlignCenter)
        layout_carga.addWidget(self.spinner, 0, Qt.AlignHCenter)
        layout_carga.addSpacing(12)
        layout_carga.addWidget(self.texto_carga, 0, Qt.AlignHCenter)
        diseño.addWidget(self.capa_carga, 1)

        # Contenedor de los mods
        self.contenedor_mods = QWidget()
        layout_mods = QVBoxLayout(self.contenedor_mods)
        layout_mods.setContentsMargins(0, 0, 0, 0)
        layout_mods.setSpacing(8)

        # Galería horizontal de tarjetas
        self.galeria = QFrame()
        self.galeria.setObjectName("galeria")
        self.galeria.setMinimumHeight(415)
        layout_mods.addWidget(self.galeria, 1)

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

        # Botón para validar archivos
        self.boton_validar = QPushButton("↻  " + tr("Validar archivos"))
        self.boton_validar.setObjectName("botonValidar")
        self.boton_validar.setFixedSize(170, 36)
        self.boton_validar.clicked.connect(self.main_window.recargar_interfaz)

        # Botón para descargar todos los mods
        self.boton_descargar_todos = QPushButton("⬇  " + tr("Descargar todos los mods"))
        self.boton_descargar_todos.setObjectName("botonDescargarTodos")
        self.boton_descargar_todos.setFixedSize(195, 36)
        self.boton_descargar_todos.setCursor(Qt.PointingHandCursor)
        self.boton_descargar_todos.setStyleSheet("""
            #botonDescargarTodos {
                background: #181A20;
                border: 1px solid #262932;
                color: #E2E8F0;
                font-weight: 600;
                border-radius: 6px;
            }
            #botonDescargarTodos:hover {
                background: #232731;
                border-color: #3B82F6;
                color: #93C5FD;
            }
            #botonDescargarTodos[estado="cancelar"] {
                background: #24161A;
                border: 1px solid #991B1B;
                color: #FCA5A5;
                font-weight: 700;
            }
            #botonDescargarTodos[estado="cancelar"]:hover {
                background: #3B181B;
                border-color: #EF4444;
                color: #FFFFFF;
            }
            #botonDescargarTodos[estado="actualizado"] {
                background: #181A20;
                border: 1px solid #262932;
                color: #34D399;
                font-weight: 600;
            }
            #botonDescargarTodos[estado="actualizado"]:disabled {
                background: #181A20;
                border: 1px solid #262932;
                color: #34D399;
                font-weight: 600;
            }
            #botonDescargarTodos:disabled {
                background: #181A20;
                border: 1px solid #262932;
                color: #94A3B8;
                font-weight: 600;
            }
        """)
        if hasattr(self.main_window, "action_descargar_o_cancelar_todos"):
            self.boton_descargar_todos.clicked.connect(self.main_window.action_descargar_o_cancelar_todos)
        else:
            self.boton_descargar_todos.clicked.connect(self._descargar_todos_fallback)

        # Botón para eliminar todos los mods
        self.boton_eliminar_todos = QPushButton("🗑  " + tr("Eliminar todos los mods"))
        self.boton_eliminar_todos.setObjectName("botonEliminarTodos")
        self.boton_eliminar_todos.setFixedSize(185, 36)
        self.boton_eliminar_todos.setCursor(Qt.PointingHandCursor)
        self.boton_eliminar_todos.setStyleSheet("""
            #botonEliminarTodos {
                background: #181A20;
                border: 1px solid #262932;
                color: #E2E8F0;
                font-weight: 600;
                border-radius: 6px;
            }
            #botonEliminarTodos:hover {
                background: #232731;
                border-color: #EF4444;
                color: #FCA5A5;
            }
        """)
        if hasattr(self.main_window, "eliminar_todos_los_mods"):
            self.boton_eliminar_todos.clicked.connect(self.main_window.eliminar_todos_los_mods)
        else:
            self.boton_eliminar_todos.clicked.connect(self._eliminar_todos_los_mods_fallback)

        # Botón de novedades del launcher
        self.btn_novedades = QPushButton("❕")
        self.btn_novedades.setObjectName("btnNovedades")
        self.btn_novedades.setFixedSize(36, 36)
        self.btn_novedades.setCursor(Qt.PointingHandCursor)
        self.btn_novedades.setToolTip("Ver Novedades del Launcher")
        self.btn_novedades.setProperty("animando", False)
        if self.main_window:
            self.btn_novedades.clicked.connect(
                self.main_window.abrir_modal_novedades)

        self.actualizar_estilo_tema()

        fila_validar = QHBoxLayout()
        fila_validar.setContentsMargins(0, 12, 0, 0)
        fila_validar.addStretch()
        fila_validar.addWidget(self.boton_juego)
        fila_validar.addSpacing(10)
        fila_validar.addWidget(self.boton_validar)
        fila_validar.addSpacing(10)
        fila_validar.addWidget(self.boton_descargar_todos)
        fila_validar.addSpacing(10)
        fila_validar.addWidget(self.boton_eliminar_todos)
        fila_validar.addSpacing(10)
        fila_validar.addWidget(self.btn_novedades)
        layout_mods.addLayout(fila_validar)

        diseño.addWidget(self.contenedor_mods, 1)
        self.contenedor_mods.hide()

        self._posicion_arrastre = QPoint()
        self._valor_arrastre = 0

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
        self.siguiente.move(self.galeria.width() -
                            self.siguiente.width(), max(0, y))

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

    def _descargar_todos_fallback(self):
        if hasattr(self.main_window, "action_descargar_o_cancelar_todos"):
            self.main_window.action_descargar_o_cancelar_todos()

    def _eliminar_todos_los_mods_fallback(self):
        if hasattr(self.main_window, "eliminar_todos_los_mods"):
            self.main_window.eliminar_todos_los_mods()

    def iniciar_arrastre(self, posicion):
        self._posicion_arrastre = posicion
        self._valor_arrastre = self.scroll.horizontalScrollBar().value()

    def arrastrar(self, posicion):
        diferencia = posicion.x() - self._posicion_arrastre.x()
        self.scroll.horizontalScrollBar().setValue(self._valor_arrastre - diferencia)

    def _lanzar_juego(self):
        if self._esperando_lanzar_juego:
            return

        # Evitar abrir el juego dos veces
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

        # Si la página de perfiles tiene operaciones pendientes, esperar a que terminen
        perfiles_page = getattr(self.main_window, "pagina_perfiles", None)
        if perfiles_page is not None:
            if getattr(perfiles_page, "_skills_dirty", False) and hasattr(perfiles_page, "_guardar_skills_inmediato"):
                perfiles_page._guardar_skills_inmediato()
            if hasattr(perfiles_page, "hay_operaciones_pendientes") and perfiles_page.hay_operaciones_pendientes():
                self._esperando_lanzar_juego = True
                if hasattr(self, "boton_juego"):
                    self.boton_juego.setEnabled(False)
                    self.boton_juego.setText("⏳  " + tr("Esperando perfil..."))

                def _esperar_y_arrancar():
                    try:
                        perfiles_page.esperar_operaciones_pendientes(timeout_max=30.0)
                    finally:
                        try:
                            self._señal_listo_lanzar.emit(ruta_exe)
                        except RuntimeError:
                            pass

                threading.Thread(target=_esperar_y_arrancar, daemon=True).start()
                return

        self._ejecutar_exe_tras_espera(ruta_exe)

    def _ejecutar_exe_tras_espera(self, ruta_exe: str):
        self._esperando_lanzar_juego = False
        if hasattr(self, "boton_juego"):
            self.boton_juego.setEnabled(True)
            self.boton_juego.setText("▶  " + tr("Ejecutar juego"))

        if esta_juego_ejecutandose():
            QMessageBox.warning(self, tr("Juego en ejecución"),
                                tr("American Truck Simulator ya se encuentra abierto."))
            return

        if not ruta_exe or not os.path.exists(ruta_exe):
            QMessageBox.critical(
                self,
                tr("Error al ejecutar"),
                tr("No se encontró el ejecutable 'amtrucks.exe'.\n\nPor favor, ve a Configuración y selecciona la ubicación del juego manualmente.")
            )
            return

        # Lanzar el juego y minimizar el launcher
        try:
            subprocess.Popen([ruta_exe], cwd=os.path.dirname(ruta_exe))
            if self.main_window is not None and hasattr(self.main_window, "showMinimized"):
                self.main_window.showMinimized()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo iniciar el juego: {e}")

    def animar_boton_novedades(self):
        """Efecto de parpadeo suave alternando propiedades sin romper el estilo :hover."""
        self._conteo_anim = 0

        def _paso_brillo():
            self._conteo_anim += 1
            estado_anim = (self._conteo_anim % 2 == 1)
            self.btn_novedades.setProperty("animando", estado_anim)

            # Forzar a Qt a re-evaluar la hoja de estilos
            self.btn_novedades.style().unpolish(self.btn_novedades)
            self.btn_novedades.style().polish(self.btn_novedades)

            if self._conteo_anim >= 6:
                self.btn_novedades.setProperty("animando", False)
                self.btn_novedades.style().unpolish(self.btn_novedades)
                self.btn_novedades.style().polish(self.btn_novedades)
                self._timer_brillo.stop()

        self._timer_brillo = QTimer(self)
        self._timer_brillo.setInterval(500)
        self._timer_brillo.timeout.connect(_paso_brillo)
        self._timer_brillo.start()

    def actualizar_estilo_tema(self):
        """Actualiza los botones de la página que llevan el color de acento del tema activo."""
        from temas import obtener_tema_actual
        tema = obtener_tema_actual()
        acento = tema.get("acento", "#E5A93C")
        hover = tema.get("hover", "#F1C40F")
        borde_osc = tema.get("borde_oscuro", "#C58922")
        fondo_suave = tema.get("fondo_suave", "#2D2517")
        texto_claro = tema.get("texto_claro", "#FFC86B")

        if hasattr(self, "boton_actualizar_launcher"):
            self.boton_actualizar_launcher.setStyleSheet(f"""
                #botonActualizarLauncher {{ 
                    background: {acento}; 
                    color: #121316; 
                    font-weight: 900; 
                    font-size: 13px; 
                    padding: 10px; 
                    border-radius: 6px; 
                    border: 2px solid {borde_osc}; 
                }}
                #botonActualizarLauncher:hover {{ 
                    background: {hover}; 
                    border-color: {acento};
                }}
            """)

        if hasattr(self, "btn_novedades"):
            self.btn_novedades.setStyleSheet(f"""
                #btnNovedades {{
                    background-color: #1A1D24;
                    color: #FFFFFF;
                    font-size: 14px;
                    font-weight: bold;
                    border: 1px solid #2A2E39;
                    border-radius: 6px;
                }}
                #btnNovedades[animando="true"] {{
                    background-color: {fondo_suave};
                    color: {texto_claro};
                    border: 1px solid {acento};
                }}
                #btnNovedades:hover {{
                    background-color: #1A1D24 !important;
                    border: 1px solid {acento} !important;
                    color: {acento} !important;
                }}
            """)

        fondo_boton = tema.get("fondo_boton_menu", "#181A20")
        fondo_hover = tema.get("fondo_boton_hover", "#232731")
        borde_tarjeta = tema.get("borde_tarjeta", "#262932")

        if hasattr(self, "boton_descargar_todos"):
            self.boton_descargar_todos.setStyleSheet(f"""
                #botonDescargarTodos {{
                    background: {fondo_boton};
                    border: 1px solid {borde_tarjeta};
                    color: #E2E8F0;
                    font-weight: 600;
                    border-radius: 6px;
                }}
                #botonDescargarTodos:hover {{
                    background: {fondo_hover};
                    border-color: {acento};
                    color: #FFFFFF;
                }}
                #botonDescargarTodos[estado="cancelar"] {{
                    background: #24161A;
                    border: 1px solid #991B1B;
                    color: #FCA5A5;
                    font-weight: 700;
                }}
                #botonDescargarTodos[estado="cancelar"]:hover {{
                    background: #3B181B;
                    border-color: #EF4444;
                    color: #FFFFFF;
                }}
                #botonDescargarTodos[estado="actualizado"] {{
                    background: {fondo_boton};
                    border: 1px solid {borde_tarjeta};
                    color: #34D399;
                    font-weight: 600;
                }}
                #botonDescargarTodos[estado="actualizado"]:disabled {{
                    background: {fondo_boton};
                    border: 1px solid {borde_tarjeta};
                    color: #34D399;
                    font-weight: 600;
                }}
                #botonDescargarTodos:disabled {{
                    background: {fondo_boton};
                    border: 1px solid {borde_tarjeta};
                    color: #94A3B8;
                    font-weight: 600;
                }}
            """)

        if hasattr(self, "boton_eliminar_todos"):
            self.boton_eliminar_todos.setStyleSheet(f"""
                #botonEliminarTodos {{
                    background: {fondo_boton};
                    border: 1px solid {borde_tarjeta};
                    color: #E2E8F0;
                    font-weight: 600;
                    border-radius: 6px;
                }}
                #botonEliminarTodos:hover {{
                    background: {fondo_hover};
                    border-color: #EF4444;
                    color: #FCA5A5;
                }}
            """)

    def actualizar_textos_idioma(self):
        """Actualiza los textos visibles de la sección de mods según el idioma activo."""
        from i18n import tr
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("MIS MODS"))
        if hasattr(self, "boton_juego"):
            if self._esperando_lanzar_juego:
                self.boton_juego.setText("⏳  " + tr("Esperando perfil..."))
            else:
                self.boton_juego.setText("▶  " + tr("Ejecutar juego"))
        if hasattr(self, "boton_validar"):
            self.boton_validar.setText("↻  " + tr("Validar archivos"))
        if hasattr(self, "boton_eliminar_todos"):
            self.boton_eliminar_todos.setText("🗑  " + tr("Eliminar todos los mods"))
        if hasattr(self, "btn_novedades"):
            self.btn_novedades.setToolTip(tr("Ver Novedades del Launcher"))
        if hasattr(self, "texto_carga"):
            self.texto_carga.setText(tr("VALIDANDO ARCHIVOS"))
        if hasattr(self.main_window, "_actualizar_estado_boton_todos"):
            self.main_window._actualizar_estado_boton_todos()

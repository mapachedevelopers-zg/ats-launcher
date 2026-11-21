import os
import time
import threading
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from ctypes import wintypes

from PySide6.QtCore import QObject, Qt, QTimer, Signal, QSize, QPoint, QPropertyAnimation, QEasingCurve, QEvent, QRect
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget, QGraphicsBlurEffect,
)

from estilos import obtener_hoja_estilos
from temas import guardar_tema_actual, obtener_ruta_recurso
from updater import comprobar_actualizacion_launcher, aplicar_actualizacion_y_reiniciar
from constantes import VERSION_ACTUAL, RECURSOS_OFUSCADOS
from i18n import tr, registrar_observador_idioma, desregistrar_observador_idioma
import download_manager
from download_manager import iniciar_descarga_hilo, obtener_datos_servidor, obtener_ruta_ats
from ui_widgets import TarjetaMod
from utils import descargar_imagen

from .animacion_corazon import generar_iconos_corazon
from .barra_titulo import BarraTituloCustom
from .modales import ModalNovedades, ModalTerminos

from vistas.pagina_mods import PaginaMods
from vistas.pagina_orden import PaginaOrden
from vistas.perfiles import PaginaPerfiles
from vistas.pagina_donaciones import PaginaDonaciones
from vistas.pagina_herramientas import PaginaHerramientas
from vistas.pagina_redes import PaginaRedes
from vistas.pagina_configuracion import PaginaConfiguracion
from vistas.pagina_plugins import PaginaPlugins


class SeñalesUI(QObject):
    imagen_mod = Signal(str, object, object)
    estado_mod = Signal(object, str)
    recurso = Signal(str, object)
    progreso = Signal(object, int)
    progreso_actualizador = Signal(int)
    descarga_finalizada = Signal(object, bool)
    validacion_terminada = Signal()
    datos_servidor = Signal(object)
    progreso_validacion = Signal(int)


class LauncherUI(QMainWindow):
    def __init__(self, datos_servidor=None):
        super().__init__(flags=Qt.FramelessWindowHint)

        self.datos_servidor = datos_servidor
        self.tarjetas = {}
        self.imagenes_mod = {}
        self.en_actualizacion_launcher = False
        self.eventos_cancelacion = {}

        self._margin = 8
        self._geometria_normal = QRect(100, 100, 1200, 700)
        self._is_maximized_state = False

        self.señales = SeñalesUI()
        self.señales.imagen_mod.connect(self._recibir_imagen_mod)
        self.señales.estado_mod.connect(self._recibir_estado)
        self.señales.recurso.connect(self._recibir_recurso)
        self.señales.progreso.connect(self._actualizar_progreso)
        self.señales.progreso_actualizador.connect(
            self._actualizar_progreso_actualizacion)
        self.señales.descarga_finalizada.connect(self._terminar_descarga)
        self.señales.validacion_terminada.connect(self._ocultar_carga)
        self.señales.datos_servidor.connect(self._recibir_datos_servidor)
        self.señales.progreso_validacion.connect(
            self._actualizar_texto_validacion)

        # Animación suave del porcentaje de validación
        self._porcentaje_real_val = 0
        self._porcentaje_visual_val = 0
        self._timer_suavizado_val = QTimer(self)
        # ~60 FPS
        self._timer_suavizado_val.setInterval(15)
        self._timer_suavizado_val.timeout.connect(
            self._paso_animacion_porcentaje)

        self.setWindowTitle(tr("LAUNCHER DE CHASIS {version}").format(version=VERSION_ACTUAL))
        self.resize(1200, 700)
        self.setMinimumSize(900, 600)

        self._indice_spinner = 0
        self._timer_carga = QTimer(self)
        self._timer_carga.timeout.connect(self._animar_carga)

        self._crear_interfaz()
        self._mostrar_carga()
        self._habilitar_minimizado_barra_tareas()

        if self.datos_servidor:
            self._iniciar_con_datos()
        else:
            self.pagina_mods.texto_carga.setText("CARGANDO DATOS DEL LAUNCHER")
            threading.Thread(target=self._obtener_datos_servidor,
                             daemon=True).start()

    def _habilitar_minimizado_barra_tareas(self):
        """Habilita la capacidad nativa de Windows para minimizar/restaurar al pulsar el icono de la barra de tareas."""
        if os.name == "nt":
            hwnd = int(self.winId())
            GWL_STYLE = -16
            WS_MINIMIZEBOX = 0x00020000
            WS_CAPTION = 0x00C00000

            # Añadimos los estilos sin perder el marco personalizado
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style |= WS_MINIMIZEBOX | WS_CAPTION
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

    def esta_maximizada(self):
        """Retorna el estado real de la ventana confiando en nuestro flag."""
        return self._is_maximized_state or self.isMaximized()

    def alternar_maximizacion(self):
        if self.esta_maximizada():
            self.restaurar_custom()
        else:
            self.maximizar_custom()

    def maximizar_custom(self):
        """Guarda la geometría pequeña antes de maximizar para protegerla."""
        if not self.esta_maximizada():
            self._geometria_normal = self.geometry()

        self._is_maximized_state = True
        self.showMaximized()
        self.barra_titulo.actualizar_icono_max()

    def restaurar_custom(self):
        """Fuerza la ventana a adoptar sus medidas pequeñas guardadas."""
        self._is_maximized_state = False
        self.showNormal()
        if self._geometria_normal and not self._geometria_normal.isEmpty():
            self.setGeometry(self._geometria_normal)
        self.barra_titulo.actualizar_icono_max()

    def changeEvent(self, event):
        """Intercepta los cambios de estado del OS para corregir fallos geométricos."""
        if event.type() == QEvent.WindowStateChange:
            estado = self.windowState()

            if estado == Qt.WindowNoState and self._is_maximized_state:
                QTimer.singleShot(0, self.showMaximized)
            elif estado & Qt.WindowMaximized:
                self._is_maximized_state = True

            if hasattr(self, "barra_titulo"):
                self.barra_titulo.actualizar_icono_max()

        super().changeEvent(event)

    def minimizar_con_animacion(self):
        """Aplica un efecto de desvanecimiento (fade-out) suave al minimizar."""
        self.anim_opacidad = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacidad.setDuration(220)
        self.anim_opacidad.setStartValue(1.0)
        self.anim_opacidad.setEndValue(0.0)
        self.anim_opacidad.setEasingCurve(QEasingCurve.OutQuad)

        def _al_finalizar():
            self.showMinimized()
            self.setWindowOpacity(1.0)

        self.anim_opacidad.finished.connect(_al_finalizar)
        self.anim_opacidad.start()

    def nativeEvent(self, eventType, message):
        """Permite estirar/reducir la ventana desde los bordes solo si NO está maximizada."""
        if eventType == b"windows_generic_MSG" and os.name == "nt":
            msg = wintypes.MSG.from_address(message.__int__())
            WM_NCHITTEST = 0x0084
            if msg.message == WM_NCHITTEST:
                x_phys = ctypes.c_short(msg.lParam & 0xFFFF).value
                y_phys = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

                # Corrección de escala DPI
                dpi_ratio = self.devicePixelRatio()
                pos = self.mapFromGlobal(
                    QPoint(int(x_phys / dpi_ratio), int(y_phys / dpi_ratio)))

                w, h = self.width(), self.height()
                m = self._margin

                left = pos.x() < m
                right = pos.x() > w - m
                top = pos.y() < m
                bottom = pos.y() > h - m

                HTLEFT, HTRIGHT, HTTOP, HTBOTTOM = 10, 11, 12, 15
                HTTOPLEFT, HTTOPRIGHT, HTBOTTOMLEFT, HTBOTTOMRIGHT = 13, 14, 16, 17

                if not self.esta_maximizada():
                    if top and left:
                        return True, HTTOPLEFT
                    if top and right:
                        return True, HTTOPRIGHT
                    if bottom and left:
                        return True, HTBOTTOMLEFT
                    if bottom and right:
                        return True, HTBOTTOMRIGHT
                    if left:
                        return True, HTLEFT
                    if right:
                        return True, HTRIGHT
                    if top:
                        return True, HTTOP
                    if bottom:
                        return True, HTBOTTOM

        return super().nativeEvent(eventType, message)

    def _obtener_datos_servidor(self):
        self.señales.datos_servidor.emit(obtener_datos_servidor())

    def _recibir_datos_servidor(self, datos):
        if not datos:
            self.pagina_mods.texto_carga.setText(
                "NO SE PUDO CONECTAR AL SERVIDOR")
            return
        self.datos_servidor = datos

        # Actualizar el título con la versión
        tit_launcher = tr("LAUNCHER DE CHASIS {version}").format(version=VERSION_ACTUAL)
        self.setWindowTitle(tit_launcher)
        if hasattr(self, "barra_titulo") and hasattr(self.barra_titulo, "lbl_titulo"):
            self.barra_titulo.lbl_titulo.setText(tit_launcher)

        self._iniciar_con_datos()

    def _iniciar_con_datos(self):
        self._crear_tarjetas_visuales()
        self._cargar_recursos()
        self._indice_spinner = 0

        hay_actualizacion, url_descarga = comprobar_actualizacion_launcher(
            self.datos_servidor)
        if hay_actualizacion:
            self.pagina_mods.boton_actualizar_launcher.show()
            self.pagina_mods.boton_actualizar_launcher.clicked.connect(
                lambda: self.ejecutar_actualizacion_launcher(url_descarga))

        self._iniciar_validacion(forzar_completo=False)

        QTimer.singleShot(30000, self._iniciar_validacion_silenciosa_fondo)

    def abrir_modal_novedades(self):
        """Obtiene la versión directamente del JSON de GitHub para el modal."""
        texto_novedades = "No hay novedades registradas en este momento."
        version_servidor = VERSION_ACTUAL

        if self.datos_servidor:
            texto_novedades = self.datos_servidor.get(
                "novedades", texto_novedades)
            version_servidor = str(self.datos_servidor.get(
                "launcher_version", VERSION_ACTUAL))

        # Desenfoque del fondo
        self.efe_blur = QGraphicsBlurEffect(self)
        self.efe_blur.setBlurRadius(15)
        self.centralWidget().setGraphicsEffect(self.efe_blur)

        # Posición de origen de la animación
        pos_boton = (
            self.pagina_mods.btn_novedades.mapTo(self, QPoint(0, 0))
            if hasattr(self.pagina_mods, "btn_novedades")
            else QPoint(self.width() - 80, self.height() - 60)
        )

        def al_cerrar():
            self.centralWidget().setGraphicsEffect(None)

        self.modal_novedades = ModalNovedades(
            self, version_servidor, texto_novedades, pos_boton, al_cerrar)
        self.modal_novedades.show()
        self.modal_novedades.raise_()

    def abrir_modal_terminos(self, origen_pos=None):
        """Abre la ventana modal interactiva con los Términos y Condiciones del Launcher."""
        pos_origen = origen_pos or QPoint(self.width() // 2, self.height() // 2)

        self.efe_blur = QGraphicsBlurEffect(self)
        self.efe_blur.setBlurRadius(15)
        self.centralWidget().setGraphicsEffect(self.efe_blur)

        def al_cerrar():
            self.centralWidget().setGraphicsEffect(None)

        self.modal_terminos = ModalTerminos(self, pos_origen, al_cerrar)
        self.modal_terminos.show()
        self.modal_terminos.raise_()

    def ejecutar_actualizacion_launcher(self, url_descarga):
        self.en_actualizacion_launcher = True
        self._mostrar_carga()
        self.pagina_mods.texto_carga.setText("DESCARGANDO ACTUALIZACIÓN: 0%")

        def hilo_actualizacion():
            def en_progreso(porcentaje):
                self.señales.progreso_actualizador.emit(porcentaje)

            aplicar_actualizacion_y_reiniciar(url_descarga, en_progreso)

        threading.Thread(target=hilo_actualizacion, daemon=True).start()

    def _actualizar_progreso_actualizacion(self, porcentaje):
        if porcentaje == 100:
            self.pagina_mods.texto_carga.setText(
                "¡INSTALACIÓN COMPLETADA! CERRANDO...")
            self.pagina_mods.texto_carga.setStyleSheet(
                "color: #2ECC71; font-weight: bold;")

            # Cierre limpio del proceso para que el actualizador pueda reemplazar el exe
            def _terminar_proceso():
                try:
                    QApplication.quit()
                except Exception:
                    pass
                os._exit(0)

            QTimer.singleShot(800, _terminar_proceso)
        else:
            self.pagina_mods.texto_carga.setText(
                f"DESCARGANDO ACTUALIZACIÓN DEL LAUNCHER: {porcentaje}%")

    def _crear_interfaz(self):
        raiz = QWidget()
        self.setCentralWidget(raiz)

        layout_principal = QVBoxLayout(raiz)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        tit_launcher = tr("LAUNCHER DE CHASIS {version}").format(version=VERSION_ACTUAL)
        self.barra_titulo = BarraTituloCustom(
            self, titulo=tit_launcher)
        layout_principal.addWidget(self.barra_titulo)

        contenedor_cuerpo = QWidget()
        diseño = QHBoxLayout(contenedor_cuerpo)
        diseño.setContentsMargins(0, 0, 0, 0)
        diseño.setSpacing(0)

        lateral = QFrame()
        lateral.setObjectName("barraLateral")
        lateral.setFixedWidth(220)
        menu = QVBoxLayout(lateral)
        menu.setContentsMargins(20, 20, 20, 25)
        menu.setSpacing(14)

        self.logo = QLabel("CHASIS")
        self.logo.setObjectName("logoLabel")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setFixedSize(160, 145)
        # CAMBIO: mostrar el logo local de inmediato (luego se sustituye por el remoto si existe)
        _ruta_logo_local = obtener_ruta_recurso("logo_chasis.png")
        if os.path.exists(_ruta_logo_local):
            _pix_logo = QPixmap(_ruta_logo_local).scaled(
                130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(_pix_logo)
        menu.addWidget(self.logo)
        menu.addSpacing(20)

        self.vistas = QStackedWidget()

        self.pagina_mods = PaginaMods(main_window=self)
        self.pagina_orden = PaginaOrden()
        self.pagina_plugins = PaginaPlugins()
        self.pagina_perfiles = PaginaPerfiles(main_window=self)
        self.pagina_donaciones = PaginaDonaciones()
        self.pagina_herramientas = PaginaHerramientas()
        self.pagina_redes = PaginaRedes()
        self.pagina_configuracion = PaginaConfiguracion(main_window=self)

        self.vistas.addWidget(self.pagina_mods)
        self.vistas.addWidget(self.pagina_orden)
        self.vistas.addWidget(self.pagina_plugins)
        self.vistas.addWidget(self.pagina_perfiles)
        self.vistas.addWidget(self.pagina_donaciones)
        self.vistas.addWidget(self.pagina_herramientas)
        self.vistas.addWidget(self.pagina_redes)
        self.vistas.addWidget(self.pagina_configuracion)

        botones_menu = (
            ("🚚  Mis Mods", 0),
            ("📋  Orden Mods", 1),
            ("🧩  Plugins", 2),
            ("👤  Perfiles", 3),
            (" Donaciones", 4),
            ("🛠️  Herramientas", 5),
            ("🌐  Redes Sociales", 6),
            ("⚙️  Configuración", 7),
        )

        self.botones_menu_sidebar = []
        for texto, indice in botones_menu:
            boton = QPushButton(texto)
            boton.setObjectName("botonMenu")
            boton.setFixedHeight(42)
            boton.setCursor(Qt.PointingHandCursor)
            boton.clicked.connect(
                lambda _, i=indice: self.vistas.setCurrentIndex(i))
            menu.addWidget(boton)
            self.botones_menu_sidebar.append((boton, indice))
            if indice == 4:
                self.boton_donaciones = boton
                self.boton_donaciones.setIconSize(QSize(20, 20))

        self.vistas.currentChanged.connect(self._on_vista_cambiada)
        self._on_vista_cambiada(0)

        menu.addStretch()
        diseño.addWidget(lateral)
        diseño.addWidget(self.vistas, 1)

        layout_principal.addWidget(contenedor_cuerpo)
        self.actualizar_textos_idioma()
        registrar_observador_idioma(self._on_idioma_cambiado)
        self.aplicar_tema()
        self._iniciar_animacion_corazon()

    def _on_idioma_cambiado(self, codigo):
        self.actualizar_textos_idioma()

    def actualizar_textos_idioma(self):
        """Actualiza los textos de la barra lateral y subcomponentes según el idioma activo."""
        tit_launcher = tr("LAUNCHER DE CHASIS {version}").format(version=VERSION_ACTUAL)
        self.setWindowTitle(tit_launcher)
        if hasattr(self, "barra_titulo") and hasattr(self.barra_titulo, "lbl_titulo"):
            self.barra_titulo.lbl_titulo.setText(tit_launcher)

        claves_sidebar = [
            ("🚚  ", "Mis Mods"),
            ("📋  ", "Orden Mods"),
            ("🧩  ", "Plugins"),
            ("👤  ", "Perfiles"),
            (" ", "Donaciones"),
            ("🛠️  ", "Herramientas"),
            ("🌐  ", "Redes Sociales"),
            ("⚙️  ", "Configuración"),
        ]
        if hasattr(self, "botones_menu_sidebar"):
            for boton, indice in self.botones_menu_sidebar:
                if 0 <= indice < len(claves_sidebar):
                    prefijo, clave = claves_sidebar[indice]
                    boton.setText(f"{prefijo}{tr(clave)}")

        for attr in ("pagina_mods", "pagina_orden", "pagina_plugins",
                     "pagina_perfiles", "pagina_donaciones",
                     "pagina_herramientas", "pagina_redes",
                     "pagina_configuracion"):
            if hasattr(self, attr):
                pag = getattr(self, attr)
                if hasattr(pag, "actualizar_textos_idioma"):
                    try:
                        pag.actualizar_textos_idioma()
                    except Exception as e:
                        print(f"[WARN] Error actualizando idioma en {attr}: {e}")

        if hasattr(self, "tarjetas") and self.tarjetas:
            for t in self.tarjetas.values():
                if hasattr(t, "actualizar_textos_idioma"):
                    try:
                        t.actualizar_textos_idioma()
                    except Exception:
                        pass

    def _iniciar_animacion_corazon(self):
        """Genera fotogramas en memoria del corazón (3 giros rápidos 'fuin fuin' + palpitaciones lentas + pausa) con 0% impacto CPU."""
        if not hasattr(self, "boton_donaciones"):
            return

        self._iconos_corazon = generar_iconos_corazon()
        self._frame_corazon = 0
        if self._iconos_corazon:
            self.boton_donaciones.setIcon(self._iconos_corazon[0])

        self._timer_corazon = QTimer(self)
        self._timer_corazon.setInterval(33)
        self._timer_corazon.timeout.connect(self._animar_paso_corazon)

        QTimer.singleShot(800, self._arrancar_timer_corazon)

    def _arrancar_timer_corazon(self):
        """Inicia el temporizador del corazón suavemente una vez estabilizada la ventana."""
        if hasattr(self, "_timer_corazon") and not self._timer_corazon.isActive():
            self._timer_corazon.start()

    def _animar_paso_corazon(self):
        """Avanza al siguiente fotograma del corazón precargado."""
        if not hasattr(self, "boton_donaciones") or not hasattr(self, "_iconos_corazon") or not self._iconos_corazon:
            return
        self._frame_corazon = (self._frame_corazon + 1) % len(self._iconos_corazon)
        self.boton_donaciones.setIcon(self._iconos_corazon[self._frame_corazon])

    def _on_vista_cambiada(self, indice_activo):
        """Actualiza la apariencia del botón activo en la barra lateral con el color del tema."""
        for boton, idx in getattr(self, "botones_menu_sidebar", []):
            activo = idx == indice_activo
            boton.setProperty("activo", "true" if activo else "false")
            boton.style().unpolish(boton)
            boton.style().polish(boton)

    def aplicar_tema(self, nombre_tema=None):
        """Aplica la hoja de estilos global y actualiza las vistas dinámicas con el tema seleccionado."""
        if nombre_tema:
            guardar_tema_actual(nombre_tema)
        self.setStyleSheet(obtener_hoja_estilos())
        if hasattr(self, "pagina_perfiles") and hasattr(self.pagina_perfiles, "actualizar_estilo_tabs"):
            self.pagina_perfiles.actualizar_estilo_tabs()
        if hasattr(self, "pagina_mods") and hasattr(self.pagina_mods, "actualizar_estilo_tema"):
            self.pagina_mods.actualizar_estilo_tema()
        if hasattr(self, "pagina_configuracion") and hasattr(self.pagina_configuracion, "actualizar_estilo_tema"):
            self.pagina_configuracion.actualizar_estilo_tema()
        if hasattr(self, "vistas"):
            self._on_vista_cambiada(self.vistas.currentIndex())

    def _crear_tarjetas_visuales(self):
        for mod in self.datos_servidor.get("mods", []):
            subruta_mod = os.path.join("mod", mod["archivo_scs"])
            ruta = obtener_ruta_ats(subruta_mod)
            tarjeta = TarjetaMod(
                mod, ruta,
                lambda _=False, m=mod: self._iniciar_descarga(m),
                lambda m=mod: self._cancelar_descarga(m),
                eliminar=lambda m=mod: self._eliminar_mod_individual(m),
            )
            self.tarjetas[mod["id"]] = tarjeta
            self.pagina_mods.agregar_tarjeta(tarjeta)
        self._actualizar_estado_boton_todos()

    def _eliminar_mod_individual(self, mod):
        mod_id = mod.get("id")
        subruta = os.path.join("mod", mod.get("archivo_scs", ""))
        ruta = obtener_ruta_ats(subruta)
        exito = download_manager.eliminar_archivo_mod(ruta)

        if not exito and download_manager.esta_juego_ejecutandose():
            QMessageBox.warning(
                self,
                "Juego en ejecución",
                f"No se pudo eliminar el mod '{mod.get('nombre', '')}' porque American Truck Simulator está abierto y lo tiene cargado en memoria.\n\nPor favor, sal del juego para poder eliminarlo."
            )
            return

        tarjeta = self.tarjetas.get(mod_id)
        if tarjeta:
            tarjeta.actualizar_estado("descargar")
            if mod_id in self.imagenes_mod:
                tarjeta.poner_imagen(self.imagenes_mod[mod_id], False)
            self._actualizar_estado_boton_todos()

    def eliminar_todos_los_mods(self):
        mods = self.datos_servidor.get("mods", [])
        if not mods:
            QMessageBox.information(self, "Sin mods", "No hay mods registrados para eliminar.")
            return

        if download_manager.esta_juego_ejecutandose():
            resp_juego = QMessageBox.warning(
                self,
                "Juego en ejecución",
                "⚠️ American Truck Simulator se encuentra abierto en este momento.\n\n"
                "Los mods que el juego esté usando activamente no podrán borrarse hasta que salgas del juego.\n\n"
                "¿Deseas intentar eliminar los mods de todos modos?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if resp_juego == QMessageBox.No:
                return

        resp = QMessageBox.warning(
            self,
            "Confirmar eliminación total",
            "⚠️ ¿Estás completamente seguro de que deseas ELIMINAR TODOS los mods del launcher?\n\n"
            "Esta acción borrará todos los paquetes de camiones, remolques, rines y skins instalados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resp == QMessageBox.Yes:
            bloqueados = 0
            for mod in mods:
                subruta = os.path.join("mod", mod.get("archivo_scs", ""))
                ruta = obtener_ruta_ats(subruta)
                if not download_manager.eliminar_archivo_mod(ruta):
                    bloqueados += 1
            if bloqueados > 0:
                QMessageBox.warning(
                    self,
                    "Archivos en uso",
                    f"{bloqueados} archivo(s) están bloqueados por American Truck Simulator. Ciérralo para eliminarlos por completo."
                )
            self.recargar_interfaz()

    def _actualizar_estado_boton_todos(self):
        """Actualiza el texto, estilo y disponibilidad del botón de descarga global."""
        if not hasattr(self, "pagina_mods") or not hasattr(self.pagina_mods, "boton_descargar_todos"):
            return

        btn = self.pagina_mods.boton_descargar_todos

        # Hay descargas en curso: el botón pasa a modo cancelar
        if len(self.eventos_cancelacion) > 0:
            btn.setText("✕  " + tr("Cancelar descarga"))
            btn.setProperty("estado", "cancelar")
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tr("Cancelar descarga"))
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            return

        # Sin tarjetas cargadas
        if not self.tarjetas:
            btn.setText("✓  " + tr("Todos los mods actualizados"))
            btn.setProperty("estado", "actualizado")
            btn.setEnabled(False)
            btn.setCursor(Qt.ArrowCursor)
            btn.setToolTip(tr("Todos los mods actualizados"))
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            return

        num_descargar = sum(1 for t in self.tarjetas.values() if t.estado_actual == "descargar")
        num_actualizar = sum(1 for t in self.tarjetas.values() if t.estado_actual == "actualizar")
        num_actualizado = sum(1 for t in self.tarjetas.values() if t.estado_actual == "actualizado")
        total = len(self.tarjetas)

        if num_descargar > 0:
            btn.setText("⬇  " + tr("Descargar todos los mods"))
            btn.setProperty("estado", "descargar")
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tr("Descargar todos los mods"))
        elif num_actualizar > 0:
            btn.setText("🔄  " + tr("Actualizar todos los mods"))
            btn.setProperty("estado", "actualizar")
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tr("Actualizar todos los mods"))
        elif num_actualizado == total:
            btn.setText("✓  " + tr("Todos los mods actualizados"))
            btn.setProperty("estado", "actualizado")
            btn.setEnabled(False)
            btn.setCursor(Qt.ArrowCursor)
            btn.setToolTip(tr("Todos los mods actualizados"))
        else:
            # Estados mixtos (validando, etc.)
            btn.setText("⬇  " + tr("Descargar todos los mods"))
            btn.setProperty("estado", "descargar")
            btn.setEnabled(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tr("Descargar todos los mods"))

        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def action_descargar_o_cancelar_todos(self):
        """Descarga todos los mods pendientes o cancela todas las descargas activas."""
        # Si hay descargas en curso, se cancelan todas
        if len(self.eventos_cancelacion) > 0:
            btn = self.pagina_mods.boton_descargar_todos
            btn.setText(tr("Cancelando..."))
            btn.setEnabled(False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            for evento in list(self.eventos_cancelacion.values()):
                evento.set()
            return

        # Si no, se descargan todos los pendientes
        mods = self.datos_servidor.get("mods", [])
        mods_a_descargar = [
            m for m in mods
            if self.tarjetas.get(m["id"])
            and self.tarjetas[m["id"]].estado_actual in ("descargar", "actualizar")
            and m["id"] not in self.eventos_cancelacion
        ]

        if not mods_a_descargar:
            self._actualizar_estado_boton_todos()
            return

        for mod in mods_a_descargar:
            self._iniciar_descarga(mod)

        self._actualizar_estado_boton_todos()

    def _manejar_fin_descarga(self, tarjeta, exito, mod_id):
        if mod_id in self.eventos_cancelacion:
            del self.eventos_cancelacion[mod_id]
        self.señales.descarga_finalizada.emit(tarjeta, exito)

    def _cancelar_descarga(self, mod):
        mod_id = mod["id"]
        if mod_id in self.eventos_cancelacion:
            self.eventos_cancelacion[mod_id].set()

    def _cargar_recursos(self):
        def _hilo_pool():
            with ThreadPoolExecutor(max_workers=3) as executor:
                for clave, url in RECURSOS_OFUSCADOS.items():
                    executor.submit(self._cargar_recurso, clave, url)
                for mod in self.datos_servidor.get("mods", []):
                    executor.submit(self._cargar_imagen_mod, mod)

        threading.Thread(target=_hilo_pool, daemon=True).start()

    def _cargar_recurso(self, clave, url):
        try:
            self.señales.recurso.emit(clave, descargar_imagen(url))
        except Exception as error:
            print(f"[UI] Error cargando {clave}: {error}")

    def _cargar_imagen_mod(self, mod):
        try:
            imagen = descargar_imagen(mod["imagen_url"])
            self.señales.imagen_mod.emit(mod["id"], imagen, imagen)
        except Exception as error:
            print(f"[UI] Error cargando imagen de {mod['nombre']}: {error}")

    def _iniciar_validacion(self, forzar_completo=False):
        # Reinicio de la animación del porcentaje
        self._porcentaje_real_val = 0
        self._porcentaje_visual_val = 0.0
        if not self.en_actualizacion_launcher:
            self.pagina_mods.texto_carga.setText(f"{tr('VALIDANDO ARCHIVOS')}: 0%")

        # Intervalo un poco más lento para un avance más natural
        self._timer_suavizado_val.setInterval(25)
        self._timer_suavizado_val.start()

        threading.Thread(
            target=lambda: self._validar_archivos_secuencial(forzar_completo), daemon=True).start()

    def _validar_archivos_secuencial(self, forzar_completo=False):
        # Aplica primero las actualizaciones de mods que quedaron pendientes
        download_manager.aplicar_actualizaciones_pendientes_mods()

        mods = self.datos_servidor.get("mods", [])
        total_mods = len(mods)

        if total_mods == 0:
            self.señales.validacion_terminada.emit()
            return

        completados = 0
        lock = threading.Lock()

        def validar_un_mod(mod):
            nonlocal completados
            tarjeta = self.tarjetas[mod["id"]]
            subruta_mod = os.path.join("mod", mod["archivo_scs"])
            ruta = obtener_ruta_ats(subruta_mod)
            tarjeta.ruta_archivo = ruta

            if not os.path.exists(ruta):
                estado = "descargar"
            else:
                # Oculta el archivo .scs para que no se manipule por error
                download_manager.ocultar_archivo_mod(ruta)

                hash_local = download_manager.obtener_md5_rapido(ruta, forzar_recalculo=forzar_completo)
                estado = "actualizado" if hash_local == mod.get(
                    "md5", "") and mod.get("md5") else "actualizar"

            with lock:
                completados += 1
                porcentaje = int((completados / total_mods) * 100)
                self.señales.progreso_validacion.emit(porcentaje)

            return mod, estado

        with ThreadPoolExecutor(max_workers=4) as executor:
            futuros = [executor.submit(validar_un_mod, mod) for mod in mods]

            for futuro in as_completed(futuros):
                mod, estado = futuro.result()
                self.señales.estado_mod.emit(mod, estado)

        self.señales.validacion_terminada.emit()

    def _iniciar_validacion_silenciosa_fondo(self):
        """A los 30 segundos, comprueba el MD5 real completo en segundo plano sin interrumpir ni congelar."""
        def _hilo_fondo():
            time.sleep(1)
            mods = self.datos_servidor.get("mods", []) if self.datos_servidor else []
            for mod in mods:
                # Si el usuario está descargando algo, se aborta la validación de fondo
                if len(self.eventos_cancelacion) > 0:
                    return

                subruta_mod = os.path.join("mod", mod.get("archivo_scs", ""))
                ruta = obtener_ruta_ats(subruta_mod)
                if not os.path.exists(ruta):
                    continue

                # Cálculo del MD5 real completo
                hash_real = download_manager.calcular_md5(ruta)
                if not hash_real:
                    continue

                # Se guarda en caché el hash real
                try:
                    stat_f = os.stat(ruta)
                    download_manager.guardar_en_cache_md5(
                        os.path.normcase(os.path.abspath(ruta)),
                        stat_f.st_size,
                        stat_f.st_mtime,
                        hash_real
                    )
                except Exception:
                    pass

                # Si no coincide con el servidor, se marca para actualizar
                md5_servidor = mod.get("md5", "")
                if md5_servidor and hash_real != md5_servidor:
                    self.señales.estado_mod.emit(mod, "actualizar")

                # Pausa para no saturar el disco
                time.sleep(1.5)

        threading.Thread(target=_hilo_fondo, daemon=True).start()

    def _recibir_imagen_mod(self, mod_id, imagen_color, _):
        self.imagenes_mod[mod_id] = imagen_color
        tarjeta = self.tarjetas.get(mod_id)
        if tarjeta:
            tarjeta.poner_imagen(
                imagen_color, tarjeta.estado_actual == "actualizado")

    def _recibir_recurso(self, clave, imagen):
        if clave == "logo":
            pixmap = QPixmap.fromImage(imagen).scaled(
                130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pixmap)
            self.logo.setText("")
        elif clave == "qr":
            pixmap = QPixmap.fromImage(imagen).scaled(
                280, 330, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.pagina_donaciones.etiqueta_qr.setPixmap(pixmap)
            self.pagina_donaciones.etiqueta_qr.setText("")
        elif clave == "paypal":
            pixmap = QPixmap.fromImage(imagen).scaled(
                260, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.pagina_donaciones.boton_paypal.setFixedHeight(45)
            self.pagina_donaciones.boton_paypal.setIcon(QIcon(pixmap))
            self.pagina_donaciones.boton_paypal.setIconSize(QSize(260, 50))
            self.pagina_donaciones.boton_paypal.setText("")
        elif clave == "orden":
            pixmap = QPixmap.fromImage(imagen)
            self.pagina_orden.imagen_orden.setPixmap(pixmap)
            self.pagina_orden.imagen_orden.setFixedSize(pixmap.size())
            self.pagina_orden.imagen_orden.setText("")
        else:
            for boton in self.pagina_redes.findChildren(QPushButton):
                if boton.property("recurso") == clave:
                    boton.setIcon(QIcon(QPixmap.fromImage(imagen)))
                    boton.setIconSize(QSize(256, 128))
                    boton.setText("")
                    return

    def _recibir_estado(self, mod, estado):
        mod_id = mod["id"]
        tarjeta = self.tarjetas.get(mod_id)
        if tarjeta is None:
            return
        tarjeta.actualizar_estado(estado)
        if mod_id in self.imagenes_mod:
            tarjeta.poner_imagen(
                self.imagenes_mod[mod_id], estado == "actualizado")

    def _iniciar_descarga(self, mod):
        tarjeta = self.tarjetas[mod["id"]]
        tarjeta.mostrar_progreso(0)
        evento_cancelar = threading.Event()
        self.eventos_cancelacion[mod["id"]] = evento_cancelar

        iniciar_descarga_hilo(
            mod["url_descarga"], tarjeta.ruta_archivo,
            lambda exito, t=tarjeta, m_id=mod["id"]: self._manejar_fin_descarga(
                t, exito, m_id),
            lambda valor, t=tarjeta: self.señales.progreso.emit(
                t, int(valor * 100)),
            evento_cancelar
        )

        self._actualizar_estado_boton_todos()

    @staticmethod
    def _actualizar_progreso(tarjeta, valor):
        # La tarjeta puede no existir si se recargó la interfaz
        if tarjeta:
            tarjeta.mostrar_progreso(valor)

    def _terminar_descarga(self, tarjeta, exito):
        if exito:
            tarjeta.animar_explosion_completado()
            tarjeta.actualizar_estado("actualizado")
            imagen = self.imagenes_mod.get(tarjeta.mod["id"])
            if imagen:
                tarjeta.poner_imagen(imagen, True)
        else:
            tarjeta.ocultar_progreso()
            tarjeta.actualizar_estado("descargar")
        self._actualizar_estado_boton_todos()

    def _animar_carga(self):
        self.pagina_mods.spinner.avanzar()

    def _mostrar_carga(self):
        self.pagina_mods.boton_validar.setEnabled(False)
        if hasattr(self.pagina_mods, "boton_descargar_todos"):
            self.pagina_mods.boton_descargar_todos.setEnabled(False)
            self.pagina_mods.boton_descargar_todos.setText(tr("Validando..."))
            self.pagina_mods.boton_descargar_todos.setToolTip(tr("Comprobando el estado de los mods..."))
        self.pagina_mods.contenedor_mods.hide()
        self.pagina_mods.capa_carga.show()
        self._timer_carga.start(33)

    def _paso_animacion_porcentaje(self):
        """
        Avanza el porcentaje de forma orgánica. Si hay una pausa por un mod pesado,
        sigue avanzando poco a poco sin congelarse.
        """
        # Si el valor visual va por detrás del real, se acerca suavemente
        if self._porcentaje_visual_val < self._porcentaje_real_val:
            diferencia = self._porcentaje_real_val - self._porcentaje_visual_val
            # Paso proporcional a la distancia, con un mínimo para que nunca se detenga
            paso = max(0.4, diferencia * 0.08)
            self._porcentaje_visual_val += paso

        # Si está esperando a un mod pesado, avanza muy despacio sin llegar a 100
        elif self._porcentaje_visual_val < 98.0 and self._porcentaje_real_val < 100:
            self._porcentaje_visual_val += 0.08

        val_int = int(min(100, self._porcentaje_visual_val))

        if not self.en_actualizacion_launcher:
            self.pagina_mods.texto_carga.setText(
                f"{tr('VALIDANDO ARCHIVOS')}: {val_int}%")

        if val_int >= 100:
            self._timer_suavizado_val.stop()

    def _ocultar_carga(self):
        if self.en_actualizacion_launcher:
            return

        # Fuerza el porcentaje real al 100%
        self._porcentaje_real_val = 100

        def _comprobar_fin_animacion():
            # Espera a que la animación visual llegue al final antes de ocultar
            if self._porcentaje_visual_val >= 99.0:
                self._porcentaje_visual_val = 100.0
                if not self.en_actualizacion_launcher:
                    self.pagina_mods.texto_carga.setText(
                        f"{tr('VALIDANDO ARCHIVOS')}: 100%")

                self._timer_suavizado_val.stop()
                self._timer_carga.stop()
                self.pagina_mods.capa_carga.hide()
                self.pagina_mods.contenedor_mods.show()
                self.pagina_mods.boton_validar.setEnabled(True)
                QTimer.singleShot(50, self.pagina_mods._colocar_flechas)
                self._actualizar_estado_boton_todos()

                # Animación del botón de novedades al terminar la carga
                if hasattr(self.pagina_mods, "animar_boton_novedades"):
                    self.pagina_mods.animar_boton_novedades()
            else:
                QTimer.singleShot(30, _comprobar_fin_animacion)

        _comprobar_fin_animacion()

    def recargar_interfaz(self):
        self._mostrar_carga()
        for tarjeta in self.tarjetas.values():
            tarjeta.boton.setEnabled(False)
            tarjeta.boton.setText("Validando…")
            tarjeta.boton.setStyleSheet("background: #3E3E3E;")
            if tarjeta.mod["id"] in self.imagenes_mod:
                tarjeta.poner_imagen(
                    self.imagenes_mod[tarjeta.mod["id"]], False)

        self._iniciar_validacion(forzar_completo=True)

    def closeEvent(self, evento):
        try:
            desregistrar_observador_idioma(self._on_idioma_cambiado)
        except Exception:
            pass
        for evento_cancelar in self.eventos_cancelacion.values():
            evento_cancelar.set()
        super().closeEvent(evento)

    def _actualizar_texto_validacion(self, porcentaje_real):
        # Solo se actualiza el objetivo; la animación lo alcanza suavemente
        self._porcentaje_real_val = porcentaje_real

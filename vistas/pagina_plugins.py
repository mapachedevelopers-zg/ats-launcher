import os
import zipfile
import threading
import requests
import shutil

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QFrame, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal, QObject
from utils import aplicar_sombra, obtener_ruta_ats
from download_manager import obtener_ruta_ats, obtener_ruta_exe_ats, obtener_datos_servidor, esta_juego_ejecutandose
from i18n import tr


class SeñalesPlugin(QObject):
    progreso = Signal(str, str)
    finalizado = Signal(str, bool, str)


class PaginaPlugins(QWidget):
    def __init__(self):
        super().__init__()
        self.señales = SeñalesPlugin()
        self.señales.progreso.connect(self._actualizar_texto_boton)
        self.señales.finalizado.connect(self._fin_instalacion)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(20)

        self.titulo = QLabel(tr("PLUGINS DISPONIBLES"))
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.titulo)

        grid = QGridLayout()
        grid.setSpacing(16)

        # ---------- CarPlay ----------
        self.btn_carplay = QPushButton("INSTALAR")
        self.btn_carplay.setFixedSize(130, 32)
        self.btn_carplay.clicked.connect(self._instalar_carplay)

        self.btn_carplay_del = QPushButton("Desinstalar")
        self.btn_carplay_del.setFixedSize(130, 24)
        self.btn_carplay_del.setCursor(Qt.PointingHandCursor)
        self.btn_carplay_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #E74C3C; font-size: 10px; font-weight: 700; border: none;
            }
            QPushButton:hover { color: #FF6B6B; text-decoration: underline; }
        """)
        self.btn_carplay_del.clicked.connect(
            lambda: self._desinstalar_plugin("carplay"))
        self.btn_carplay_del.hide()

        card_carplay = self._crear_tarjeta_carplay(
            "🖥️ CarPlay",
            "Transmite en tiempo real tu pantalla (YouTube, Spotify, navegador) directamente en el GPS o pantalla de la cabina de tu camión.",
            "⌨️ Activar/desactivar en el juego con Ctrl + F8",
            self.btn_carplay,
            [self.btn_carplay_del]
        )
        grid.addWidget(card_carplay, 0, 0)

        # ---------- ReShade ----------
        self.btn_reshade = QPushButton("INSTALAR")
        self.btn_reshade.setFixedSize(130, 32)
        self.btn_reshade.clicked.connect(self._instalar_reshade)

        self.btn_reshade_del = QPushButton("Desinstalar")
        self.btn_reshade_del.setFixedSize(130, 24)
        self.btn_reshade_del.setCursor(Qt.PointingHandCursor)
        self.btn_reshade_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #E74C3C; font-size: 10px; font-weight: 700; border: none;
            }
            QPushButton:hover { color: #FF6B6B; text-decoration: underline; }
        """)
        self.btn_reshade_del.clicked.connect(
            lambda: self._desinstalar_plugin("reshade"))
        self.btn_reshade_del.hide()

        card_reshade = self._crear_tarjeta_carplay(
            "🎨 ReShade Presets",
            "Mejora la definición, nitidez y saturación de color del juego. Incluye múltiples perfiles personalizables.",
            "⌨️ Activar/Desactivar con Insert\n⚙️ Menú de ajustes con tecla Home",
            self.btn_reshade,
            [self.btn_reshade_del]
        )
        grid.addWidget(card_reshade, 0, 1)

        # ---------- Direccionales automáticas ----------
        self.btn_blinker = QPushButton("INSTALAR")
        self.btn_blinker.setFixedSize(130, 32)
        self.btn_blinker.clicked.connect(self._instalar_blinker)

        self.btn_blinker_del = QPushButton("Desinstalar")
        self.btn_blinker_del.setFixedSize(80, 28)
        self.btn_blinker_del.setCursor(Qt.PointingHandCursor)
        self.btn_blinker_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #E74C3C; font-size: 10px; font-weight: 700; border: none;
            }
            QPushButton:hover { color: #FF6B6B; text-decoration: underline; }
        """)
        self.btn_blinker_del.clicked.connect(
            lambda: self._desinstalar_plugin("blinker"))
        self.btn_blinker_del.hide()

        self.btn_blinker_cfg = QPushButton("Configurar")
        self.btn_blinker_cfg.setFixedSize(80, 28)
        self.btn_blinker_cfg.setCursor(Qt.PointingHandCursor)
        self.btn_blinker_cfg.setStyleSheet("""
            QPushButton {
                background: transparent; color: #2ECC71; font-size: 10px; font-weight: 700; border: none;
            }
            QPushButton:hover { color: #58D68D; text-decoration: underline; }
        """)
        self.btn_blinker_cfg.clicked.connect(self._abrir_config_blinker)
        self.btn_blinker_cfg.hide()

        card_blinker = self._crear_tarjeta_carplay(
            "💡 Direccionales Automáticas",
            "Activa automáticamente los direccionales al girar el volante más de 70° y los apaga al enderezar.",
            "⚙️ Configurable desde autoblinker.ini en la carpeta plugins",
            self.btn_blinker,
            [self.btn_blinker_cfg, self.btn_blinker_del]
        )
        grid.addWidget(card_blinker, 1, 0)

        # ---------- Cabin Walk ----------
        self.btn_cabinwalk = QPushButton("INSTALAR")
        self.btn_cabinwalk.setFixedSize(130, 32)
        self.btn_cabinwalk.clicked.connect(self._instalar_cabinwalk)

        self.btn_cabinwalk_del = QPushButton("Desinstalar")
        self.btn_cabinwalk_del.setFixedSize(130, 24)
        self.btn_cabinwalk_del.setCursor(Qt.PointingHandCursor)
        self.btn_cabinwalk_del.setStyleSheet("""
            QPushButton {
                background: transparent; color: #E74C3C; font-size: 10px; font-weight: 700; border: none;
            }
            QPushButton:hover { color: #FF6B6B; text-decoration: underline; }
        """)
        self.btn_cabinwalk_del.clicked.connect(
            lambda: self._desinstalar_plugin("cabinwalk"))
        self.btn_cabinwalk_del.hide()

        card_cabinwalk = self._crear_tarjeta_carplay(
            "🚶 Cabin Walk",
            "Permite moverte libremente por el interior del camión (asiento pasajero, cama/sofá, de pie) mediante atajos del teclado numérico.",
            "⌨️ Menú / Configurar: Supr\n  • Conductor: Numpad 5\n  • Pasajero: Numpad 3\n  • De pie: Numpad 2\n  • Sofá: Numpad 1",
            self.btn_cabinwalk,
            [self.btn_cabinwalk_del]
        )
        grid.addWidget(card_cabinwalk, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()

        self._verificar_estado_carplay()
        self._verificar_estado_reshade()
        self._verificar_estado_blinker()
        self._verificar_estado_cabinwalk()

    def _crear_tarjeta_carplay(self, titulo, descripcion, nota, boton_instalar, lista_botones_secundarios):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        tarjeta.setFixedHeight(175)
        aplicar_sombra(tarjeta)

        lay = QVBoxLayout(tarjeta)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(6)

        lbl_t = QLabel(tr(titulo))
        lbl_t.setStyleSheet(
            "color: #F8FAFC; font-size: 14px; font-weight: 800; background: transparent;")

        lbl_d = QLabel(tr(descripcion))
        lbl_d.setWordWrap(True)
        lbl_d.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;")

        lbl_nota = QLabel(tr(nota))
        lbl_nota.setWordWrap(True)
        lbl_nota.setStyleSheet(
            "color: #E5A93C; font-size: 10px; font-weight: 700; background: transparent;")

        if not hasattr(self, "_tarjetas_plugins_textos"):
            self._tarjetas_plugins_textos = []
        self._tarjetas_plugins_textos.append({
            "lbl_t": lbl_t, "titulo": titulo,
            "lbl_d": lbl_d, "desc": descripcion,
            "lbl_nota": lbl_nota, "nota": nota,
        })

        lay_secundarios = QHBoxLayout()
        lay_secundarios.setSpacing(4)
        for btn_sec in lista_botones_secundarios:
            lay_secundarios.addWidget(btn_sec)

        botones_layout = QVBoxLayout()
        botones_layout.addWidget(boton_instalar)
        botones_layout.addLayout(lay_secundarios)
        botones_layout.setSpacing(2)

        fila_b = QHBoxLayout()
        fila_b.addWidget(lbl_nota, 1)
        fila_b.addSpacing(10)
        fila_b.addLayout(botones_layout)

        lay.addWidget(lbl_t)
        lay.addWidget(lbl_d)
        lay.addLayout(fila_b)
        return tarjeta

    def _abrir_config_blinker(self):
        exe_path = obtener_ruta_exe_ats()
        if exe_path and os.path.exists(exe_path):
            dir_bin_win64 = os.path.dirname(exe_path)
            ruta_ini = os.path.join(
                dir_bin_win64, "plugins", "autoblinker.ini")

            if os.path.exists(ruta_ini):
                os.startfile(ruta_ini)
            else:
                QMessageBox.warning(
                    self, "Archivo no encontrado",
                    "No se encontró el archivo de configuración 'autoblinker.ini'.")
        else:
            QMessageBox.warning(
                self, "ATS no encontrado",
                "No se pudo determinar la ruta de instalación del juego.")

    def _verificar_estado_carplay(self):
        exe_path = obtener_ruta_exe_ats()
        if exe_path and os.path.exists(exe_path):
            ruta_dll = os.path.join(os.path.dirname(
                exe_path), "plugins", "PrismTextureStreamerFB.dll")
            if os.path.exists(ruta_dll):
                self.btn_carplay.setText(tr("INSTALADO"))
                self.btn_carplay.setProperty("estado", "exito")
                self.btn_carplay.style().unpolish(self.btn_carplay)
                self.btn_carplay.style().polish(self.btn_carplay)
                self.btn_carplay_del.show()
                return
        self.btn_carplay.setText(tr("INSTALAR"))

    def _verificar_estado_reshade(self):
        exe_path = obtener_ruta_exe_ats()
        if exe_path and os.path.exists(exe_path):
            dir_bin = os.path.dirname(exe_path)
            if os.path.exists(os.path.join(dir_bin, "dxgi.dll")) or os.path.exists(os.path.join(dir_bin, "ReShade.ini")):
                self.btn_reshade.setText(tr("INSTALADO"))
                self.btn_reshade.setProperty("estado", "exito")
                self.btn_reshade.style().unpolish(self.btn_reshade)
                self.btn_reshade.style().polish(self.btn_reshade)
                self.btn_reshade_del.show()
                return
        self.btn_reshade.setText(tr("INSTALAR"))

    def _verificar_estado_blinker(self):
        exe_path = obtener_ruta_exe_ats()
        if exe_path and os.path.exists(exe_path):
            dir_plugins = os.path.join(os.path.dirname(exe_path), "plugins")
            if os.path.exists(os.path.join(dir_plugins, "autoblinker.dll")):
                self.btn_blinker.setText(tr("INSTALADO"))
                self.btn_blinker.setProperty("estado", "exito")
                self.btn_blinker.style().unpolish(self.btn_blinker)
                self.btn_blinker.style().polish(self.btn_blinker)
                self.btn_blinker_del.show()
                self.btn_blinker_cfg.show()
                return
        self.btn_blinker.setText(tr("INSTALAR"))

    def _verificar_estado_cabinwalk(self):
        exe_path = obtener_ruta_exe_ats()
        if exe_path and os.path.exists(exe_path):
            dir_plugins = os.path.join(os.path.dirname(exe_path), "plugins")
            # Cabin Walk se basa en el framework SPF
            if os.path.exists(os.path.join(dir_plugins, "spf-framework.dll")):
                self.btn_cabinwalk.setText(tr("INSTALADO"))
                self.btn_cabinwalk.setProperty("estado", "exito")
                self.btn_cabinwalk.style().unpolish(self.btn_cabinwalk)
                self.btn_cabinwalk.style().polish(self.btn_cabinwalk)
                self.btn_cabinwalk_del.show()
                return
        self.btn_cabinwalk.setText(tr("INSTALAR"))

    def actualizar_textos_idioma(self):
        """Actualiza el título y botones de la sección de plugins."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("PLUGINS DISPONIBLES"))
        for btn_del in (self.btn_carplay_del, self.btn_reshade_del, self.btn_blinker_del, self.btn_cabinwalk_del):
            if btn_del:
                btn_del.setText(tr("Desinstalar"))
        if hasattr(self, "btn_blinker_cfg") and self.btn_blinker_cfg:
            self.btn_blinker_cfg.setText(tr("Configurar"))
        for t_info in getattr(self, "_tarjetas_plugins_textos", []):
            t_info["lbl_t"].setText(tr(t_info["titulo"]))
            t_info["lbl_d"].setText(tr(t_info["desc"]))
            t_info["lbl_nota"].setText(tr(t_info["nota"]))
        self._verificar_estado_carplay()
        self._verificar_estado_reshade()
        self._verificar_estado_blinker()
        self._verificar_estado_cabinwalk()

    def _instalar_carplay(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de instalar o modificar este plugin."
            )
            return
        self.btn_carplay.setEnabled(False)
        threading.Thread(target=self._hilo_instalacion_plugin,
                         args=("carplay",), daemon=True).start()

    def _instalar_reshade(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de instalar o modificar este plugin."
            )
            return
        self.btn_reshade.setEnabled(False)
        threading.Thread(target=self._hilo_instalacion_plugin,
                         args=("reshade",), daemon=True).start()

    def _instalar_blinker(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de instalar o modificar este plugin."
            )
            return
        self.btn_blinker.setEnabled(False)
        threading.Thread(target=self._hilo_instalacion_plugin,
                         args=("blinker",), daemon=True).start()

    def _instalar_cabinwalk(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de instalar o modificar este plugin."
            )
            return
        self.btn_cabinwalk.setEnabled(False)
        threading.Thread(target=self._hilo_instalacion_plugin,
                         args=("cabinwalk",), daemon=True).start()

    def _desinstalar_plugin(self, tipo):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de desinstalar este plugin."
            )
            return

        exe_path = obtener_ruta_exe_ats()
        if not exe_path or not os.path.exists(exe_path):
            self.señales.progreso.emit(tipo, "ERROR: ATS NO HALLADO")
            return

        dir_bin_win64 = os.path.dirname(exe_path)

        if tipo == "carplay":
            ruta_dll = os.path.join(
                dir_bin_win64, "plugins", "PrismTextureStreamerFB.dll")
            if os.path.exists(ruta_dll):
                os.remove(ruta_dll)

            ruta_docs = os.path.join(
                obtener_ruta_ats(""), "PrismTextureStreamer")
            if os.path.exists(ruta_docs):
                shutil.rmtree(ruta_docs, ignore_errors=True)

            self.btn_carplay_del.hide()
            self._fin_instalacion("carplay", False, "INSTALAR")

        elif tipo == "reshade":
            archivos_reshade = ["dxgi.dll", "ReShade.ini",
                                "ReShade.log", "dxgi.log"]
            carpetas_reshade = ["reshade-shaders"]

            for archivo in archivos_reshade:
                ruta_arch = os.path.join(dir_bin_win64, archivo)
                if os.path.exists(ruta_arch):
                    os.remove(ruta_arch)

            for carpeta in carpetas_reshade:
                ruta_carp = os.path.join(dir_bin_win64, carpeta)
                if os.path.exists(ruta_carp):
                    shutil.rmtree(ruta_carp, ignore_errors=True)

            self.btn_reshade_del.hide()
            self._fin_instalacion("reshade", False, "INSTALAR")

        elif tipo == "blinker":
            dir_plugins = os.path.join(dir_bin_win64, "plugins")
            for archivo in ("autoblinker.dll", "autoblinker.ini"):
                ruta_arch = os.path.join(dir_plugins, archivo)
                if os.path.exists(ruta_arch):
                    os.remove(ruta_arch)

            self.btn_blinker_del.hide()
            self.btn_blinker_cfg.hide()
            self._fin_instalacion("blinker", False, "INSTALAR")

        elif tipo == "cabinwalk":
            dir_plugins = os.path.join(dir_bin_win64, "plugins")

            # Eliminar la DLL del framework SPF
            dll_spf = os.path.join(dir_plugins, "spf-framework.dll")
            if os.path.exists(dll_spf):
                os.remove(dll_spf)

            # Eliminar las carpetas del framework SPF
            for carpeta_spf in ("spfAssets", "spfPlugins"):
                ruta_c = os.path.join(dir_plugins, carpeta_spf)
                if os.path.exists(ruta_c):
                    shutil.rmtree(ruta_c, ignore_errors=True)

            self.btn_cabinwalk_del.hide()
            self._fin_instalacion("cabinwalk", False, "INSTALAR")

    def _hilo_instalacion_plugin(self, tipo):
        try:
            self.señales.progreso.emit(tipo, "Descargando...")

            datos_servidor = obtener_datos_servidor() or {}

            if tipo == "carplay":
                url = datos_servidor.get(
                    "carplay_url", "https://github.com/joseluishernandezclaros/ats-mods-repo/releases/download/1.2/CARPLAY.zip")
                nombre_zip = "CARPLAY.zip"
            elif tipo == "reshade":
                url = datos_servidor.get(
                    "reshade_url", "https://github.com/joseluishernandezclaros/ats-mods-repo/releases/download/1.2/RESHADE.zip")
                nombre_zip = "RESHADE.zip"
            elif tipo == "blinker":
                url = datos_servidor.get(
                    "blinker_url", "https://github.com/joseluishernandezclaros/ats-mods-repo/releases/download/1.2/DIRECCIONALES.zip")
                nombre_zip = "DIRECCIONALES.zip"
            else:
                url = datos_servidor.get(
                    "cabin_walk_url", "https://github.com/joseluishernandezclaros/ats-mods-repo/releases/download/1.2/Cabin_Walk.zip")
                nombre_zip = "Cabin_Walk.zip"

            resp = requests.get(url, stream=True)
            ruta_zip_temp = os.path.join(
                os.environ.get("TEMP", "."), nombre_zip)

            with open(ruta_zip_temp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.señales.progreso.emit(tipo, "Instalando...")

            exe_path = obtener_ruta_exe_ats()
            if not exe_path or not os.path.exists(exe_path):
                self.señales.finalizado.emit(tipo, False, "EXE NO HALLADO")
                return

            dir_bin_win64 = os.path.dirname(exe_path)
            ruta_extract_temp = os.path.join(
                os.environ.get("TEMP", "."), f"{nombre_zip}_EXTRACT")

            with zipfile.ZipFile(ruta_zip_temp, "r") as zip_ref:
                zip_ref.extractall(ruta_extract_temp)

            if tipo == "carplay":
                ruta_docs_ats = obtener_ruta_ats("")
                ruta_plugins_juego = os.path.join(dir_bin_win64, "plugins")
                os.makedirs(ruta_plugins_juego, exist_ok=True)

                for root, _, files in os.walk(ruta_extract_temp):
                    for file in files:
                        full_path = os.path.join(root, file)

                        if file.lower() == "prismtexturestreamerfb.dll":
                            dest_dll = os.path.join(ruta_plugins_juego, file)
                            if os.path.exists(dest_dll):
                                os.remove(dest_dll)
                            shutil.move(full_path, dest_dll)

                        elif "PrismTextureStreamer" in root:
                            rel_path = os.path.relpath(
                                full_path, ruta_extract_temp)
                            dest_path = os.path.join(ruta_docs_ats, rel_path)
                            os.makedirs(os.path.dirname(
                                dest_path), exist_ok=True)
                            if os.path.exists(dest_path):
                                os.remove(dest_path)
                            shutil.move(full_path, dest_path)

            elif tipo == "reshade":
                for root, _, files in os.walk(ruta_extract_temp):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(
                            full_path, ruta_extract_temp)
                        dest_path = os.path.join(dir_bin_win64, rel_path)

                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        shutil.move(full_path, dest_path)

            elif tipo in ("blinker", "cabinwalk"):
                # Los plugins de este tipo se copian directamente a bin/win_x64/plugins
                dir_plugins = os.path.join(dir_bin_win64, "plugins")
                os.makedirs(dir_plugins, exist_ok=True)

                for item in os.listdir(ruta_extract_temp):
                    full_item_path = os.path.join(ruta_extract_temp, item)
                    dest_item_path = os.path.join(dir_plugins, item)

                    if os.path.isfile(full_item_path):
                        if os.path.exists(dest_item_path):
                            os.remove(dest_item_path)
                        shutil.move(full_item_path, dest_item_path)
                    elif os.path.isdir(full_item_path):
                        if os.path.exists(dest_item_path):
                            shutil.rmtree(dest_item_path, ignore_errors=True)
                        shutil.move(full_item_path, dest_item_path)

            self.señales.finalizado.emit(tipo, True, "¡INSTALADO!")
        except Exception as e:
            print(f"[Plugins] Error instalando {tipo}: {e}")
            self.señales.finalizado.emit(tipo, False, "ERROR")

    def _actualizar_texto_boton(self, tipo, texto):
        if tipo == "carplay":
            btn = self.btn_carplay
        elif tipo == "reshade":
            btn = self.btn_reshade
        elif tipo == "blinker":
            btn = self.btn_blinker
        else:
            btn = self.btn_cabinwalk
        btn.setText(texto)

    def _fin_instalacion(self, tipo, exito, mensaje):
        if tipo == "carplay":
            btn, btn_del = self.btn_carplay, self.btn_carplay_del
            btn_cfg = None
        elif tipo == "reshade":
            btn, btn_del = self.btn_reshade, self.btn_reshade_del
            btn_cfg = None
        elif tipo == "blinker":
            btn, btn_del = self.btn_blinker, self.btn_blinker_del
            btn_cfg = self.btn_blinker_cfg
        else:
            btn, btn_del = self.btn_cabinwalk, self.btn_cabinwalk_del
            btn_cfg = None

        btn.setText(mensaje)
        if exito:
            btn.setProperty("estado", "exito")
            btn_del.show()
            if btn_cfg:
                btn_cfg.show()
        else:
            btn.setProperty("estado", "")
            btn.setEnabled(True)
            btn_del.hide()
            if btn_cfg:
                btn_cfg.hide()

        btn.style().unpolish(btn)
        btn.style().polish(btn)

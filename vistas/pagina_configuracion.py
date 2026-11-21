import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout,
    QFileDialog, QMessageBox, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, QUrl, QSize, QTimer, QPoint
from PySide6.QtGui import QDesktopServices
from download_manager import (
    obtener_ruta_ats, obtener_ruta_exe_ats, obtener_ruta_plugins_ats,
    cargar_config_usuario, guardar_config_usuario
)
from utils import aplicar_sombra
from temas import (
    TEMAS, obtener_nombre_tema_actual, guardar_tema_actual,
    crear_icono_tema, TEMA_POR_DEFECTO
)
from i18n import tr, IDIOMAS, obtener_idioma_actual, guardar_idioma_actual


class PaginaConfiguracion(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        diseño = QVBoxLayout(self)
        diseño.setContentsMargins(40, 40, 40, 40)
        diseño.setSpacing(20)

        self.titulo = QLabel("CONFIGURACIÓN DEL LAUNCHER")
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignLeft)
        diseño.addWidget(self.titulo)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        aplicar_sombra(tarjeta)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(25, 25, 25, 25)
        layout_tarjeta.setSpacing(20)

        self.lineas_divisorias = []

        # --- Línea divisoria superior ---
        linea0 = QWidget()
        linea0.setFixedHeight(1)
        linea0.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea0)
        self.lineas_divisorias.append(linea0)

        # ==========================================
        # FILA: CARPETA MOD
        # ==========================================
        fila_folder = QHBoxLayout()
        fila_folder.setSpacing(15)

        self.lbl_etiqueta_mod = QLabel("Carpeta Mod")
        self.lbl_etiqueta_mod.setStyleSheet(
            "color: white; font-weight: bold; font-size: 14px; background: transparent;")
        self.lbl_etiqueta_mod.setFixedWidth(110)
        fila_folder.addWidget(self.lbl_etiqueta_mod)

        ruta_mod_actual = obtener_ruta_ats("mod")
        self.lbl_ruta_mod = QLineEdit(ruta_mod_actual)
        self.lbl_ruta_mod.setReadOnly(True)
        self.lbl_ruta_mod.setFixedHeight(35)
        self.lbl_ruta_mod.setToolTip(ruta_mod_actual)
        self.lbl_ruta_mod.setCursorPosition(0)
        self.lbl_ruta_mod.setStyleSheet(
            "color: #CCCCCC; font-size: 13px; font-weight: 600; background: #1E1E1E; padding: 0 10px; border-radius: 4px; border: 1px solid #3E3E3E;")
        fila_folder.addWidget(self.lbl_ruta_mod, 1)

        self.btn_cambiar_mod = QPushButton("Cambiar")
        self.btn_cambiar_mod.setFixedSize(90, 35)
        self.btn_cambiar_mod.setCursor(Qt.PointingHandCursor)
        self.btn_cambiar_mod.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: white; border: 1px solid #555555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #3E3E3E; border-color: #2980B9; } QPushButton:pressed { background-color: #1E1E1E; }")
        self.btn_cambiar_mod.clicked.connect(self.action_cambiar_carpeta_mod)
        fila_folder.addWidget(self.btn_cambiar_mod)

        self.btn_abrir_mod = QPushButton("Abrir Carpeta")
        self.btn_abrir_mod.setFixedSize(100, 35)
        self.btn_abrir_mod.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_mod.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: #2ECC71; border: 1px solid #27AE60; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #27AE60; color: white; border-color: #2ECC71; }")
        self.btn_abrir_mod.clicked.connect(self.action_abrir_carpeta_mod)
        fila_folder.addWidget(self.btn_abrir_mod)

        layout_tarjeta.addLayout(fila_folder)

        # --- Línea divisoria ---
        linea1 = QWidget()
        linea1.setFixedHeight(1)
        linea1.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea1)
        self.lineas_divisorias.append(linea1)

        # ==========================================
        # FILA: CARPETA DE FOTOS (SCREENSHOTS)
        # ==========================================
        fila_screen = QHBoxLayout()
        fila_screen.setSpacing(15)

        self.lbl_etiqueta_screen = QLabel("Carpeta de\nFotos")
        self.lbl_etiqueta_screen.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_screen.setFixedWidth(110)
        self.lbl_etiqueta_screen.setWordWrap(True)
        fila_screen.addWidget(self.lbl_etiqueta_screen)

        config = cargar_config_usuario()
        ruta_screen_defecto = os.path.normpath(
            os.path.join(obtener_ruta_ats(""), "screenshot"))
        ruta_screen_actual = config.get(
            "custom_screenshot_dir", ruta_screen_defecto)

        self.lbl_ruta_screen = QLineEdit(ruta_screen_actual)
        self.lbl_ruta_screen.setReadOnly(True)
        self.lbl_ruta_screen.setFixedHeight(35)
        self.lbl_ruta_screen.setToolTip(ruta_screen_actual)
        self.lbl_ruta_screen.setCursorPosition(0)
        self.lbl_ruta_screen.setStyleSheet(
            "color: #CCCCCC; font-size: 13px; font-weight: 600; background: #1E1E1E; padding: 0 10px; border-radius: 4px; border: 1px solid #3E3E3E;")
        fila_screen.addWidget(self.lbl_ruta_screen, 1)

        self.btn_cambiar_screen = QPushButton("Cambiar")
        self.btn_cambiar_screen.setFixedSize(90, 35)
        self.btn_cambiar_screen.setCursor(Qt.PointingHandCursor)
        self.btn_cambiar_screen.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: white; border: 1px solid #555555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #3E3E3E; border-color: #2980B9; } QPushButton:pressed { background-color: #1E1E1E; }")
        self.btn_cambiar_screen.clicked.connect(self.action_cambiar_carpeta_screen)
        fila_screen.addWidget(self.btn_cambiar_screen)

        self.btn_abrir_screen = QPushButton("Abrir Carpeta")
        self.btn_abrir_screen.setFixedSize(100, 35)
        self.btn_abrir_screen.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_screen.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: #2ECC71; border: 1px solid #27AE60; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #27AE60; color: white; border-color: #2ECC71; }")
        self.btn_abrir_screen.clicked.connect(self.action_abrir_carpeta_screen)
        fila_screen.addWidget(self.btn_abrir_screen)

        layout_tarjeta.addLayout(fila_screen)

        # --- Línea divisoria ---
        linea2 = QWidget()
        linea2.setFixedHeight(1)
        linea2.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea2)
        self.lineas_divisorias.append(linea2)

        # ==========================================
        # FILA: CARPETA DE PLUGINS
        # ==========================================
        fila_plugins = QHBoxLayout()
        fila_plugins.setSpacing(15)

        self.lbl_etiqueta_plugins = QLabel("Carpeta de\nPlugins")
        self.lbl_etiqueta_plugins.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_plugins.setFixedWidth(110)
        self.lbl_etiqueta_plugins.setWordWrap(True)
        fila_plugins.addWidget(self.lbl_etiqueta_plugins)

        ruta_plugins_detectada = obtener_ruta_plugins_ats()
        ruta_plugins_actual = config.get("custom_plugins_dir", ruta_plugins_detectada)
        texto_plugins = ruta_plugins_actual if ruta_plugins_actual else "No detectada (Configura la ubicación del juego)"
        color_texto_plugins = "#CCCCCC" if ruta_plugins_actual else "#E74C3C"

        self.lbl_ruta_plugins = QLineEdit(texto_plugins)
        self.lbl_ruta_plugins.setReadOnly(True)
        self.lbl_ruta_plugins.setFixedHeight(35)
        self.lbl_ruta_plugins.setToolTip(texto_plugins)
        self.lbl_ruta_plugins.setCursorPosition(0)
        self.lbl_ruta_plugins.setStyleSheet(
            f"color: {color_texto_plugins}; font-size: 13px; font-weight: 600; background: #1E1E1E; padding: 0 10px; border-radius: 4px; border: 1px solid #3E3E3E;")
        fila_plugins.addWidget(self.lbl_ruta_plugins, 1)

        self.btn_cambiar_plugins = QPushButton("Cambiar")
        self.btn_cambiar_plugins.setFixedSize(90, 35)
        self.btn_cambiar_plugins.setCursor(Qt.PointingHandCursor)
        self.btn_cambiar_plugins.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: white; border: 1px solid #555555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #3E3E3E; border-color: #2980B9; } QPushButton:pressed { background-color: #1E1E1E; }")
        self.btn_cambiar_plugins.clicked.connect(self.action_cambiar_carpeta_plugins)
        fila_plugins.addWidget(self.btn_cambiar_plugins)

        self.btn_abrir_plugins = QPushButton("Abrir Carpeta")
        self.btn_abrir_plugins.setFixedSize(100, 35)
        self.btn_abrir_plugins.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_plugins.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: #2ECC71; border: 1px solid #27AE60; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #27AE60; color: white; border-color: #2ECC71; }")
        self.btn_abrir_plugins.clicked.connect(self.action_abrir_carpeta_plugins)
        fila_plugins.addWidget(self.btn_abrir_plugins)

        layout_tarjeta.addLayout(fila_plugins)

        # --- Línea divisoria ---
        linea3 = QWidget()
        linea3.setFixedHeight(1)
        linea3.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea3)
        self.lineas_divisorias.append(linea3)

        # ==========================================
        # FILA: UBICACIÓN DEL JUEGO (amtrucks.exe)
        # ==========================================
        fila_exe = QHBoxLayout()
        fila_exe.setSpacing(15)

        self.lbl_etiqueta_exe = QLabel("Ubicación\ndel Juego")
        self.lbl_etiqueta_exe.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_exe.setFixedWidth(110)
        self.lbl_etiqueta_exe.setWordWrap(True)
        fila_exe.addWidget(self.lbl_etiqueta_exe)

        exe_actual = obtener_ruta_exe_ats()
        texto_exe = exe_actual if exe_actual else "No detectado (Selecciona amtrucks.exe manualmente)"
        color_texto_exe = "#CCCCCC" if exe_actual else "#E74C3C"

        self.lbl_ruta_exe = QLineEdit(texto_exe)
        self.lbl_ruta_exe.setReadOnly(True)
        self.lbl_ruta_exe.setFixedHeight(35)
        self.lbl_ruta_exe.setToolTip(texto_exe)
        self.lbl_ruta_exe.setCursorPosition(0)
        self.lbl_ruta_exe.setStyleSheet(
            f"color: {color_texto_exe}; font-size: 13px; font-weight: 600; background: #1E1E1E; padding: 0 10px; border-radius: 4px; border: 1px solid #3E3E3E;")
        fila_exe.addWidget(self.lbl_ruta_exe, 1)

        self.btn_cambiar_exe = QPushButton("Buscar EXE")
        self.btn_cambiar_exe.setFixedSize(90, 35)
        self.btn_cambiar_exe.setCursor(Qt.PointingHandCursor)
        self.btn_cambiar_exe.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: white; border: 1px solid #555555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #3E3E3E; border-color: #2980B9; } QPushButton:pressed { background-color: #1E1E1E; }"
        )
        self.btn_cambiar_exe.clicked.connect(self.action_cambiar_exe_juego)
        fila_exe.addWidget(self.btn_cambiar_exe)

        self.btn_restablecer_exe = QPushButton("Restablecer")
        self.btn_restablecer_exe.setFixedSize(100, 35)
        self.btn_restablecer_exe.setCursor(Qt.PointingHandCursor)
        self.btn_restablecer_exe.setStyleSheet(
            "QPushButton { background-color: #2B2B2B; color: #E74C3C; border: 1px solid #C0392B; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #C0392B; color: white; border-color: #E74C3C; }"
        )
        self.btn_restablecer_exe.clicked.connect(self.action_restablecer_exe_juego)
        fila_exe.addWidget(self.btn_restablecer_exe)

        layout_tarjeta.addLayout(fila_exe)

        # --- Línea divisoria ---
        linea4 = QWidget()
        linea4.setFixedHeight(1)
        linea4.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea4)
        self.lineas_divisorias.append(linea4)

        # ==========================================
        # FILA: TEMA + IDIOMA (lado a lado)
        # ==========================================
        fila_tema_idioma = QHBoxLayout()
        fila_tema_idioma.setSpacing(25)

        # --- Columna: Tema ---
        col_tema = QHBoxLayout()
        col_tema.setSpacing(12)
        self.lbl_etiqueta_tema = QLabel("Tema del\nLauncher")
        self.lbl_etiqueta_tema.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_tema.setFixedWidth(85)
        self.lbl_etiqueta_tema.setWordWrap(True)
        col_tema.addWidget(self.lbl_etiqueta_tema)

        self.combo_tema = QComboBox()
        self.combo_tema.setFixedHeight(40)
        self.combo_tema.setCursor(Qt.PointingHandCursor)
        self.combo_tema.setIconSize(QSize(20, 20))
        for nombre in TEMAS.keys():
            self.combo_tema.addItem(crear_icono_tema(nombre, 20), tr(nombre), userData=nombre)

        tema_actual = obtener_nombre_tema_actual()
        for i in range(self.combo_tema.count()):
            if self.combo_tema.itemData(i) == tema_actual:
                self.combo_tema.setCurrentIndex(i)
                break
        self.combo_tema.currentIndexChanged.connect(self.action_cambiar_tema)

        def _al_presionar_item_tema(model_index):
            if not model_index.isValid():
                return
            idx = model_index.row()
            self.combo_tema.hidePopup()
            if self.combo_tema.currentIndex() != idx:
                self.combo_tema.setCurrentIndex(idx)

        self.combo_tema.view().pressed.connect(_al_presionar_item_tema)
        col_tema.addWidget(self.combo_tema, 1)

        # --- Columna: Idioma ---
        col_idioma = QHBoxLayout()
        col_idioma.setSpacing(12)
        self.lbl_etiqueta_idioma = QLabel("Idioma del\nLauncher")
        self.lbl_etiqueta_idioma.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_idioma.setFixedWidth(85)
        self.lbl_etiqueta_idioma.setWordWrap(True)
        col_idioma.addWidget(self.lbl_etiqueta_idioma)

        self.combo_idioma = QComboBox()
        self.combo_idioma.setFixedHeight(40)
        self.combo_idioma.setCursor(Qt.PointingHandCursor)
        for codigo, datos in IDIOMAS.items():
            self.combo_idioma.addItem(datos["etiqueta"], codigo)

        idioma_actual = obtener_idioma_actual()
        for i in range(self.combo_idioma.count()):
            if self.combo_idioma.itemData(i) == idioma_actual:
                self.combo_idioma.setCurrentIndex(i)
                break

        def _al_presionar_item_idioma(model_index):
            if not model_index.isValid():
                return
            idx = model_index.row()
            self.combo_idioma.hidePopup()
            if self.combo_idioma.currentIndex() != idx:
                self.combo_idioma.setCurrentIndex(idx)

        self.combo_idioma.view().pressed.connect(_al_presionar_item_idioma)
        self.combo_idioma.currentIndexChanged.connect(self.action_cambiar_idioma)
        col_idioma.addWidget(self.combo_idioma, 1)

        fila_tema_idioma.addLayout(col_tema, 1)
        fila_tema_idioma.addLayout(col_idioma, 1)
        layout_tarjeta.addLayout(fila_tema_idioma)

        # --- Línea divisoria ---
        linea5 = QWidget()
        linea5.setFixedHeight(1)
        linea5.setStyleSheet("background-color: #444444;")
        layout_tarjeta.addWidget(linea5)
        self.lineas_divisorias.append(linea5)

        # ==========================================
        # FILA: TÉRMINOS Y CONDICIONES
        # ==========================================
        fila_terminos = QHBoxLayout()
        fila_terminos.setSpacing(15)

        self.lbl_etiqueta_terminos = QLabel("Términos y\nCondiciones")
        self.lbl_etiqueta_terminos.setStyleSheet(
            "color: white; font-weight: bold; font-size: 13px; background: transparent;")
        self.lbl_etiqueta_terminos.setFixedWidth(110)
        self.lbl_etiqueta_terminos.setWordWrap(True)
        fila_terminos.addWidget(self.lbl_etiqueta_terminos)

        self.lbl_desc_terminos = QLabel(tr(
            "Consulta los términos de servicio, política de uso de mods y descargo de responsabilidad legal del launcher."
        ))
        self.lbl_desc_terminos.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent;")
        self.lbl_desc_terminos.setWordWrap(True)
        fila_terminos.addWidget(self.lbl_desc_terminos, 1)

        self.btn_ver_terminos = QPushButton("📜  Ver Términos")
        self.btn_ver_terminos.setFixedSize(140, 35)
        self.btn_ver_terminos.setCursor(Qt.PointingHandCursor)
        self.btn_ver_terminos.clicked.connect(self.action_ver_terminos)
        fila_terminos.addWidget(self.btn_ver_terminos)

        layout_tarjeta.addLayout(fila_terminos)

        diseño.addWidget(tarjeta)
        diseño.addStretch()

        self.actualizar_estilo_tema()
        self.actualizar_textos_idioma()

    # ==========================================
    # ACCIONES
    # ==========================================
    def _actualizar_campo_ruta(self, campo: QLineEdit, texto: str):
        campo.setText(texto)
        campo.setToolTip(texto)
        campo.setCursorPosition(0)
        self.actualizar_estilo_tema()

    def action_cambiar_carpeta_mod(self):
        ruta_actual = obtener_ruta_ats("mod")
        directorio_nuevo = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Mods de ATS", ruta_actual)

        if directorio_nuevo:
            directorio_nuevo = os.path.normpath(directorio_nuevo)
            config = cargar_config_usuario()
            config["custom_mod_dir"] = directorio_nuevo
            guardar_config_usuario(config)
            self._actualizar_campo_ruta(self.lbl_ruta_mod, directorio_nuevo)
            self.main_window.recargar_interfaz()

    def action_abrir_carpeta_mod(self):
        ruta_folder = self.lbl_ruta_mod.text()
        if not os.path.exists(ruta_folder):
            os.makedirs(ruta_folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta_folder))

    def action_cambiar_carpeta_screen(self):
        ruta_actual = self.lbl_ruta_screen.text()
        directorio_nuevo = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Fotos de ATS", ruta_actual)

        if directorio_nuevo:
            directorio_nuevo = os.path.normpath(directorio_nuevo)
            config = cargar_config_usuario()
            config["custom_screenshot_dir"] = directorio_nuevo
            guardar_config_usuario(config)
            self._actualizar_campo_ruta(self.lbl_ruta_screen, directorio_nuevo)

    def action_abrir_carpeta_screen(self):
        ruta_folder = self.lbl_ruta_screen.text()
        if not os.path.exists(ruta_folder):
            os.makedirs(ruta_folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta_folder))

    def action_cambiar_carpeta_plugins(self):
        ruta_actual = self.lbl_ruta_plugins.text()
        dir_inicial = ruta_actual if os.path.exists(ruta_actual) else ""
        directorio_nuevo = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Plugins de ATS", dir_inicial)

        if directorio_nuevo:
            directorio_nuevo = os.path.normpath(directorio_nuevo)
            config = cargar_config_usuario()
            config["custom_plugins_dir"] = directorio_nuevo
            guardar_config_usuario(config)
            self._actualizar_campo_ruta(self.lbl_ruta_plugins, directorio_nuevo)

    def action_abrir_carpeta_plugins(self):
        ruta_folder = self.lbl_ruta_plugins.text()
        if not ruta_folder or ruta_folder.startswith("No detectada"):
            QMessageBox.warning(
                self, "Carpeta no configurada",
                "Primero debes seleccionar la ubicación del ejecutable amtrucks.exe o elegir la carpeta de plugins manualmente."
            )
            return
        if not os.path.exists(ruta_folder):
            os.makedirs(ruta_folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta_folder))

    def action_cambiar_exe_juego(self):
        exe_actual = obtener_ruta_exe_ats()
        dir_inicial = os.path.dirname(exe_actual) if exe_actual and os.path.exists(exe_actual) else ""

        archivo_nuevo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar ejecutable de ATS (amtrucks.exe)",
            dir_inicial,
            "Ejecutable del Juego (*.exe)"
        )

        if archivo_nuevo:
            archivo_nuevo = os.path.normpath(archivo_nuevo)
            config = cargar_config_usuario()
            config["custom_game_exe"] = archivo_nuevo
            guardar_config_usuario(config)
            self._actualizar_campo_ruta(self.lbl_ruta_exe, archivo_nuevo)

            if "custom_plugins_dir" not in config:
                dir_plugins_nuevo = os.path.normpath(os.path.join(os.path.dirname(archivo_nuevo), "plugins"))
                self._actualizar_campo_ruta(self.lbl_ruta_plugins, dir_plugins_nuevo)

    def action_restablecer_exe_juego(self):
        config = cargar_config_usuario()
        if "custom_game_exe" in config:
            del config["custom_game_exe"]
            guardar_config_usuario(config)
        exe_detectado = obtener_ruta_exe_ats()
        if exe_detectado:
            self._actualizar_campo_ruta(self.lbl_ruta_exe, exe_detectado)
        else:
            self._actualizar_campo_ruta(self.lbl_ruta_exe, "No detectado (Selecciona amtrucks.exe manualmente)")

        if "custom_plugins_dir" not in config:
            ruta_p = obtener_ruta_plugins_ats()
            if ruta_p:
                self._actualizar_campo_ruta(self.lbl_ruta_plugins, ruta_p)
            else:
                self._actualizar_campo_ruta(self.lbl_ruta_plugins, "No detectada (Configura la ubicación del juego)")

    def action_cambiar_tema(self, idx_o_nombre):
        if isinstance(idx_o_nombre, int):
            if idx_o_nombre < 0:
                return
            nombre_tema = self.combo_tema.itemData(idx_o_nombre)
        else:
            nombre_tema = idx_o_nombre
        if not nombre_tema:
            return
        guardar_tema_actual(nombre_tema)
        if hasattr(self.main_window, "aplicar_tema"):
            # Se difiere un instante para que el combo cierre su popup
            # antes de re-aplicar el estilo global.
            QTimer.singleShot(25, lambda n=nombre_tema: self.main_window.aplicar_tema(n))

    def action_cambiar_idioma(self, idx: int):
        codigo = self.combo_idioma.itemData(idx)
        if not codigo:
            return
        guardar_idioma_actual(codigo)
        self.actualizar_textos_idioma()
        if hasattr(self.main_window, "actualizar_textos_idioma"):
            self.main_window.actualizar_textos_idioma()

    def action_restablecer_tema(self):
        for i in range(self.combo_tema.count()):
            if self.combo_tema.itemData(i) == TEMA_POR_DEFECTO:
                self.combo_tema.setCurrentIndex(i)
                return

    def action_ver_terminos(self):
        if hasattr(self.main_window, "abrir_modal_terminos"):
            pos_btn = self.btn_ver_terminos.mapTo(self.main_window, QPoint(0, 0))
            self.main_window.abrir_modal_terminos(pos_btn)

    def actualizar_textos_idioma(self):
        """Actualiza todos los textos visuales de la página de configuración según el idioma activo."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("CONFIGURACIÓN DEL LAUNCHER"))
        if hasattr(self, "lbl_etiqueta_mod"):
            self.lbl_etiqueta_mod.setText(tr("Carpeta Mod"))
        if hasattr(self, "btn_cambiar_mod"):
            self.btn_cambiar_mod.setText(tr("Cambiar"))
        if hasattr(self, "btn_abrir_mod"):
            self.btn_abrir_mod.setText(tr("Abrir Carpeta"))

        if hasattr(self, "lbl_etiqueta_screen"):
            self.lbl_etiqueta_screen.setText(tr("Carpeta de\nFotos"))
        if hasattr(self, "btn_cambiar_screen"):
            self.btn_cambiar_screen.setText(tr("Cambiar"))
        if hasattr(self, "btn_abrir_screen"):
            self.btn_abrir_screen.setText(tr("Abrir Carpeta"))

        if hasattr(self, "lbl_etiqueta_plugins"):
            self.lbl_etiqueta_plugins.setText(tr("Carpeta de\nPlugins"))
        if hasattr(self, "btn_cambiar_plugins"):
            self.btn_cambiar_plugins.setText(tr("Cambiar"))
        if hasattr(self, "btn_abrir_plugins"):
            self.btn_abrir_plugins.setText(tr("Abrir Carpeta"))

        if hasattr(self, "lbl_etiqueta_exe"):
            self.lbl_etiqueta_exe.setText(tr("Ubicación\ndel Juego"))
        if hasattr(self, "btn_cambiar_exe"):
            self.btn_cambiar_exe.setText(tr("Buscar EXE"))
        if hasattr(self, "btn_restablecer_exe"):
            self.btn_restablecer_exe.setText(tr("Restablecer"))

        if hasattr(self, "lbl_etiqueta_tema"):
            self.lbl_etiqueta_tema.setText(tr("Tema del\nLauncher"))
        if hasattr(self, "combo_tema"):
            self.combo_tema.blockSignals(True)
            for i in range(self.combo_tema.count()):
                key = self.combo_tema.itemData(i)
                if key:
                    self.combo_tema.setItemText(i, tr(key))
            self.combo_tema.blockSignals(False)
        if hasattr(self, "lbl_etiqueta_idioma"):
            self.lbl_etiqueta_idioma.setText(tr("Idioma del\nLauncher"))

        if hasattr(self, "lbl_etiqueta_terminos"):
            self.lbl_etiqueta_terminos.setText(tr("Términos y\nCondiciones"))
        if hasattr(self, "lbl_desc_terminos"):
            self.lbl_desc_terminos.setText(tr("Consulta los términos de servicio, política de uso de mods y descargo de responsabilidad legal del launcher."))
        if hasattr(self, "btn_ver_terminos"):
            self.btn_ver_terminos.setText(tr("📜  Ver Términos"))

    def actualizar_estilo_tema(self):
        """Aplica la paleta de colores del tema activo a las etiquetas, líneas y botones de configuración."""
        from temas import obtener_tema_actual
        tema = obtener_tema_actual()
        fondo_input = tema.get("fondo_input", "#1E1E1E")
        borde_tarjeta = tema.get("borde_tarjeta", "#262932")
        borde_suave = tema.get("borde_suave", "#1F222A")
        acento = tema.get("acento", "#E5A93C")
        contraste = tema.get("contraste", "#0F172A")
        borde_osc = tema.get("borde_oscuro", "#C58922")
        fondo_boton = tema.get("fondo_boton_menu", "#181A20")
        fondo_hover = tema.get("fondo_boton_hover", "#232731")

        for lbl in (getattr(self, "lbl_ruta_mod", None),
                    getattr(self, "lbl_ruta_screen", None),
                    getattr(self, "lbl_ruta_plugins", None),
                    getattr(self, "lbl_ruta_exe", None)):
            if lbl:
                color_txt = "#E74C3C" if "No detectad" in lbl.text() else "#CCCCCC"
                lbl.setStyleSheet(f"""
                    QLineEdit {{
                        color: {color_txt};
                        font-size: 13px;
                        font-weight: 600;
                        background: {fondo_input};
                        padding: 0 10px;
                        border-radius: 4px;
                        border: 1px solid {borde_tarjeta};
                        selection-background-color: {acento};
                        selection-color: {contraste};
                    }}
                    QLineEdit:focus {{
                        border: 1px solid {acento};
                    }}
                """)

        for linea in getattr(self, "lineas_divisorias", []):
            linea.setStyleSheet(f"background-color: {borde_suave};")

        if hasattr(self, "btn_restablecer_tema"):
            self.btn_restablecer_tema.setStyleSheet(
                f"QPushButton {{ background-color: {fondo_boton}; color: {acento}; border: 1px solid {borde_osc}; border-radius: 4px; font-size: 12px; font-weight: bold; }} QPushButton:hover {{ background-color: {fondo_hover}; color: #FFFFFF; border-color: {acento}; }}")

        if hasattr(self, "btn_ver_terminos"):
            self.btn_ver_terminos.setStyleSheet(
                f"QPushButton {{ background-color: {fondo_boton}; color: {acento}; border: 1px solid {borde_osc}; border-radius: 4px; font-size: 12px; font-weight: bold; }} QPushButton:hover {{ background-color: {fondo_hover}; color: #FFFFFF; border-color: {acento}; }}")

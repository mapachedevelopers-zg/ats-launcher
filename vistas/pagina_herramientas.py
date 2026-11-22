import os
import re
import requests
from constantes import URL_EMISORAS_GITHUB
import hashlib
import threading
import zipfile
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
    QHBoxLayout, QGridLayout, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from utils import aplicar_sombra, modificar_config_ats, leer_config_ats, obtener_ruta_ats
from download_manager import obtener_datos_servidor, esta_juego_ejecutandose
from i18n import tr


class SeñalesHerramientas(QObject):
    resultado_emisoras = Signal(bool, str)
    estado_verificacion_emisoras = Signal(bool)


class PaginaHerramientas(QWidget):
    def __init__(self):
        super().__init__()
        self._tarjetas_herramientas = []
        self.señales = SeñalesHerramientas()
        self.señales.resultado_emisoras.connect(self._fin_descarga_emisoras)
        self.señales.estado_verificacion_emisoras.connect(self._actualizar_estado_emisoras)

        # Área con scroll para todas las herramientas
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        contenedor = QWidget()
        layout_contenedor = QVBoxLayout(contenedor)
        layout_contenedor.setContentsMargins(40, 25, 40, 30)
        layout_contenedor.setSpacing(20)

        # Título
        self.titulo = QLabel(tr("HERRAMIENTAS Y CONFIGURACIÓN ATS"))
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignCenter)
        layout_contenedor.addWidget(self.titulo)

        # Cuadrícula de herramientas
        grid_herramientas = QGridLayout()
        grid_herramientas.setSpacing(16)

        # 1. Buffer Page Size
        self.btn_buffer = QPushButton("AJUSTAR")
        self.btn_buffer.clicked.connect(self.action_ajustar_buffer)
        card_buffer = self._crear_tarjeta_herramienta(
            "💾 Buffer Page Size",
            "Ajusta la memoria de renderizado a 10 para evitar tirones con mods pesados.",
            self.btn_buffer
        )
        grid_herramientas.addWidget(card_buffer, 0, 0)

        # 2. Consola de comandos
        self.btn_consola = QPushButton("ACTIVAR")
        self.btn_consola.clicked.connect(self.action_activar_consola)
        card_consola = self._crear_tarjeta_herramienta(
            "💻 Consola de Comandos",
            "Habilita la tecla (~) dentro del juego para ejecutar comandos de desarrollador.",
            self.btn_consola
        )
        grid_herramientas.addWidget(card_consola, 0, 1)

        # 3. Cámara libre
        self.btn_camara0 = QPushButton("ACTIVAR")
        self.btn_camara0.clicked.connect(self.action_activar_camara0)
        card_camara0 = self._crear_tarjeta_herramienta(
            "🎥 Cámara Libre (Cámara 0)",
            "Permite volar con el teclado numérico y teletransportar tu camión en el mapa.",
            self.btn_camara0
        )
        grid_herramientas.addWidget(card_camara0, 1, 0)

        # 4. Convoy 128 jugadores
        self.btn_servidores128 = QPushButton("ACTIVAR")
        self.btn_servidores128.clicked.connect(self.action_activar_servidores128)

        card_convoy = self._crear_tarjeta_herramienta(
            "🚛 Convoy 128 Jugadores",
            "Expande el límite predeterminado del modo multijugador Convoy hasta 128 slots.",
            self.btn_servidores128
        )
        grid_herramientas.addWidget(card_convoy, 1, 1)

        # 5. Emisoras colombianas
        self.btn_emisoras = QPushButton("VERIFICANDO...")
        self.btn_emisoras.setEnabled(False)
        self.btn_emisoras.clicked.connect(self.action_instalar_emisoras)
        card_emisoras = self._crear_tarjeta_herramienta(
            "📻 Emisoras Colombianas",
            "Instala la lista actualizada de radios en vivo colombianas en la radio de la cabina.",
            self.btn_emisoras
        )
        grid_herramientas.addWidget(card_emisoras, 2, 0)

        # 6. Densidad de tráfico (contador)
        card_trafico = self._crear_tarjeta_trafico_contador()
        grid_herramientas.addWidget(card_trafico, 2, 1)

        # 7. Filtros de mods en Convoy
        self.btn_filtros_convoy = QPushButton("ACTIVAR")
        self.btn_filtros_convoy.clicked.connect(self.action_activar_filtros_convoy)
        card_filtros = self._crear_tarjeta_herramienta(
            "🌐 Activar filtro de mods y mods opcionales",
            "Permite encontrar y unirse a servidores de Convoy con mods, admitiendo además mods opcionales individuales según lo permita la sesión.",
            self.btn_filtros_convoy
        )
        grid_herramientas.addWidget(card_filtros, 3, 0)

        # 8. Respaldo de perfiles
        card_backup = self._crear_tarjeta_backup_perfiles()
        grid_herramientas.addWidget(card_backup, 3, 1)

        layout_contenedor.addLayout(grid_herramientas)
        layout_contenedor.addStretch()
        scroll.setWidget(contenedor)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.addWidget(scroll)

        self._verificar_estados_iniciales()

    def _crear_tarjeta_herramienta(self, titulo, descripcion, boton_accion):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        tarjeta.setFixedHeight(125)
        aplicar_sombra(tarjeta)

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        lbl_titulo = QLabel(tr(titulo))
        lbl_titulo.setStyleSheet(
            "color: #F8FAFC; font-size: 14px; font-weight: 800; background: transparent;")

        lbl_desc = QLabel(tr(descripcion))
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;")

        fila_inferior = QHBoxLayout()
        fila_inferior.addStretch()

        boton_accion.setFixedSize(125, 32)
        boton_accion.setCursor(Qt.PointingHandCursor)
        boton_accion.setProperty("texto_inicial", boton_accion.text())
        boton_accion.setText(tr(boton_accion.text()))
        fila_inferior.addWidget(boton_accion)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_desc)
        layout.addLayout(fila_inferior)

        self._tarjetas_herramientas.append({
            "lbl_titulo": lbl_titulo,
            "lbl_desc": lbl_desc,
            "titulo": titulo,
            "desc": descripcion,
            "btn": boton_accion,
        })

        return tarjeta

    def _crear_tarjeta_trafico_contador(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        tarjeta.setFixedHeight(125)
        aplicar_sombra(tarjeta)

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(6)

        self.lbl_tit_trafico = QLabel(tr("🚦 Densidad de Tráfico (0 a 10)"))
        self.lbl_tit_trafico.setStyleSheet(
            "color: #F8FAFC; font-size: 14px; font-weight: 800; background: transparent;")

        self.lbl_desc_trafico = QLabel(tr("Ajusta el nivel de densidad vehicular en las carreteras:"))
        self.lbl_desc_trafico.setWordWrap(True)
        self.lbl_desc_trafico.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;")

        fila_control = QHBoxLayout()
        fila_control.setSpacing(8)

        btn_menos = QPushButton("−")
        btn_menos.setFixedSize(32, 32)
        btn_menos.setCursor(Qt.PointingHandCursor)
        btn_menos.setStyleSheet("""
            QPushButton {
                background: #232731; color: #F8FAFC; font-weight: 900; font-size: 16px;
                border: 1px solid #334155; border-radius: 4px;
            }
            QPushButton:hover { background: #E74C3C; border-color: #FF6B6B; }
        """)
        btn_menos.clicked.connect(lambda: self._modificar_valor_trafico_ui(-1))

        valor_config = leer_config_ats("g_traffic") or "1"
        try:
            val_int = int(float(valor_config))
        except ValueError:
            val_int = 1

        self.input_num_trafico = QLineEdit(str(max(0, min(10, val_int))))
        self.input_num_trafico.setFixedSize(45, 32)
        self.input_num_trafico.setAlignment(Qt.AlignCenter)
        self.input_num_trafico.setReadOnly(True)
        self.input_num_trafico.setStyleSheet("""
            QLineEdit {
                background: #11161B; color: #E5A93C; font-weight: 900; font-size: 15px;
                border: 1px solid #262932; border-radius: 4px;
            }
        """)

        btn_mas = QPushButton("+")
        btn_mas.setFixedSize(32, 32)
        btn_mas.setCursor(Qt.PointingHandCursor)
        btn_mas.setStyleSheet("""
            QPushButton {
                background: #232731; color: #F8FAFC; font-weight: 900; font-size: 16px;
                border: 1px solid #334155; border-radius: 4px;
            }
            QPushButton:hover { background: #27AE60; border-color: #2ECC71; }
        """)
        btn_mas.clicked.connect(lambda: self._modificar_valor_trafico_ui(1))

        self.btn_aplicar_trafico = QPushButton(tr("APLICAR"))
        self.btn_aplicar_trafico.setFixedSize(125, 32)
        self.btn_aplicar_trafico.setCursor(Qt.PointingHandCursor)
        self.btn_aplicar_trafico.clicked.connect(self.action_ajustar_trafico)

        fila_control.addWidget(btn_menos)
        fila_control.addWidget(self.input_num_trafico)
        fila_control.addWidget(btn_mas)
        fila_control.addStretch()
        fila_control.addWidget(self.btn_aplicar_trafico)

        layout.addWidget(self.lbl_tit_trafico)
        layout.addWidget(self.lbl_desc_trafico)
        layout.addLayout(fila_control)

        return tarjeta

    def _crear_tarjeta_backup_perfiles(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        tarjeta.setFixedHeight(125)
        aplicar_sombra(tarjeta)

        layout = QHBoxLayout(tarjeta)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        # --- Columna izquierda: textos ---
        col_izq = QVBoxLayout()
        col_izq.setSpacing(4)

        self.lbl_tit_backup = QLabel(tr("💾 Respaldo de Perfiles"))
        self.lbl_tit_backup.setStyleSheet(
            "color: #F8FAFC; font-size: 14px; font-weight: 800; background: transparent;")

        self.lbl_desc_backup = QLabel(tr("Copia de seguridad en archivo .zip de todos los perfiles locales."))
        self.lbl_desc_backup.setWordWrap(True)
        self.lbl_desc_backup.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background: transparent;")

        self.lbl_ruta_backup_info = QLabel(tr("Sin copias de seguridad creadas aún."))
        self.lbl_ruta_backup_info.setWordWrap(True)
        self.lbl_ruta_backup_info.setStyleSheet(
            "color: #94A3B8; font-size: 10px; font-weight: 600; background: transparent;")

        col_izq.addWidget(self.lbl_tit_backup)
        col_izq.addWidget(self.lbl_desc_backup)
        col_izq.addWidget(self.lbl_ruta_backup_info)
        col_izq.addStretch()

        # --- Columna derecha: botones tipo enlace ---
        col_der = QVBoxLayout()
        col_der.setSpacing(2)
        col_der.setAlignment(Qt.AlignVCenter)

        estilo_base = """
            QPushButton {
                background: transparent; border: none; text-align: left;
                font-size: 11px; font-weight: 700; padding: 2px 0px;
            }
            QPushButton:hover { text-decoration: underline; }
            QPushButton:disabled { color: #475569 !important; }
        """

        self.btn_crear_backup = QPushButton(tr("+ Crear Backup"))
        self.btn_crear_backup.setCursor(Qt.PointingHandCursor)
        self.btn_crear_backup.setStyleSheet(
            estilo_base + "QPushButton { color: #34D399; } QPushButton:hover { color: #6EE7B7; }")
        self.btn_crear_backup.clicked.connect(self.action_crear_backup_perfiles)

        self.btn_restaurar = QPushButton("↻ " + tr("Restaurar Copia"))
        self.btn_restaurar.setCursor(Qt.PointingHandCursor)
        self.btn_restaurar.setStyleSheet(
            estilo_base + "QPushButton { color: #60A5FA; } QPushButton:hover { color: #93C5FD; }")
        self.btn_restaurar.clicked.connect(self.action_restaurar_backup_perfiles)

        self.btn_borrar = QPushButton("🗑 " + tr("Eliminar Copia"))
        self.btn_borrar.setCursor(Qt.PointingHandCursor)
        self.btn_borrar.setStyleSheet(
            estilo_base + "QPushButton { color: #F87171; } QPushButton:hover { color: #FCA5A5; }")
        self.btn_borrar.clicked.connect(self.action_eliminar_backup_perfiles)

        self.btn_abrir_backup = QPushButton("📁 " + tr("Abrir Carpeta"))
        self.btn_abrir_backup.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_backup.setStyleSheet(
            estilo_base + "QPushButton { color: #FBBF24; } QPushButton:hover { color: #FDE68A; }")
        self.btn_abrir_backup.clicked.connect(self.action_abrir_carpeta_backups)

        col_der.addWidget(self.btn_crear_backup)
        col_der.addWidget(self.btn_restaurar)
        col_der.addWidget(self.btn_borrar)
        col_der.addWidget(self.btn_abrir_backup)

        layout.addLayout(col_izq, 1)
        layout.addLayout(col_der, 0)

        self._actualizar_botones_backup()
        return tarjeta

    def _obtener_directorio_backups(self) -> str:
        appdata = os.environ.get("APPDATA")
        if appdata:
            dir_b = os.path.join(appdata, "ATS_Launcher", "Backups")
        else:
            dir_b = os.path.expanduser("~/.ats_launcher/Backups")
        os.makedirs(dir_b, exist_ok=True)
        return os.path.normpath(dir_b)

    def _obtener_ultimo_backup(self) -> str | None:
        dir_b = self._obtener_directorio_backups()
        if not os.path.exists(dir_b):
            return None
        zips = [
            os.path.join(dir_b, f) for f in os.listdir(dir_b)
            if f.lower().endswith(".zip") and os.path.isfile(os.path.join(dir_b, f))
        ]
        if not zips:
            return None
        zips.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return zips[0]

    def _actualizar_botones_backup(self):
        ultimo = self._obtener_ultimo_backup()
        hay_backup = bool(ultimo and os.path.exists(ultimo))
        self.btn_restaurar.setEnabled(hay_backup)
        self.btn_borrar.setEnabled(hay_backup)
        self.btn_restaurar.setCursor(Qt.PointingHandCursor if hay_backup else Qt.ArrowCursor)
        self.btn_borrar.setCursor(Qt.PointingHandCursor if hay_backup else Qt.ArrowCursor)
        if hay_backup:
            nom_zip = os.path.basename(ultimo)
            tam_mb = os.path.getsize(ultimo) / (1024 * 1024)
            self.lbl_ruta_backup_info.setText(f"{tr('Último:')} {nom_zip} ({tam_mb:.1f} MB)")
            self.lbl_ruta_backup_info.setStyleSheet(
                "color: #34D399; font-size: 10px; font-weight: 600; background: transparent;")
        else:
            self.lbl_ruta_backup_info.setText(tr("Sin copias de seguridad creadas aún."))
            self.lbl_ruta_backup_info.setStyleSheet(
                "color: #94A3B8; font-size: 10px; font-weight: 600; background: transparent;")

    def action_crear_backup_perfiles(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Por favor cierra American Truck Simulator antes de realizar una copia de seguridad."
            )
            return

        dir_profiles = os.path.join(obtener_ruta_ats(""), "profiles")
        if not os.path.exists(dir_profiles):
            QMessageBox.warning(self, "Atención", "No se encontró la carpeta 'profiles' de ATS.")
            return

        dir_dest = self._obtener_directorio_backups()
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_path = os.path.join(dir_dest, f"Backup_Perfiles_{stamp}.zip")
        zip_tmp = f"{zip_path}.tmp"

        self.btn_crear_backup.setEnabled(False)
        self.btn_crear_backup.setText("Comprimiendo...")
        self.btn_restaurar.setEnabled(False)
        self.btn_borrar.setEnabled(False)

        def _hilo_comprimir():
            exito = False
            msg_error = ""
            try:
                with zipfile.ZipFile(zip_tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
                    for root, dirs, files in os.walk(dir_profiles):
                        for file in files:
                            full = os.path.join(root, file)
                            rel = os.path.relpath(full, dir_profiles)
                            z.write(full, rel)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                os.replace(zip_tmp, zip_path)
                exito = True
            except Exception as e:
                msg_error = str(e)
                if os.path.exists(zip_tmp):
                    try:
                        os.remove(zip_tmp)
                    except Exception:
                        pass

            def _finalizar():
                self.btn_crear_backup.setEnabled(True)
                self.btn_crear_backup.setText("+ Crear Backup")
                self._actualizar_botones_backup()
                if exito:
                    QMessageBox.information(
                        self, "Copia de Seguridad Creada",
                        f"Se creó correctamente la copia de seguridad de todos tus perfiles locales en:\n\n{zip_path}"
                    )
                else:
                    QMessageBox.critical(
                        self, "Error",
                        f"No se pudo crear el archivo de respaldo: {msg_error}"
                    )

            QTimer.singleShot(0, _finalizar)

        threading.Thread(target=_hilo_comprimir, daemon=True).start()

    def action_restaurar_backup_perfiles(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Por favor cierra American Truck Simulator antes de restaurar una copia de seguridad."
            )
            return

        ultimo = self._obtener_ultimo_backup()
        if not ultimo or not os.path.exists(ultimo):
            QMessageBox.information(self, "Sin copias", "No hay ninguna copia de seguridad guardada.")
            return

        nom_zip = os.path.basename(ultimo)
        resp = QMessageBox.question(
            self, "Confirmar Restauración",
            f"¿Deseas restaurar la copia '{nom_zip}'?\n\n"
            f"⚠️ Los archivos actuales de la carpeta 'profiles' serán reemplazados por los de esta copia.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        dir_profiles = os.path.join(obtener_ruta_ats(""), "profiles")
        try:
            os.makedirs(dir_profiles, exist_ok=True)
            with zipfile.ZipFile(ultimo, "r") as z:
                z.extractall(dir_profiles)

            QMessageBox.information(
                self, "Restauración Exitosa",
                f"Tus perfiles han sido restaurados exitosamente desde:\n{nom_zip}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo restaurar la copia de seguridad: {e}")

    def action_eliminar_backup_perfiles(self):
        ultimo = self._obtener_ultimo_backup()
        if not ultimo or not os.path.exists(ultimo):
            return

        nom_zip = os.path.basename(ultimo)
        resp = QMessageBox.warning(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente la copia de seguridad '{nom_zip}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resp == QMessageBox.Yes:
            try:
                os.remove(ultimo)
                self._actualizar_botones_backup()
                QMessageBox.information(self, "Eliminado", "La copia de seguridad ha sido eliminada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo: {e}")

    def action_abrir_carpeta_backups(self):
        dir_b = self._obtener_directorio_backups()
        QDesktopServices.openUrl(QUrl.fromLocalFile(dir_b))

    def _modificar_valor_trafico_ui(self, delta):
        try:
            val_actual = int(self.input_num_trafico.text())
        except ValueError:
            val_actual = 1

        nuevo_val = max(0, min(10, val_actual + delta))
        self.input_num_trafico.setText(str(nuevo_val))

    def _verificar_estados_iniciales(self):
        if leer_config_ats("g_developer") == "1":
            self._marcar_exito(self.btn_camara0, "ACTIVADO")
        if leer_config_ats("g_console") == "1":
            self._marcar_exito(self.btn_consola, "ACTIVADO")
        if leer_config_ats("g_max_convoy_size") == "128":
            self._marcar_exito(self.btn_servidores128, "ACTIVADO")
        if leer_config_ats("r_buffer_page_size") == "10":
            self._marcar_exito(self.btn_buffer, "AJUSTADO (10)")
        if self._estan_filtros_convoy_activos():
            self._marcar_exito(self.btn_filtros_convoy, "ACTIVADO")

        # La comprobación de las emisoras se hace en segundo plano
        # para no bloquear la interfaz mientras se descarga la lista.
        threading.Thread(target=self._hilo_comparar_emisoras, daemon=True).start()

    def _estan_filtros_convoy_activos(self) -> bool:
        """Verifica si en session_filters.sii están activos los filtros de mods y opcionales."""
        ruta = obtener_ruta_ats("session_filters.sii")
        if not os.path.exists(ruta):
            return False
        try:
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
            modded = re.search(r"show_modded:\s*true", contenido, re.IGNORECASE)
            optional = re.search(r"show_with_optional:\s*true", contenido, re.IGNORECASE)
            return bool(modded and optional)
        except Exception:
            return False

    def _guardar_filtros_convoy(self, activar: bool) -> bool:
        """Modifica o crea session_filters.sii con show_modded y show_with_optional."""
        ruta = obtener_ruta_ats("session_filters.sii")
        val = "true" if activar else "false"
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    contenido = f.read()

                if re.search(r"show_modded:\s*\w+", contenido):
                    contenido = re.sub(r"show_modded:\s*\w+", f"show_modded: {val}", contenido)
                else:
                    contenido = re.sub(r"(session_filters\s*:\s*[^{]+\{)", f"\\1\n show_modded: {val}", contenido)

                if re.search(r"show_with_optional:\s*\w+", contenido):
                    contenido = re.sub(r"show_with_optional:\s*\w+", f"show_with_optional: {val}", contenido)
                else:
                    contenido = re.sub(r"(session_filters\s*:\s*[^{]+\{)", f"\\1\n show_with_optional: {val}", contenido)
            else:
                contenido = f"""SiiNunit
{{
session_filters : _nameless.session_filters {{
 hide_invalid: false
 hide_password_protected: false
 hide_high_latency: false
 show_modded: {val}
 show_with_optional: {val}
 traffic_rule: none
 damage_rule: none
 service_collision_rule: none
 menu_collision_rule: none
 force_speed_limiter_rule: none
 hide_remote_rule: none
 hide_dedicated: none
}}

}}
"""
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            return True
        except Exception as e:
            print(f"[HERRAMIENTAS] Error al guardar session_filters.sii: {e}")
            return False

    def action_activar_filtros_convoy(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de modificar los filtros de Convoy."
            )
            return

        activo = self._estan_filtros_convoy_activos()
        nuevo_estado = not activo
        exito = self._guardar_filtros_convoy(nuevo_estado)
        if exito:
            if nuevo_estado:
                self._efecto_boton_exito(self.btn_filtros_convoy, "¡ACTIVADO!")
            else:
                self.btn_filtros_convoy.setText("ACTIVAR")
                self.btn_filtros_convoy.setProperty("estado", "")
                self.btn_filtros_convoy.style().unpolish(self.btn_filtros_convoy)
                self.btn_filtros_convoy.style().polish(self.btn_filtros_convoy)
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el archivo session_filters.sii.")

    def action_activar_camara0(self):
        modificar_config_ats("g_developer", "1")
        self._efecto_boton_exito(self.btn_camara0, "¡ACTIVADO!")

    def action_activar_consola(self):
        modificar_config_ats("g_console", "1")
        self._efecto_boton_exito(self.btn_consola, "¡ACTIVADO!")

    def action_activar_servidores128(self):
        modificar_config_ats("g_max_convoy_size", "128")
        self._efecto_boton_exito(self.btn_servidores128, "¡ACTIVADO!")

    def action_ajustar_buffer(self):
        modificar_config_ats("r_buffer_page_size", "10")
        self._efecto_boton_exito(self.btn_buffer, "¡AJUSTADO!")

    def action_ajustar_trafico(self):
        valor_elegido = self.input_num_trafico.text()
        modificar_config_ats("g_traffic", valor_elegido)

        self.btn_aplicar_trafico.setText(f"APLICADO ({valor_elegido})")
        self.btn_aplicar_trafico.setStyleSheet("font-size: 11px;")
        self.btn_aplicar_trafico.setProperty("estado", "exito")
        self.btn_aplicar_trafico.style().unpolish(self.btn_aplicar_trafico)
        self.btn_aplicar_trafico.style().polish(self.btn_aplicar_trafico)

        QTimer.singleShot(2000, self._restaurar_boton_trafico)

    def _restaurar_boton_trafico(self):
        self.btn_aplicar_trafico.setText("APLICAR")
        self.btn_aplicar_trafico.setStyleSheet("")
        self.btn_aplicar_trafico.setProperty("estado", "")
        self.btn_aplicar_trafico.style().unpolish(self.btn_aplicar_trafico)
        self.btn_aplicar_trafico.style().polish(self.btn_aplicar_trafico)

    def action_instalar_emisoras(self):
        if esta_juego_ejecutandose():
            QMessageBox.warning(
                self, "Juego en ejecución",
                "Debes cerrar American Truck Simulator antes de instalar las emisoras."
            )
            return

        self.btn_emisoras.setEnabled(False)
        self.btn_emisoras.setText("Descargando...")

        threading.Thread(target=self._hilo_descarga_emisoras, daemon=True).start()

    def _hilo_descarga_emisoras(self):
        try:
            datos_servidor = obtener_datos_servidor() or {}
            url = datos_servidor.get("emisoras_url", URL_EMISORAS_GITHUB)

            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                ruta_docs_ats = obtener_ruta_ats("")
                ruta_destino = os.path.join(ruta_docs_ats, "live_streams.sii")

                with open(ruta_destino, "wb") as f:
                    f.write(resp.content)

                self.señales.resultado_emisoras.emit(True, "¡INSTALADO!")
            else:
                self.señales.resultado_emisoras.emit(False, "ERROR HTTP")
        except Exception as e:
            print(f"[EMISORAS] Error: {e}")
            self.señales.resultado_emisoras.emit(False, "ERROR")

    def _hilo_comparar_emisoras(self):
        try:
            datos_servidor = obtener_datos_servidor() or {}
            url = datos_servidor.get("emisoras_url", URL_EMISORAS_GITHUB)

            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                contenido_remoto = resp.content
                hash_remoto = hashlib.md5(contenido_remoto).hexdigest()

                ruta_local = os.path.join(obtener_ruta_ats(""), "live_streams.sii")

                if os.path.exists(ruta_local):
                    with open(ruta_local, "rb") as f:
                        hash_local = hashlib.md5(f.read()).hexdigest()

                    if hash_remoto == hash_local:
                        self.señales.estado_verificacion_emisoras.emit(True)
                        return

            self.señales.estado_verificacion_emisoras.emit(False)
        except Exception as e:
            print(f"[EMISORAS] Error al verificar online: {e}")
            self.señales.estado_verificacion_emisoras.emit(False)

    def _actualizar_estado_emisoras(self, esta_actualizado):
        if esta_actualizado:
            self._marcar_exito(self.btn_emisoras, "INSTALADO")
        else:
            self.btn_emisoras.setText("INSTALAR")
            self.btn_emisoras.setEnabled(True)
            self.btn_emisoras.setProperty("estado", "")
            self.btn_emisoras.style().unpolish(self.btn_emisoras)
            self.btn_emisoras.style().polish(self.btn_emisoras)

    def _fin_descarga_emisoras(self, exito, mensaje):
        self.btn_emisoras.setText(mensaje)
        if exito:
            self._marcar_exito(self.btn_emisoras, "INSTALADO")
        else:
            self.btn_emisoras.setEnabled(True)

    def _efecto_boton_exito(self, boton, texto_exito):
        boton.setText(texto_exito)
        self._marcar_exito(boton, texto_exito)

    def _marcar_exito(self, boton, texto):
        boton.setProperty("texto_exito", texto)
        boton.setText(tr(texto))
        boton.setProperty("estado", "exito")
        boton.style().unpolish(boton)
        boton.style().polish(boton)

    def actualizar_textos_idioma(self):
        """Actualiza todos los títulos, descripciones y botones de las herramientas según el idioma activo."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("HERRAMIENTAS Y CONFIGURACIÓN ATS"))

        for item in getattr(self, "_tarjetas_herramientas", []):
            item["lbl_titulo"].setText(tr(item["titulo"]))
            item["lbl_desc"].setText(tr(item["desc"]))
            btn = item["btn"]
            if btn.property("estado") == "exito":
                txt = btn.property("texto_exito") or "ACTIVADO"
                btn.setText(tr(txt))
            else:
                txt = btn.property("texto_inicial") or "ACTIVAR"
                btn.setText(tr(txt))

        if hasattr(self, "lbl_tit_trafico"):
            self.lbl_tit_trafico.setText(tr("🚦 Densidad de Tráfico (0 a 10)"))
        if hasattr(self, "lbl_desc_trafico"):
            self.lbl_desc_trafico.setText(tr("Ajusta el nivel de densidad vehicular en las carreteras:"))
        if hasattr(self, "btn_aplicar_trafico"):
            self.btn_aplicar_trafico.setText(tr("APLICAR"))

        if hasattr(self, "lbl_tit_backup"):
            self.lbl_tit_backup.setText(tr("💾 Respaldo de Perfiles"))
        if hasattr(self, "lbl_desc_backup"):
            self.lbl_desc_backup.setText(tr("Copia de seguridad en archivo .zip de todos los perfiles locales."))
        if hasattr(self, "btn_crear_backup"):
            self.btn_crear_backup.setText(tr("+ Crear Backup"))
        if hasattr(self, "btn_restaurar"):
            self.btn_restaurar.setText("↻ " + tr("Restaurar Copia"))
        if hasattr(self, "btn_borrar"):
            self.btn_borrar.setText("🗑 " + tr("Eliminar Copia"))
        if hasattr(self, "btn_abrir_backup"):
            self.btn_abrir_backup.setText("📁 " + tr("Abrir Carpeta"))
        if hasattr(self, "_actualizar_botones_backup"):
            self._actualizar_botones_backup()

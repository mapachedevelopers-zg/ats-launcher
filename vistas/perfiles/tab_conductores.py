from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QSlider, QSpinBox)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import QMessageBox, notificar_exito_boton, TXT_PRINCIPAL, TXT_SECUNDARIO


ESTILO_SLIDER = """
QSlider::groove:horizontal {
    height: 6px;
    background: #232731;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3B82F6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #CBD5E1;
    border: 1px solid #3B82F6;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #FFFFFF;
    border-color: #60A5FA;
}
"""

ESTILO_SPIN = """
QSpinBox {
    background: #12141A;
    color: #F8FAFC;
    border: 1px solid #2B303C;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 13px;
    font-weight: bold;
}
QSpinBox:focus {
    border-color: #3B82F6;
}
"""


class TabConductoresMixin:
    """Pestaña moderna y minimalista de gestión de personal, contratación y calificación."""

    def _tab_conductores(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(14)

        # --- Fila de KPIs ---
        fila_kpi = QHBoxLayout()
        fila_kpi.setSpacing(10)

        self.chip_contratados = self._crear_kpi_card(
            "Conductores Contratados", "0", "#38BDF8",
            "Total de conductores IA actualmente contratados en tu empresa.",
        )
        self.chip_con_camion = self._crear_kpi_card(
            "Con Camión Asignado", "0", "#10B981",
            "Conductores contratados que ya tienen un camión asignado trabajando.",
        )
        self.chip_sin_camion = self._crear_kpi_card(
            "En Espera (Sin Camión)", "0", "#F59E0B",
            "Conductores en garajes esperando que les asignes un camión libre.",
        )
        self.chip_espacios = self._crear_kpi_card(
            "Espacios Libres en Garajes", "0", "#A855F7",
            "Espacios totales disponibles en tus garajes para contratar nuevos conductores.",
        )

        fila_kpi.addWidget(self.chip_contratados["frame"], 1)
        fila_kpi.addWidget(self.chip_con_camion["frame"], 1)
        fila_kpi.addWidget(self.chip_sin_camion["frame"], 1)
        fila_kpi.addWidget(self.chip_espacios["frame"], 1)
        lay.addLayout(fila_kpi)

        # --- Tarjeta principal ---
        card_main = QFrame()
        card_main.setStyleSheet(
            "QFrame#card_main { background: #181A20; border: 1px solid #262932; border-radius: 8px; }"
            "QLabel { background: transparent; border: none; }"
        )
        card_main.setObjectName("card_main")
        lay_main = QVBoxLayout(card_main)
        lay_main.setContentsMargins(20, 18, 20, 20)
        lay_main.setSpacing(12)

        self.lbl_tit_main_conductores = QLabel(tr("Gestión y Contratación de Personal"))
        self.lbl_tit_main_conductores.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800;")
        lay_main.addWidget(self.lbl_tit_main_conductores)
        lay_main.addSpacing(4)

        # Contratación
        fila_hire = QHBoxLayout()
        fila_hire.setSpacing(10)

        self.lbl_cant_hire = QLabel(tr("Contratar conductores:"))
        self.lbl_cant_hire.setFixedWidth(200)
        self.lbl_cant_hire.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold;")

        self.slider_hire = QSlider(Qt.Horizontal)
        self.slider_hire.setStyleSheet(ESTILO_SLIDER)
        self.slider_hire.setRange(0, 0)
        self.slider_hire.setValue(0)
        self.slider_hire.setFixedHeight(24)

        self.spin_hire = QSpinBox()
        self.spin_hire.setStyleSheet(ESTILO_SPIN)
        self.spin_hire.setRange(0, 0)
        self.spin_hire.setValue(0)
        self.spin_hire.setFixedSize(72, 32)

        self.btn_hire_max = QPushButton(tr("Máximo"))
        self.btn_hire_max.setFixedSize(78, 32)
        self.btn_hire_max.setCursor(Qt.PointingHandCursor)
        self.btn_hire_max.setStyleSheet(self._estilo_btn("neutro"))
        self.btn_hire_max.setToolTip(
            "<div style='max-width: 250px;'>Ajusta la barra al número máximo de conductores que puedes contratar en este momento.</div>"
        )
        self.btn_hire_max.clicked.connect(self._action_hire_set_max)

        self.btn_contratar = QPushButton(tr("Contratar Conductores"))
        self.btn_contratar.setFixedSize(180, 32)
        self.btn_contratar.setCursor(Qt.PointingHandCursor)
        self.btn_contratar.setStyleSheet(self._estilo_btn("verde"))
        self.btn_contratar.setToolTip(
            "<div style='max-width: 260px;'>Contrata la cantidad elegida y los distribuye automáticamente en los espacios libres de tus garajes.</div>"
        )
        self.btn_contratar.clicked.connect(self._action_contratar_conductores)

        self.slider_hire.valueChanged.connect(self.spin_hire.setValue)
        self.spin_hire.valueChanged.connect(self.slider_hire.setValue)
        self.slider_hire.valueChanged.connect(self._on_hire_count_changed)

        fila_hire.addWidget(self.lbl_cant_hire)
        fila_hire.addWidget(self.slider_hire, 1)
        fila_hire.addWidget(self.spin_hire)
        fila_hire.addWidget(self.btn_hire_max)
        fila_hire.addWidget(self.btn_contratar)
        lay_main.addLayout(fila_hire)

        self.lbl_hire_status = QLabel("")
        self.lbl_hire_status.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600; padding-left: 204px;")
        lay_main.addWidget(self.lbl_hire_status)

        # Separador
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background: #232731; border: none;")
        lay_main.addSpacing(6)
        lay_main.addWidget(sep1)
        lay_main.addSpacing(6)

        # Calificación
        fila_calif = QHBoxLayout()
        fila_calif.setSpacing(10)

        self.lbl_calif_conductores = QLabel(tr("Calificación promedio:"))
        self.lbl_calif_conductores.setFixedWidth(200)
        self.lbl_calif_conductores.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold;")

        self.slider_calif = QSlider(Qt.Horizontal)
        self.slider_calif.setStyleSheet(ESTILO_SLIDER)
        self.slider_calif.setRange(10, 100)
        self.slider_calif.setSingleStep(5)
        self.slider_calif.setPageStep(10)
        self.slider_calif.setValue(50)
        self.slider_calif.setFixedHeight(24)

        self.lbl_calif_display = QLabel("5.0 · Medio")
        self.lbl_calif_display.setFixedSize(155, 32)
        self.lbl_calif_display.setStyleSheet(
            "background: #12141A; color: #38BDF8; font-size: 12px; font-weight: 800; "
            "border: 1px solid #2B303C; border-radius: 6px; padding: 2px 6px;"
        )
        self.lbl_calif_display.setAlignment(Qt.AlignCenter)

        self.btn_aplicar_calif = QPushButton(tr("Aplicar Calificación"))
        self.btn_aplicar_calif.setFixedSize(180, 32)
        self.btn_aplicar_calif.setCursor(Qt.PointingHandCursor)
        self.btn_aplicar_calif.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.btn_aplicar_calif.setStyleSheet(self._estilo_btn("azul"))
        self.btn_aplicar_calif.setToolTip(
            "<div style='max-width: 260px;'>Aplica la calificación elegida a todos tus conductores contratados, recalculando sus habilidades y experiencia.</div>"
        )
        self.btn_aplicar_calif.clicked.connect(self._action_aplicar_calificacion)

        self.slider_calif.valueChanged.connect(self._on_calif_slider_changed)

        fila_calif.addWidget(self.lbl_calif_conductores)
        fila_calif.addWidget(self.slider_calif, 1)
        fila_calif.addWidget(self.lbl_calif_display)
        fila_calif.addWidget(self.btn_aplicar_calif)
        lay_main.addLayout(fila_calif)

        # Separador
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background: #232731; border: none;")
        lay_main.addSpacing(6)
        lay_main.addWidget(sep2)
        lay_main.addSpacing(6)

        # Acciones
        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(12)

        self.btn_asignar_conductores = QPushButton(tr("Asignar a Camiones Libres"))
        self.btn_asignar_conductores.setFixedHeight(34)
        self.btn_asignar_conductores.setCursor(Qt.PointingHandCursor)
        self.btn_asignar_conductores.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.btn_asignar_conductores.setStyleSheet(self._estilo_btn("azul"))
        self.btn_asignar_conductores.setToolTip(
            "<div style='max-width: 260px;'>Asigna automáticamente los conductores disponibles a los camiones vacíos de tu empresa.</div>"
        )
        self.btn_asignar_conductores.clicked.connect(self._action_asignar_camiones)
        self.btn_asignar_conductores.setEnabled(False)

        self.btn_despedir_todos = QPushButton(tr("Despedir a Todos"))
        self.btn_despedir_todos.setFixedHeight(34)
        self.btn_despedir_todos.setCursor(Qt.PointingHandCursor)
        self.btn_despedir_todos.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.btn_despedir_todos.setStyleSheet(self._estilo_btn("rojo"))
        self.btn_despedir_todos.setToolTip(
            "<div style='max-width: 260px;'>Despide a todos los conductores contratados de tu empresa para liberar plazas en los garajes (tu personaje principal no se verá afectado).</div>"
        )
        self.btn_despedir_todos.clicked.connect(self._action_despedir_todos)
        self.btn_despedir_todos.setEnabled(False)

        fila_acciones.addWidget(self.btn_asignar_conductores, 1)
        fila_acciones.addWidget(self.btn_despedir_todos, 1)
        lay_main.addLayout(fila_acciones)

        lay.addWidget(card_main)
        lay.addStretch()
        return w

    def _crear_kpi_card(self, titulo: str, valor_inicial: str, color_acento: str, tooltip: str = "") -> dict:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: #181A20;
                border: 1px solid #262932;
                border-top: 3px solid {color_acento};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {color_acento};
                background: #1D2028;
            }}
        """)
        if tooltip:
            f.setToolTip(f"<div style='max-width: 250px;'>{tooltip}</div>")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        lbl_t = QLabel(tr(titulo))
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        lbl_v = QLabel(valor_inicial)
        lbl_v.setStyleSheet(f"color: {color_acento}; font-size: 19px; font-weight: 900; border: none; background: transparent;")

        lay.addWidget(lbl_t)
        lay.addWidget(lbl_v)
        return {"frame": f, "valor": lbl_v, "lbl_t": lbl_t, "titulo": titulo}

    def _actualizar_idioma_tab_conductores(self):
        """Actualiza títulos y textos de la pestaña Conductores."""
        for chip in (getattr(self, "chip_contratados", None), getattr(self, "chip_con_camion", None),
                     getattr(self, "chip_sin_camion", None), getattr(self, "chip_espacios", None)):
            if chip and "lbl_t" in chip:
                chip["lbl_t"].setText(tr(chip["titulo"]))
        if hasattr(self, "lbl_tit_main_conductores"):
            self.lbl_tit_main_conductores.setText(tr("Gestión y Contratación de Personal"))
        if hasattr(self, "lbl_cant_hire"):
            self.lbl_cant_hire.setText(tr("Contratar conductores:"))
        if hasattr(self, "btn_hire_max"):
            self.btn_hire_max.setText(tr("Máximo"))
        if hasattr(self, "btn_contratar"):
            self.btn_contratar.setText(tr("Contratar Conductores"))
        if hasattr(self, "lbl_calif_conductores"):
            self.lbl_calif_conductores.setText(tr("Calificación promedio:"))
        if hasattr(self, "btn_aplicar_calif"):
            self.btn_aplicar_calif.setText(tr("Aplicar Calificación"))
        if hasattr(self, "btn_asignar_conductores"):
            self.btn_asignar_conductores.setText(tr("Asignar a Camiones Libres"))
        if hasattr(self, "btn_despedir_todos"):
            self.btn_despedir_todos.setText(tr("Despedir a Todos"))
        if hasattr(self, "slider_calif"):
            self._on_calif_slider_changed(self.slider_calif.value())
        if hasattr(self, "datos_partida_actual") and self.datos_partida_actual:
            self._refrescar_conductores(self.datos_partida_actual)

    def _on_hire_count_changed(self, val: int):
        self.btn_contratar.setProperty("bloqueado_por_estado", val <= 0)
        self.btn_contratar.setEnabled(val > 0)

    def _action_hire_set_max(self):
        self.slider_hire.setValue(self.slider_hire.maximum())

    def _on_calif_slider_changed(self, val: int):
        calif = val / 10.0
        if calif >= 10.0:
            txt = f"★ 10.0 · {tr('Máximo')}"
        elif calif <= 2.5:
            txt = f"★ {calif:.1f} · {tr('Novato')}"
        elif calif <= 6.5:
            txt = f"★ {calif:.1f} · {tr('Medio')}"
        else:
            txt = f"★ {calif:.1f} · {tr('Avanzado')}"
        self.lbl_calif_display.setText(txt)

    def _siguiente_clave_conductor(self, prefijo: str) -> str:
        seq = getattr(self, "_secuencia_cola", 0) + 1
        self._secuencia_cola = seq
        return f"{prefijo}_{seq}"

    def _action_contratar_conductores(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        cant = self.spin_hire.value()
        if cant <= 0:
            QMessageBox.information(self, "Aviso", "Selecciona una cantidad de conductores mayor a 0 para contratar.")
            return
        if not self._juego_cerrado_o_alertar():
            return

        datos = self.datos_partida_actual
        libres = max(0, int(datos.get("free_driver_slots", 0)))
        pool = max(0, int(datos.get("pool_drivers_count", 0)))
        n_est = min(cant, libres, pool)
        if n_est > 0:
            datos["hired_drivers_count"] = max(0, int(datos.get("hired_drivers_count", 0)) + n_est)
            datos["pool_drivers_count"] = max(0, pool - n_est)
            datos["free_driver_slots"] = max(0, libres - n_est)
            datos["idle_hired_drivers_count"] = max(0, int(datos.get("idle_hired_drivers_count", 0)) + n_est)
            self._marcar_otras_tabs_sucias()
            self._refrescar_conductores(datos)
            notificar_exito_boton(self.btn_contratar, "¡Contratados!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_conductor("drv_hire"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g, c=cant: profile_manager.contratar_conductores_ia(r, cantidad=c, entrenar_max=False),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True,
        )

    def _action_aplicar_calificacion(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or not self._juego_cerrado_o_alertar():
            return
        calif = self.slider_calif.value() / 10.0
        datos = self.datos_partida_actual
        if int(datos.get("hired_drivers_count", 0)) > 0:
            datos["avg_driver_rating"] = round(calif, 1)
            self._marcar_otras_tabs_sucias()
            self._refrescar_conductores(datos)
            notificar_exito_boton(self.btn_aplicar_calif, f"¡Calificación {calif:.1f}!")

        self._encolar_edicion_ligera_async(
            "conductores_calif",
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g, c=calif: profile_manager.entrenar_conductores_ia(r, calificacion=c),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=False,
        )

    def _action_asignar_camiones(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        datos = self.datos_partida_actual
        drv_cnt = int(datos.get("hired_drivers_count", 0)) if datos else 0
        idle_cnt = int(datos.get("idle_hired_drivers_count", 0)) if datos else 0
        empty_trucks = int(datos.get("empty_trucks_count", 0)) if datos else 0
        if drv_cnt <= 0 or idle_cnt <= 0 or empty_trucks <= 0:
            return
        if not self._juego_cerrado_o_alertar():
            return

        n_pares = min(idle_cnt, empty_trucks)
        if n_pares > 0:
            datos["drivers_with_truck_count"] = max(0, int(datos.get("drivers_with_truck_count", 0)) + n_pares)
            datos["idle_hired_drivers_count"] = max(0, idle_cnt - n_pares)
            datos["empty_trucks_count"] = max(0, empty_trucks - n_pares)
            self._marcar_otras_tabs_sucias()
            self._refrescar_conductores(datos)
            notificar_exito_boton(self.btn_asignar_conductores, "¡Asignados!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_conductor("drv_asg"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g: profile_manager.asignar_conductores_a_camiones(r),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True,
        )

    def _action_despedir_todos(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        datos = self.datos_partida_actual
        drv_cnt = int(datos.get("hired_drivers_count", 0)) if datos else 0
        if drv_cnt <= 0:
            return
        resp = QMessageBox.question(
            self,
            "Confirmar despido general",
            "¿Estás seguro de que deseas despedir a TODOS los conductores contratados de tu empresa?\n\n"
            "Todos tus garajes quedarán sin conductores asignados (tu personaje principal no se verá afectado).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return
        if not self._juego_cerrado_o_alertar():
            return

        con_trk = max(0, int(datos.get("drivers_with_truck_count", 0)))
        datos["hired_drivers_count"] = 0
        datos["drivers_with_truck_count"] = 0
        datos["idle_hired_drivers_count"] = 0
        datos["pool_drivers_count"] = max(0, int(datos.get("pool_drivers_count", 0)) + drv_cnt)
        datos["free_driver_slots"] = max(0, int(datos.get("free_driver_slots", 0)) + drv_cnt)
        datos["empty_trucks_count"] = max(0, int(datos.get("empty_trucks_count", 0)) + con_trk)
        self._marcar_otras_tabs_sucias()
        self._refrescar_conductores(datos)
        notificar_exito_boton(self.btn_despedir_todos, "¡Todos Despedidos!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_conductor("drv_dismiss"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g: profile_manager.despedir_conductores_ia(r, solo_sin_camion=False),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True,
        )

    def _refrescar_conductores(self, datos: dict):
        drv_cnt = int(datos.get("hired_drivers_count", 0))
        free_slots = int(datos.get("free_driver_slots", 0))
        pool_cnt = int(datos.get("pool_drivers_count", 0))
        idle_cnt = int(datos.get("idle_hired_drivers_count", 0))
        empty_trucks = int(datos.get("empty_trucks_count", 0))
        drivers_with_truck = int(datos.get("drivers_with_truck_count", 0))
        avg_rating = float(datos.get("avg_driver_rating", 5.0))

        # Conductores accesibles según las agencias de reclutamiento desbloqueadas
        agencias_desbloq = int(datos.get("unlocked_recruitments_count", 0))
        total_ciudades = int(datos.get("total_cities_count", 0))
        if total_ciudades > 0:
            if agencias_desbloq <= 0:
                disponibles_agencias = 0
            elif agencias_desbloq >= total_ciudades:
                disponibles_agencias = pool_cnt
            else:
                disponibles_agencias = max(1, int(round(pool_cnt * (agencias_desbloq / total_ciudades)))) if pool_cnt > 0 else 0
        else:
            disponibles_agencias = pool_cnt

        self.chip_contratados["valor"].setText(str(drv_cnt))
        self.chip_con_camion["valor"].setText(str(drivers_with_truck))
        self.chip_sin_camion["valor"].setText(str(idle_cnt))
        self.chip_espacios["valor"].setText(str(free_slots))

        max_contratable = min(free_slots, disponibles_agencias)
        self.slider_hire.blockSignals(True)
        self.spin_hire.blockSignals(True)
        self.slider_hire.setRange(0, max_contratable)
        self.spin_hire.setRange(0, max_contratable)

        if max_contratable <= 0:
            if free_slots <= 0:
                self.lbl_hire_status.setText(
                    tr("Sin espacios libres en garajes. Compra o amplía garajes en la pestaña Garajes.")
                )
                self.lbl_hire_status.setStyleSheet("color: #E5A93C; font-size: 11px; font-weight: 600; padding-left: 204px;")
            elif agencias_desbloq <= 0 and pool_cnt > 0:
                self.lbl_hire_status.setText(
                    tr("Sin agencias desbloqueadas. Desbloquéalas en Exploración y Mapa para contratar.")
                )
                self.lbl_hire_status.setStyleSheet("color: #E5A93C; font-size: 11px; font-weight: 600; padding-left: 204px;")
            else:
                self.lbl_hire_status.setText(
                    tr("No hay más conductores disponibles en el mercado laboral de esta partida.")
                )
                self.lbl_hire_status.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600; padding-left: 204px;")
        else:
            if 0 < agencias_desbloq < total_ciudades and disponibles_agencias < pool_cnt:
                self.lbl_hire_status.setText(
                    tr("Capacidad actual: {cant} conductores  ·  Desbloquea más agencias en Exploración y Mapa para acceder a {total}.").format(
                        cant=max_contratable, total=pool_cnt
                    )
                )
            else:
                self.lbl_hire_status.setText(
                    tr("Espacio disponible para contratar hasta {cant} conductores en tus garajes.").format(
                        cant=max_contratable
                    )
                )
            self.lbl_hire_status.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600; padding-left: 204px;")

        val_actual = min(self.spin_hire.value(), max_contratable)
        if val_actual == 0 and max_contratable > 0:
            val_actual = 1
        self.slider_hire.setValue(val_actual)
        self.spin_hire.setValue(val_actual)
        self.slider_hire.blockSignals(False)
        self.spin_hire.blockSignals(False)

        self.btn_hire_max.setEnabled(max_contratable > 0)
        self._on_hire_count_changed(val_actual)

        # Calificación
        val_slider_calif = max(10, min(100, int(round(avg_rating * 10))))
        self.slider_calif.blockSignals(True)
        self.slider_calif.setValue(val_slider_calif)
        self.slider_calif.blockSignals(False)
        self._on_calif_slider_changed(val_slider_calif)

        # Asignar a camiones libres
        posibles_asignar = min(empty_trucks, idle_cnt)
        puede_asignar = drv_cnt > 0 and idle_cnt > 0 and empty_trucks > 0
        self.btn_asignar_conductores.setProperty("bloqueado_por_estado", not puede_asignar)
        self.btn_asignar_conductores.setEnabled(puede_asignar)
        if puede_asignar:
            self.btn_asignar_conductores.setToolTip(
                f"<div style='max-width: 270px;'><b>Asignar a Camiones Libres</b><br>"
                f"Asignará hasta <b>{posibles_asignar}</b> conductor(es) disponibles a los camiones vacíos de tu empresa.</div>"
            )
        else:
            if drv_cnt <= 0:
                motivo = "No tienes conductores contratados en esta partida."
            elif idle_cnt <= 0:
                motivo = "Todos tus conductores contratados ya tienen un camión asignado."
            elif empty_trucks <= 0:
                motivo = "No tienes camiones vacíos disponibles en tus garajes para asignar."
            else:
                motivo = "No hay conductores ni camiones disponibles para emparejar en este momento."
            self.btn_asignar_conductores.setToolTip(
                f"<div style='max-width: 270px;'><b>Opción Desactivada</b><br>{motivo}</div>"
            )

        # Despedir a todos
        puede_despedir = drv_cnt > 0
        self.btn_despedir_todos.setProperty("bloqueado_por_estado", not puede_despedir)
        self.btn_despedir_todos.setEnabled(puede_despedir)
        if puede_despedir:
            self.btn_despedir_todos.setToolTip(
                f"<div style='max-width: 270px;'><b>Despedir a Todos</b><br>"
                f"Despide a los <b>{drv_cnt}</b> conductores contratados (tu personaje principal no se verá afectado).</div>"
            )
        else:
            self.btn_despedir_todos.setToolTip(
                "<div style='max-width: 270px;'><b>Opción Desactivada</b><br>"
                "No tienes conductores contratados en esta partida para despedir.</div>"
            )

        # Aplicar calificación
        puede_calif = drv_cnt > 0
        self.btn_aplicar_calif.setProperty("bloqueado_por_estado", not puede_calif)
        self.btn_aplicar_calif.setEnabled(puede_calif)
        if puede_calif:
            self.btn_aplicar_calif.setToolTip(
                f"<div style='max-width: 270px;'><b>Aplicar Calificación</b><br>"
                f"Aplica la calificación elegida a tus <b>{drv_cnt}</b> conductores contratados.</div>"
            )
        else:
            self.btn_aplicar_calif.setToolTip(
                "<div style='max-width: 270px;'><b>Opción Desactivada</b><br>"
                "No tienes conductores contratados en tu empresa para calificar.</div>"
            )

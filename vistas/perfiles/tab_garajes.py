from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QFrame, QScrollArea,
                               QLineEdit)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import (QMessageBox, notificar_exito_boton, TXT_PRINCIPAL, TXT_SECUNDARIO,
                    VERDE_TXT, VERDE_BORDE, AZUL_TXT, AZUL_BORDE,
                    AMBAR_TXT, AMBAR_BORDE, ROJO_TXT, ROJO_BORDE)


class TabGarajesMixin:
    """Pestaña Garajes: fila superior de acciones masivas dentro de la misma lista desplazable para alineación exacta."""

    def _tab_garajes(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 12, 18, 14)
        lay.setSpacing(14)

        # --- Panel de control (estadísticas + filtros) ---
        panel_ctrl = QFrame()
        panel_ctrl.setStyleSheet(
            "QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }"
            "QLabel { background: transparent; border: none; }"
        )
        lay_ctrl = QVBoxLayout(panel_ctrl)
        lay_ctrl.setContentsMargins(18, 14, 18, 14)
        lay_ctrl.setSpacing(12)

        # Fila de estadísticas
        fila_stats = QHBoxLayout()
        fila_stats.setSpacing(14)

        def _crear_etiqueta_stat(color_texto: str) -> QLabel:
            lb = QLabel()
            lb.setStyleSheet(f"color: {color_texto}; font-size: 12px; font-weight: 800; border: none; background: transparent;")
            return lb

        self.lbl_stat_total = _crear_etiqueta_stat(TXT_PRINCIPAL)
        self.lbl_stat_comprados = _crear_etiqueta_stat(VERDE_TXT)
        self.lbl_stat_sin_comprar = _crear_etiqueta_stat("#94A3B8")

        sep_stats = QLabel("·")
        sep_stats.setStyleSheet("color: #475569; font-size: 14px; font-weight: 900; border: none; background: transparent;")

        self.lbl_stat_pequenos = _crear_etiqueta_stat(AZUL_TXT)
        self.lbl_stat_medianos = _crear_etiqueta_stat(AMBAR_TXT)
        self.lbl_stat_grandes = _crear_etiqueta_stat("#34D399")

        fila_stats.addWidget(self.lbl_stat_total)
        fila_stats.addWidget(self.lbl_stat_comprados)
        fila_stats.addWidget(self.lbl_stat_sin_comprar)
        fila_stats.addWidget(sep_stats)
        fila_stats.addWidget(self.lbl_stat_pequenos)
        fila_stats.addWidget(self.lbl_stat_medianos)
        fila_stats.addWidget(self.lbl_stat_grandes)
        fila_stats.addStretch()

        lay_ctrl.addLayout(fila_stats)

        # Fila de búsqueda / filtro
        fila_filtro = QHBoxLayout()
        fila_filtro.setSpacing(10)

        self.txt_buscar_garaje = QLineEdit()
        self.txt_buscar_garaje.setPlaceholderText(tr("Buscar garaje por nombre de ciudad..."))
        self.txt_buscar_garaje.setFixedHeight(32)
        self.txt_buscar_garaje.setStyleSheet(self._estilo_input())
        self.txt_buscar_garaje.textChanged.connect(self._filtrar_lista_garajes)

        self.lbl_fil_garajes = QLabel(tr("Mostrar:"))
        self.lbl_fil_garajes.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold;")

        self.combo_filtro_garaje = QComboBox()
        self.combo_filtro_garaje.setFixedHeight(32)
        self.combo_filtro_garaje.setFixedWidth(185)
        self.combo_filtro_garaje.setStyleSheet(self._estilo_combo())
        self.combo_filtro_garaje.addItems([
            tr("Todos los garajes"),
            tr("Solo Comprados"),
            tr("Sin Comprar"),
            tr("Tamaño Pequeño"),
            tr("Tamaño Mediano"),
            tr("Tamaño Grande"),
        ])
        self._configurar_combo_un_clic(self.combo_filtro_garaje, self._filtrar_lista_garajes)

        fila_filtro.addWidget(self.txt_buscar_garaje, 1)
        fila_filtro.addWidget(self.lbl_fil_garajes)
        fila_filtro.addWidget(self.combo_filtro_garaje)
        lay_ctrl.addLayout(fila_filtro)
        lay.addWidget(panel_ctrl)

        # --- Tabla (lista desplazable) ---
        marco_tabla = QFrame()
        marco_tabla.setObjectName("marcoTablaGarajes")
        marco_tabla.setStyleSheet(
            "QFrame#marcoTablaGarajes { background: #11161B; border: 1px solid #262932; border-radius: 8px; }"
        )
        lay_tabla = QVBoxLayout(marco_tabla)
        lay_tabla.setContentsMargins(0, 0, 0, 0)
        lay_tabla.setSpacing(0)

        self.scroll_garajes = QScrollArea()
        self.scroll_garajes.setWidgetResizable(True)
        self.scroll_garajes.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_garajes.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #13151B; width: 12px; border-radius: 6px; margin: 2px; }
            QScrollBar::handle:vertical { background: #3B4252; border-radius: 5px; min-height: 28px; }
            QScrollBar::handle:vertical:hover { background: #3B82F6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal { background: #13151B; height: 16px; border-radius: 8px; margin: 2px; border: 1px solid #1E232E; }
            QScrollBar::handle:horizontal { background: #475569; border-radius: 6px; min-width: 45px; margin: 1px; }
            QScrollBar::handle:horizontal:hover { background: #3B82F6; }
            QScrollBar::handle:horizontal:pressed { background: #60A5FA; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)

        self.contenedor_lista_garajes = QWidget()
        self.contenedor_lista_garajes.setStyleSheet("background: transparent;")
        self.layout_lista_garajes = QVBoxLayout(self.contenedor_lista_garajes)
        self.layout_lista_garajes.setContentsMargins(10, 8, 10, 8)
        self.layout_lista_garajes.setSpacing(8)

        # Fila maestra de acciones masivas (primer elemento de la lista)
        self.fila_maestra_garajes = QFrame()
        self.fila_maestra_garajes.setFixedHeight(50)
        self.fila_maestra_garajes.setStyleSheet(
            "QFrame { background: #181D26; border: 1px solid #283244; border-radius: 6px; }"
            "QLabel { background: transparent; border: none; }"
        )
        lay_col = QHBoxLayout(self.fila_maestra_garajes)
        lay_col.setContentsMargins(12, 6, 12, 6)
        lay_col.setSpacing(10)

        self.lbl_acc_garajes = QLabel(tr("Cambiar tamaño a todos los garages:"))
        self.lbl_acc_garajes.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 12px; font-weight: 800;")

        self.combo_masivo_garajes = QComboBox()
        self.combo_masivo_garajes.setFixedHeight(30)
        self.combo_masivo_garajes.setMinimumWidth(320)
        self.combo_masivo_garajes.setStyleSheet(self._estilo_combo())
        self.combo_masivo_garajes.addItems([
            tr("Selecciona una opción"),
            tr("Comprar todos los garajes en tamaño pequeño"),
            tr("Comprar todos los garajes en tamaño mediano"),
            tr("Comprar todos los garajes en tamaño grande"),
        ])
        self._configurar_combo_un_clic(self.combo_masivo_garajes)

        self.btn_aplicar_masivo = QPushButton(tr("Aplicar a Todos"))
        self.btn_aplicar_masivo.setFixedHeight(30)
        self.btn_aplicar_masivo.setCursor(Qt.PointingHandCursor)
        self.btn_aplicar_masivo.setStyleSheet(self._estilo_btn("azul"))
        self.btn_aplicar_masivo.clicked.connect(self._action_aplicar_combo_masivo)

        self.btn_vender_todos = QPushButton(tr("🗑️ Vender los Garajes Vacíos"))
        self.btn_vender_todos.setFixedHeight(30)
        self.btn_vender_todos.setCursor(Qt.PointingHandCursor)
        self.btn_vender_todos.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.btn_vender_todos.setStyleSheet(self._estilo_btn("rojo"))
        self.btn_vender_todos.setToolTip(
            "Vende todos los garajes que no tengan camiones ni conductores asignados."
        )
        self.btn_vender_todos.clicked.connect(self._action_confirmar_vender_todos_vacios)
        self.btn_vender_todos.setEnabled(False)

        lay_col.addWidget(self.lbl_acc_garajes)
        lay_col.addWidget(self.combo_masivo_garajes)
        lay_col.addWidget(self.btn_aplicar_masivo)
        lay_col.addStretch()
        lay_col.addWidget(self.btn_vender_todos)

        self.layout_lista_garajes.addWidget(self.fila_maestra_garajes)
        self.layout_lista_garajes.addStretch()

        self.scroll_garajes.setWidget(self.contenedor_lista_garajes)
        lay_tabla.addWidget(self.scroll_garajes, 1)

        lay.addWidget(marco_tabla, 1)
        return w

    def _estilo_segmento(self, posicion: str, estado: str) -> str:
        """Estilo para cada segmento [ Peq | Med | Gra ] dentro del control unificado."""
        radios = {
            "izq": "border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;",
            "cen": "border-radius: 0px;",
            "der": "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;",
        }[posicion]

        borde_sep = "border-right: none;" if posicion != "der" else ""

        if estado == "activo_azul":
            return f"""
                QPushButton {{
                    background: #1B2B44; color: #93C5FD;
                    border: 1px solid #2563EB; {borde_sep} {radios}
                    font-size: 11px; font-weight: 800; padding: 0;
                }}
            """
        if estado == "activo_ambar":
            return f"""
                QPushButton {{
                    background: #332414; color: #FCD34D;
                    border: 1px solid #D97706; {borde_sep} {radios}
                    font-size: 11px; font-weight: 800; padding: 0;
                }}
            """
        if estado == "activo_verde":
            return f"""
                QPushButton {{
                    background: #122920; color: #6EE7B7;
                    border: 1px solid #059669; {borde_sep} {radios}
                    font-size: 11px; font-weight: 800; padding: 0;
                }}
            """
        # inactivo
        return f"""
                QPushButton {{
                    background: #14171E; color: #64748B;
                    border: 1px solid #232834; {borde_sep} {radios}
                    font-size: 11px; font-weight: 600; padding: 0;
                }}
                QPushButton:hover {{
                    background: #1E2430; color: #E2E8F0; border-color: #3B82F6;
                }}
            """

    def _actualizar_resumen_garajes_label(self):
        garajes = self.datos_partida_actual.get("garages", [])
        total = len(garajes)
        grandes = sum(1 for g in garajes if g["status"] == 3)
        medianos = sum(1 for g in garajes if g["status"] == 2)
        pequenos = sum(1 for g in garajes if g["status"] in (1, 6))
        comprados = grandes + medianos + pequenos
        no_comprados = total - comprados

        self.lbl_stat_total.setText(f"{tr('Total:')} {total}")
        self.lbl_stat_comprados.setText(f"{tr('● Comprados:')} {comprados}")
        self.lbl_stat_sin_comprar.setText(f"{tr('○ Sin comprar:')} {no_comprados}")
        self.lbl_stat_pequenos.setText(f"{tr('Pequeños:')} {pequenos}")
        self.lbl_stat_medianos.setText(f"{tr('Medianos:')} {medianos}")
        self.lbl_stat_grandes.setText(f"{tr('Grandes:')} {grandes}")

        # Garajes comprados completamente vacíos (vendibles)
        vacios = sum(1 for g in garajes if g["status"] > 0 and g["vehicles_ocupados"] == 0 and g["drivers_ocupados"] == 0)
        puede_vender = vacios > 0
        self.btn_vender_todos.setProperty("bloqueado_por_estado", not puede_vender)
        self.btn_vender_todos.setEnabled(puede_vender)
        if puede_vender:
            self.btn_vender_todos.setToolTip(
                f"<div style='max-width: 260px;'><b>Vender Garajes Vacíos</b><br>"
                f"Hay <b>{vacios}</b> garaje(s) comprado(s) completamente vacíos (sin camiones ni conductores) listos para vender.</div>"
            )
        else:
            self.btn_vender_todos.setToolTip(
                "<div style='max-width: 260px;'><b>Opción Desactivada</b><br>"
                "No tienes ningún garaje comprado vacío para vender. Todos tus garajes comprados tienen "
                "camiones o conductores asignados (o no tienes garajes comprados).</div>"
            )

    def _poblar_lista_garajes(self, garajes: list):
        self.contenedor_lista_garajes.setUpdatesEnabled(False)
        try:
            # Conserva la fila maestra (índice 0) y elimina el resto
            while self.layout_lista_garajes.count() > 1:
                item = self.layout_lista_garajes.takeAt(1)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
            self.filas_garajes.clear()

            for g in garajes:
                fila = QFrame()
                fila.setFixedHeight(40)
                fila.setStyleSheet(
                    "QFrame { background: #16181F; border: 1px solid #222631; border-radius: 6px; }"
                    "QLabel { background: transparent; border: none; }"
                )
                lay_f = QHBoxLayout(fila)
                lay_f.setContentsMargins(12, 3, 12, 3)
                lay_f.setSpacing(8)

                lbl_ciudad = QLabel(g["nombre"])
                lbl_ciudad.setFixedWidth(175)
                lbl_ciudad.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 700;")

                lbl_ocup = QLabel(
                    f"{tr('Camiones:')} {g['vehicles_ocupados']}/{g['capacidad']}   |   "
                    f"{tr('Conductores:')} {g['drivers_ocupados']}/{g['capacidad']}"
                )
                lbl_ocup.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 11px; font-weight: 600;")

                # Control segmentado [ Peq | Med | Gra ]
                marco_seg = QFrame()
                marco_seg.setFixedHeight(26)
                marco_seg.setFixedWidth(144)
                lay_seg = QHBoxLayout(marco_seg)
                lay_seg.setContentsMargins(0, 0, 0, 0)
                lay_seg.setSpacing(0)

                btn_peq = QPushButton(tr("Peq"))
                btn_peq.setFixedSize(48, 26)
                btn_peq.setCursor(Qt.PointingHandCursor)

                btn_med = QPushButton(tr("Med"))
                btn_med.setFixedSize(48, 26)
                btn_med.setCursor(Qt.PointingHandCursor)

                btn_gra = QPushButton(tr("Gra"))
                btn_gra.setFixedSize(48, 26)
                btn_gra.setCursor(Qt.PointingHandCursor)

                lay_seg.addWidget(btn_peq)
                lay_seg.addWidget(btn_med)
                lay_seg.addWidget(btn_gra)

                btn_ven = QPushButton(tr("Vender"))
                btn_ven.setFixedSize(80, 26)
                btn_ven.setCursor(Qt.PointingHandCursor)

                info_fila = {
                    "widget": fila,
                    "datos": g,
                    "lbl_ocup": lbl_ocup,
                    "btn_peq": btn_peq,
                    "btn_med": btn_med,
                    "btn_gra": btn_gra,
                    "btn_ven": btn_ven,
                }

                btn_peq.clicked.connect(lambda _=False, inf=info_fila: self._action_cambiar_garaje_fila(inf, 6))
                btn_med.clicked.connect(lambda _=False, inf=info_fila: self._action_cambiar_garaje_fila(inf, 2))
                btn_gra.clicked.connect(lambda _=False, inf=info_fila: self._action_cambiar_garaje_fila(inf, 3))
                btn_ven.clicked.connect(lambda _=False, inf=info_fila: self._action_cambiar_garaje_fila(inf, 0))

                self._refrescar_botones_fila_garaje(info_fila)

                lay_f.addWidget(lbl_ciudad)
                lay_f.addWidget(lbl_ocup, 1)
                lay_f.addWidget(marco_seg)
                lay_f.addWidget(btn_ven)

                self.layout_lista_garajes.addWidget(fila)
                self.filas_garajes.append(info_fila)

            self.layout_lista_garajes.addStretch()
            self._filtrar_lista_garajes()
        finally:
            self.contenedor_lista_garajes.setUpdatesEnabled(True)

    def _refrescar_botones_fila_garaje(self, info_fila: dict):
        st = info_fila["datos"]["status"]
        btn_peq = info_fila["btn_peq"]
        btn_med = info_fila["btn_med"]
        btn_gra = info_fila["btn_gra"]
        btn_ven = info_fila["btn_ven"]

        # Pequeño (1 o 6)
        if st in (1, 6):
            btn_peq.setStyleSheet(self._estilo_segmento("izq", "activo_azul"))
            btn_peq.setEnabled(False)
            btn_peq.setToolTip("Garaje actualmente en tamaño Pequeño")
        else:
            btn_peq.setStyleSheet(self._estilo_segmento("izq", "inactivo"))
            btn_peq.setEnabled(True)
            btn_peq.setToolTip("Poner este garaje en tamaño Pequeño")

        # Mediano (2)
        if st == 2:
            btn_med.setStyleSheet(self._estilo_segmento("cen", "activo_ambar"))
            btn_med.setEnabled(False)
            btn_med.setToolTip("Garaje actualmente en tamaño Mediano")
        else:
            btn_med.setStyleSheet(self._estilo_segmento("cen", "inactivo"))
            btn_med.setEnabled(True)
            btn_med.setToolTip("Mejorar este garaje a tamaño Mediano")

        # Grande (3)
        if st == 3:
            btn_gra.setStyleSheet(self._estilo_segmento("der", "activo_verde"))
            btn_gra.setEnabled(False)
            btn_gra.setToolTip("Garaje actualmente en tamaño Grande")
        else:
            btn_gra.setStyleSheet(self._estilo_segmento("der", "inactivo"))
            btn_gra.setEnabled(True)
            btn_gra.setToolTip("Mejorar este garaje a tamaño Grande")

        # Vender
        btn_ven.setText(tr("Vender"))
        if st == 0:
            btn_ven.setEnabled(False)
            btn_ven.setStyleSheet(self._estilo_btn("deshabilitado", compacto=True))
            btn_ven.setToolTip(tr("Este garaje aún no ha sido comprado"))
        else:
            btn_ven.setEnabled(True)
            btn_ven.setStyleSheet(self._estilo_btn("rojo", compacto=True))
            btn_ven.setToolTip(tr("Vender este garaje (debe estar libre de camiones y conductores)"))

    def _filtrar_lista_garajes(self, *args):
        texto = self.txt_buscar_garaje.text().strip().lower()
        modo = self.combo_filtro_garaje.currentIndex()

        for inf in self.filas_garajes:
            g = inf["datos"]
            coincide_texto = not texto or texto in g["nombre"].lower() or texto in g["id"].lower()
            st = g["status"]
            if modo == 1:
                coincide_modo = st in (1, 2, 3, 6)
            elif modo == 2:
                coincide_modo = st == 0
            elif modo == 3:
                coincide_modo = st in (1, 6)
            elif modo == 4:
                coincide_modo = st == 2
            elif modo == 5:
                coincide_modo = st == 3
            else:
                coincide_modo = True

            inf["widget"].setVisible(coincide_texto and coincide_modo)

    def _action_cambiar_garaje_fila(self, info_fila: dict, nuevo_status: int):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        g = info_fila["datos"]
        self._ejecutar_accion_partida_async(
            lambda: profile_manager.modificar_garaje_individual(ruta_g, g["id"], nuevo_status)
        )

    def _action_aplicar_combo_masivo(self):
        idx = self.combo_masivo_garajes.currentIndex()
        if idx == 0:
            QMessageBox.information(
                self,
                "Seleccionar tamaño",
                "Por favor selecciona primero un tamaño en la lista para aplicar a todos los garajes.",
            )
            return

        mapa_status = {
            1: (6, "tamaño pequeño"),
            2: (2, "tamaño mediano"),
            3: (3, "tamaño grande"),
        }
        nuevo_st, nom_tam = mapa_status[idx]

        resp = QMessageBox.question(
            self,
            "Confirmar cambio global",
            f"¿Estás seguro de que deseas poner todos tus garajes en {nom_tam}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Yes:
            self._action_modificar_todos_garajes(nuevo_st, self.btn_aplicar_masivo)

    def _action_confirmar_vender_todos_vacios(self):
        garajes = self.datos_partida_actual.get("garages", [])
        vacios = sum(1 for g in garajes if g["status"] > 0 and g["vehicles_ocupados"] == 0 and g["drivers_ocupados"] == 0)
        if vacios == 0:
            QMessageBox.information(
                self,
                "Sin garajes vacíos",
                "No tienes garajes comprados que estén vacíos actualmente (todos tienen camiones o conductores asignados).",
            )
            return

        resp = QMessageBox.warning(
            self,
            "Confirmar venta de garajes",
            f"Se encontraron {vacios} garajes vacíos sin camiones ni conductores asignados.\n\n"
            f"¿Deseas vender todos estos garajes vacíos?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Yes:
            self._action_modificar_todos_garajes(0, self.btn_vender_todos)

    def _action_modificar_todos_garajes(self, nuevo_status: int, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        txt_ok = "¡Vendidos!" if nuevo_status == 0 else "¡Actualizados!"
        self._ejecutar_accion_partida_async(
            lambda: profile_manager.modificar_todos_los_garajes(ruta_g, nuevo_status),
            boton=boton,
            texto_exito=txt_ok,
        )

    def _refrescar_garajes(self, datos: dict):
        nuevos = datos.get("garages", [])
        ids_actuales = [i["datos"]["id"] for i in self.filas_garajes]
        ids_nuevos = [g["id"] for g in nuevos]
        if self.filas_garajes and set(ids_actuales) == set(ids_nuevos):
            # Mismos garajes: actualiza en sitio sin reconstruir la lista
            mapa_filas = {inf["datos"]["id"]: inf for inf in self.filas_garajes}
            orden_cambio = ids_actuales != ids_nuevos
            self.filas_garajes = [mapa_filas[g["id"]] for g in nuevos]
            if orden_cambio:
                self.contenedor_lista_garajes.setUpdatesEnabled(False)
            try:
                for idx, (inf, g) in enumerate(zip(self.filas_garajes, nuevos), start=1):
                    inf["datos"] = g
                    inf["lbl_ocup"].setText(
                        f"{tr('Camiones:')} {g['vehicles_ocupados']}/{g['capacidad']}   |   "
                        f"{tr('Conductores:')} {g['drivers_ocupados']}/{g['capacidad']}"
                    )
                    self._refrescar_botones_fila_garaje(inf)
                    if orden_cambio:
                        self.layout_lista_garajes.insertWidget(idx, inf["widget"])
            finally:
                if orden_cambio:
                    self.contenedor_lista_garajes.setUpdatesEnabled(True)
            self._actualizar_resumen_garajes_label()
            self._filtrar_lista_garajes()
        else:
            self._poblar_lista_garajes(nuevos)
            self._actualizar_resumen_garajes_label()

    def _actualizar_idioma_tab_garajes(self):
        """Actualiza todos los textos estáticos y dinámicos de la pestaña Garajes."""
        if hasattr(self, "txt_buscar_garaje") and self.txt_buscar_garaje:
            self.txt_buscar_garaje.setPlaceholderText(tr("Buscar garaje por nombre de ciudad..."))
        if hasattr(self, "lbl_fil_garajes") and self.lbl_fil_garajes:
            self.lbl_fil_garajes.setText(tr("Mostrar:"))
        if hasattr(self, "combo_filtro_garaje") and self.combo_filtro_garaje:
            idx_fil = self.combo_filtro_garaje.currentIndex()
            self.combo_filtro_garaje.blockSignals(True)
            self.combo_filtro_garaje.clear()
            self.combo_filtro_garaje.addItems([
                tr("Todos los garajes"),
                tr("Solo Comprados"),
                tr("Sin Comprar"),
                tr("Tamaño Pequeño"),
                tr("Tamaño Mediano"),
                tr("Tamaño Grande"),
            ])
            if 0 <= idx_fil < self.combo_filtro_garaje.count():
                self.combo_filtro_garaje.setCurrentIndex(idx_fil)
            self.combo_filtro_garaje.blockSignals(False)

        if hasattr(self, "lbl_acc_garajes") and self.lbl_acc_garajes:
            self.lbl_acc_garajes.setText(tr("Cambiar tamaño a todos los garages:"))
        if hasattr(self, "combo_masivo_garajes") and self.combo_masivo_garajes:
            idx_mas = self.combo_masivo_garajes.currentIndex()
            self.combo_masivo_garajes.blockSignals(True)
            self.combo_masivo_garajes.clear()
            self.combo_masivo_garajes.addItems([
                tr("Selecciona una opción"),
                tr("Comprar todos los garajes en tamaño pequeño"),
                tr("Comprar todos los garajes en tamaño mediano"),
                tr("Comprar todos los garajes en tamaño grande"),
            ])
            if 0 <= idx_mas < self.combo_masivo_garajes.count():
                self.combo_masivo_garajes.setCurrentIndex(idx_mas)
            self.combo_masivo_garajes.blockSignals(False)

        if hasattr(self, "btn_aplicar_masivo") and self.btn_aplicar_masivo:
            self.btn_aplicar_masivo.setText(tr("Aplicar a Todos"))
        if hasattr(self, "btn_vender_todos") and self.btn_vender_todos:
            self.btn_vender_todos.setText(tr("🗑️ Vender los Garajes Vacíos"))

        for inf in getattr(self, "filas_garajes", []):
            if "btn_peq" in inf and inf["btn_peq"]:
                inf["btn_peq"].setText(tr("Peq"))
            if "btn_med" in inf and inf["btn_med"]:
                inf["btn_med"].setText(tr("Med"))
            if "btn_gra" in inf and inf["btn_gra"]:
                inf["btn_gra"].setText(tr("Gra"))
            if "btn_ven" in inf and inf["btn_ven"]:
                inf["btn_ven"].setText(tr("Vender"))
            if "lbl_ocup" in inf and inf["lbl_ocup"] and "datos" in inf:
                g = inf["datos"]
                inf["lbl_ocup"].setText(
                    f"{tr('Camiones:')} {g.get('vehicles_ocupados', 0)}/{g.get('capacidad', 0)}   |   "
                    f"{tr('Conductores:')} {g.get('drivers_ocupados', 0)}/{g.get('capacidad', 0)}"
                )

        if hasattr(self, "datos_partida_actual") and self.datos_partida_actual:
            self._actualizar_resumen_garajes_label()

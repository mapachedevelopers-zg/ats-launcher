from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
                               QSpinBox, QScrollArea)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import (QMessageBox, notificar_exito_boton, VERDE_TXT, AMBAR_TXT, AZUL_TXT, ROJO_TXT,
                    TXT_PRINCIPAL, TXT_SECUNDARIO)


# Estilo compartido de los selectores de cantidad de cada fila
ESTILO_SPIN_CAMION = (
    "QSpinBox { background: #12141A; color: #F8FAFC; border: 1px solid #2B303C; "
    "border-radius: 6px; padding: 2px 6px; font-size: 12px; font-weight: bold; }"
)


class TabCamionesMixin:
    """Pestaña optimizada para comprar y vender camiones usados sin congelar la interfaz."""

    def _tab_camiones_flota(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 12, 18, 14)
        lay.setSpacing(14)

        # --- Tarjeta superior: titulo, acciones globales y resumen ---
        card_top = QFrame()
        card_top.setStyleSheet(
            "QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }"
            "QLabel { background: transparent; border: none; }"
        )
        lay_top = QVBoxLayout(card_top)
        lay_top.setContentsMargins(18, 14, 18, 14)
        lay_top.setSpacing(12)

        fila_tit = QHBoxLayout()
        fila_tit.setSpacing(10)

        self.lbl_tit_camiones = QLabel(tr("Concesionario de Camiones Usados y Flota en Garajes"))
        self.lbl_tit_camiones.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800;")

        self.btn_comprar_variados_tab = QPushButton(tr("Comprar Camiones Variados para Llenar Garajes"))
        self.btn_comprar_variados_tab.setFixedHeight(30)
        self.btn_comprar_variados_tab.setCursor(Qt.PointingHandCursor)
        self.btn_comprar_variados_tab.setStyleSheet(self._estilo_btn("verde"))
        self.btn_comprar_variados_tab.setToolTip(
            "<div style='max-width: 260px;'>Compra automáticamente una selección variada de camiones usados "
            "y los ubica en tus garajes libres sin asignarles chofer (puedes asignarlos manualmente en la pestaña Conductores).</div>"
        )
        self.btn_comprar_variados_tab.clicked.connect(self._action_comprar_flota_variada)

        self.btn_vender_flota_tab = QPushButton(tr("Vender Todos los Camiones"))
        self.btn_vender_flota_tab.setFixedHeight(30)
        self.btn_vender_flota_tab.setCursor(Qt.PointingHandCursor)
        self.btn_vender_flota_tab.setStyleSheet(self._estilo_btn("rojo"))
        self.btn_vender_flota_tab.setToolTip(
            "<div style='max-width: 260px;'>Vende todos los camiones usados de flota adquiridos desde el launcher "
            "(protege tu camión activo y camiones oficiales/mods comprados a mano) y reembolsa su valor a tu cuenta.</div>"
        )
        self.btn_vender_flota_tab.clicked.connect(self._action_vender_toda_la_flota)

        fila_tit.addWidget(self.lbl_tit_camiones)
        fila_tit.addStretch()
        fila_tit.addWidget(self.btn_comprar_variados_tab)
        fila_tit.addWidget(self.btn_vender_flota_tab)
        lay_top.addLayout(fila_tit)

        fila_info = QHBoxLayout()
        fila_info.setSpacing(14)

        self.lbl_badge_dinero_camiones = QLabel(f"{tr('Dinero disponible:')} $0")
        self.lbl_badge_dinero_camiones.setStyleSheet(
            f"color: {VERDE_TXT}; font-size: 13px; font-weight: 800; background: transparent; border: none; padding: 0px;"
        )

        self.lbl_resumen_flota_tab = QLabel(f"{tr('Camiones en garajes:')} 0  ·  {tr('Espacios libres para comprar:')} 0")
        self.lbl_resumen_flota_tab.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: 700;")
        self.lbl_resumen_flota_tab.setToolTip(
            "<div style='max-width: 280px;'>Muestra cuántos camiones de flota tienes actualmente en tus garajes "
            "y cuántos espacios vacíos te quedan para comprar nuevos camiones.</div>"
        )

        self.lbl_motivo_compra_camiones = QLabel("")
        self.lbl_motivo_compra_camiones.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_motivo_compra_camiones.setStyleSheet(f"color: {AMBAR_TXT}; font-size: 11px; font-weight: 700;")

        fila_info.addWidget(self.lbl_badge_dinero_camiones)
        fila_info.addWidget(self.lbl_resumen_flota_tab)
        fila_info.addStretch()
        fila_info.addWidget(self.lbl_motivo_compra_camiones)
        lay_top.addLayout(fila_info)

        lay.addWidget(card_top)

        # --- Lista de modelos con scroll ---
        marco_lista = QFrame()
        marco_lista.setObjectName("marcoListaCamiones")
        marco_lista.setStyleSheet(
            "QFrame#marcoListaCamiones { background: #11161B; border: 1px solid #262932; border-radius: 8px; }"
        )
        lay_marco = QVBoxLayout(marco_lista)
        lay_marco.setContentsMargins(0, 0, 0, 0)
        lay_marco.setSpacing(0)

        self.scroll_camiones = QScrollArea()
        self.scroll_camiones.setWidgetResizable(True)
        self.scroll_camiones.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_camiones.setStyleSheet("""
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

        self.contenedor_lista_camiones = QWidget()
        self.contenedor_lista_camiones.setStyleSheet("background: transparent;")
        self.lay_lista_camiones = QVBoxLayout(self.contenedor_lista_camiones)
        self.lay_lista_camiones.setContentsMargins(10, 8, 10, 8)
        self.lay_lista_camiones.setSpacing(6)
        self.scroll_camiones.setWidget(self.contenedor_lista_camiones)
        lay_marco.addWidget(self.scroll_camiones, 1)

        lay.addWidget(marco_lista, 1)
        return w

    def _obtener_modelos_unicos(self, ofertas: list) -> list:
        ofertas_unicas = {}
        for of in ofertas:
            clave_m = (of.get("brand_id", ""), of.get("model_id", ""))
            if clave_m not in ofertas_unicas or int(of.get("price", 0)) < int(ofertas_unicas[clave_m].get("price", 0)):
                ofertas_unicas[clave_m] = of
        return list(ofertas_unicas.values())

    def _refrescar_camiones_flota(self, datos: dict):
        dinero = int(datos.get("money", 0))
        plazas_libres = int(datos.get("free_truck_slots", 0))
        total_en_garajes = int(datos.get("company_trucks_count", 0))
        ofertas = datos.get("used_trucks", [])
        lista_modelos = self._obtener_modelos_unicos(ofertas)

        precio_min = min((int(o.get("price", 0)) for o in lista_modelos if int(o.get("price", 0)) > 0), default=0)
        alcanza_alguno = len(lista_modelos) > 0 and dinero >= precio_min

        # Indicador de dinero
        self.lbl_badge_dinero_camiones.setText(f"{tr('Dinero disponible:')} ${dinero:,}")
        if alcanza_alguno or not lista_modelos:
            self.lbl_badge_dinero_camiones.setStyleSheet(
                f"color: {VERDE_TXT}; font-size: 13px; font-weight: 800; background: transparent; border: none; padding: 0px;"
            )
        else:
            self.lbl_badge_dinero_camiones.setStyleSheet(
                f"color: {ROJO_TXT}; font-size: 13px; font-weight: 800; background: transparent; border: none; padding: 0px;"
            )

        self.lbl_resumen_flota_tab.setText(
            f"{tr('Camiones en garajes:')} {total_en_garajes}  ·  {tr('Espacios libres para comprar:')} {plazas_libres}"
        )

        # Motivo por el que no se puede comprar
        if not lista_modelos:
            self.lbl_motivo_compra_camiones.setText(tr("Sin ofertas disponibles"))
            self.lbl_motivo_compra_camiones.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700;")
        elif plazas_libres <= 0:
            self.lbl_motivo_compra_camiones.setText(tr("Garajes llenos: amplía o compra otro garaje"))
            self.lbl_motivo_compra_camiones.setStyleSheet(
                f"color: {AMBAR_TXT}; background: #221B11; border: 1px solid #B45309; border-radius: 5px; "
                f"font-size: 11px; font-weight: 700; padding: 3px 8px;"
            )
        elif not alcanza_alguno:
            self.lbl_motivo_compra_camiones.setText(f"{tr('Dinero insuficiente')} (mín. ${precio_min:,})")
            self.lbl_motivo_compra_camiones.setStyleSheet(
                f"color: {ROJO_TXT}; background: #24161A; border: 1px solid #B91C1C; border-radius: 5px; "
                f"font-size: 11px; font-weight: 700; padding: 3px 8px;"
            )
        else:
            self.lbl_motivo_compra_camiones.setText("")
            self.lbl_motivo_compra_camiones.setStyleSheet("background: transparent; border: none;")

        puede_var = plazas_libres > 0 and alcanza_alguno
        puede_vender_todo = total_en_garajes > 0
        self.btn_comprar_variados_tab.setProperty("bloqueado_por_estado", not puede_var)
        self.btn_comprar_variados_tab.setEnabled(puede_var)
        self.btn_vender_flota_tab.setProperty("bloqueado_por_estado", not puede_vender_todo)
        self.btn_vender_flota_tab.setEnabled(puede_vender_todo)

        # Si los modelos no cambiaron, solo se actualizan las filas existentes (sin reconstruir)
        claves_actuales = [f["clave"] for f in getattr(self, "filas_camiones", [])]
        claves_nuevas = [(o.get("brand_id", ""), o.get("model_id", "")) for o in lista_modelos]

        if self.filas_camiones and claves_actuales == claves_nuevas:
            for info_f, of in zip(self.filas_camiones, lista_modelos):
                self._actualizar_fila_camion_existente(info_f, of, dinero, plazas_libres)
            return

        self._poblar_filas_camiones(lista_modelos, dinero, plazas_libres)

    def _poblar_filas_camiones(self, lista_modelos: list, dinero: int, plazas_libres: int):
        self.contenedor_lista_camiones.setUpdatesEnabled(False)
        try:
            while self.lay_lista_camiones.count():
                item = self.lay_lista_camiones.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
            self.filas_camiones.clear()

            if not lista_modelos:
                w_vacio = QFrame()
                w_vacio.setStyleSheet(
                    "QFrame { background: #13171E; border: 1px dashed #2A3241; border-radius: 8px; padding: 26px; margin: 15px; }"
                    "QLabel { background: transparent; border: none; }"
                )
                lay_vacio = QVBoxLayout(w_vacio)
                lay_vacio.setAlignment(Qt.AlignCenter)
                lay_vacio.setSpacing(12)

                lbl_tit = QLabel(tr("No hay ofertas de camiones disponibles en esta partida guardada"))
                lbl_tit.setAlignment(Qt.AlignCenter)
                lbl_tit.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800;")

                lbl_desc = QLabel(
                    "Ve a la sección de <b>Exploración y Mapa</b> y desbloquea concesionarios de camiones<br>"
                    "para que los concesionarios generen modelos listos para comprar y llenar tus garajes."
                )
                lbl_desc.setTextFormat(Qt.RichText)
                lbl_desc.setAlignment(Qt.AlignCenter)
                lbl_desc.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 13px; line-height: 1.4;")

                btn_ir = QPushButton(tr("Ir a la sección Exploración y Mapa →"))
                btn_ir.setFixedHeight(34)
                btn_ir.setCursor(Qt.PointingHandCursor)
                btn_ir.setStyleSheet(self._estilo_btn("azul"))
                btn_ir.clicked.connect(self._ir_a_tab_empresa)

                lay_vacio.addWidget(lbl_tit)
                lay_vacio.addWidget(lbl_desc)
                lay_vacio.addWidget(btn_ir, 0, Qt.AlignCenter)

                self.lay_lista_camiones.addWidget(w_vacio)
                self.lay_lista_camiones.addStretch()
                return

            for of in lista_modelos:
                fila = QFrame()
                fila.setFixedHeight(46)
                fila.setMinimumWidth(820)
                fila.setStyleSheet(
                    "QFrame { background: #181A20; border: 1px solid #23262F; border-radius: 6px; }"
                    "QLabel { background: transparent; border: none; padding: 0px; }"
                )
                lay_f = QHBoxLayout(fila)
                lay_f.setContentsMargins(14, 6, 12, 6)
                lay_f.setSpacing(10)

                nombre = of.get("name", "Camión Usado")
                lbl_nom = QLabel(nombre)
                lbl_nom.setFixedHeight(22)
                lbl_nom.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 800;")

                lbl_comprados = QLabel()
                lbl_comprados.setFixedWidth(105)
                lbl_comprados.setAlignment(Qt.AlignCenter)

                lbl_precio = QLabel()
                lbl_precio.setFixedWidth(88)
                lbl_precio.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                spn_cant = QSpinBox()
                spn_cant.setStyleSheet(ESTILO_SPIN_CAMION)
                spn_cant.setFixedSize(62, 28)

                btn_comprar = QPushButton("Comprar")
                btn_comprar.setFixedSize(82, 28)
                btn_comprar.setCursor(Qt.PointingHandCursor)
                btn_comprar.setStyleSheet(self._estilo_btn("azul", compacto=True))

                btn_max = QPushButton("Comprar Máx.")
                btn_max.setFixedSize(98, 28)
                btn_max.setCursor(Qt.PointingHandCursor)
                btn_max.setStyleSheet(self._estilo_btn("verde", compacto=True))

                btn_vender = QPushButton("Vender")
                btn_vender.setProperty("ms_exito", 450)
                btn_vender.setFixedSize(76, 28)
                btn_vender.setCursor(Qt.PointingHandCursor)

                info_f = {
                    "clave": (of.get("brand_id", ""), of.get("model_id", "")),
                    "offer_id": of.get("offer_id", ""),
                    "brand_id": of.get("brand_id", ""),
                    "model_id": of.get("model_id", ""),
                    "price": max(1, int(of.get("price", 45000))),
                    "max_comprar": 0,
                    "lbl_comprados": lbl_comprados,
                    "lbl_precio": lbl_precio,
                    "spn_cant": spn_cant,
                    "btn_comprar": btn_comprar,
                    "btn_max": btn_max,
                    "btn_vender": btn_vender,
                }

                def _comprar_cant(_, inf=info_f):
                    inf["spn_cant"].interpretText()
                    self._action_comprar_modelo_tab(inf["offer_id"], inf["spn_cant"].value(), inf["btn_comprar"])

                def _vender_cant(_, inf=info_f):
                    inf["spn_cant"].interpretText()
                    self._action_vender_modelo_tab(inf["brand_id"], inf["model_id"], inf["spn_cant"].value(),
                                                   inf["price"], inf["btn_vender"])

                btn_comprar.clicked.connect(_comprar_cant)
                btn_max.clicked.connect(
                    lambda _, inf=info_f: self._action_comprar_modelo_tab(inf["offer_id"], inf["max_comprar"], inf["btn_max"])
                )
                btn_vender.clicked.connect(_vender_cant)

                self._actualizar_fila_camion_existente(info_f, of, dinero, plazas_libres)

                lay_f.addWidget(lbl_nom, 1)
                lay_f.addWidget(lbl_comprados)
                lay_f.addWidget(lbl_precio)
                lay_f.addWidget(spn_cant)
                lay_f.addWidget(btn_comprar)
                lay_f.addWidget(btn_max)
                lay_f.addWidget(btn_vender)

                self.lay_lista_camiones.addWidget(fila)
                self.filas_camiones.append(info_f)

            self.lay_lista_camiones.addStretch()
        finally:
            self.contenedor_lista_camiones.setUpdatesEnabled(True)

    def _actualizar_fila_camion_existente(self, info_f: dict, of: dict, dinero: int, plazas_libres: int):
        precio = max(1, int(of.get("price", 45000)))
        en_flota = int(of.get("owned_count", 0))
        max_comprar = min(plazas_libres, dinero // precio) if plazas_libres > 0 else 0
        max_spin = max(1, max(max_comprar, en_flota))

        info_f["offer_id"] = of.get("offer_id", "")
        info_f["price"] = precio
        info_f["max_comprar"] = max_comprar
        info_f["en_flota"] = en_flota

        lbl_comprados = info_f["lbl_comprados"]
        lbl_comprados.setText(f"{tr('Comprados:')} {en_flota}")
        color_comp = AZUL_TXT if en_flota > 0 else "#64748B"
        lbl_comprados.setStyleSheet(
            f"color: {color_comp}; background: #13161D; border: 1px solid #252A36; border-radius: 5px; "
            f"font-size: 11px; font-weight: 800; padding: 3px 6px;"
        )

        lbl_precio = info_f["lbl_precio"]
        lbl_precio.setText(f"${precio:,}")
        lbl_precio.setStyleSheet(
            f"color: {VERDE_TXT if dinero >= precio else AMBAR_TXT}; font-size: 13px; font-weight: 900;"
        )

        spn = info_f["spn_cant"]
        val_prev = spn.value()
        spn.setRange(1, max_spin)
        spn.setValue(min(max(1, val_prev), max_spin))
        spn.setEnabled(max_comprar > 0 or en_flota > 0)

        btn_comprar = info_f["btn_comprar"]
        btn_max = info_f["btn_max"]
        btn_vender = info_f["btn_vender"]

        btn_comprar.setText(tr("Comprar"))
        btn_max.setText(tr("Comprar Máx."))
        btn_vender.setText(tr("Vender"))

        btn_comprar.setProperty("bloqueado_por_estado", max_comprar <= 0)
        btn_max.setProperty("bloqueado_por_estado", max_comprar <= 0)
        btn_comprar.setEnabled(max_comprar > 0)
        btn_max.setEnabled(max_comprar > 0)

        if max_comprar <= 0:
            if plazas_libres <= 0:
                motivo_tt = "No puedes comprar más camiones porque no tienes espacios libres en tus garajes."
            else:
                faltante = max(0, precio - dinero)
                motivo_tt = f"Dinero insuficiente: necesitas ${precio:,} (te faltan ${faltante:,})."
            btn_comprar.setToolTip(f"<div style='max-width: 240px;'>{motivo_tt}</div>")
            btn_max.setToolTip(f"<div style='max-width: 240px;'>{motivo_tt}</div>")
        else:
            btn_comprar.setToolTip(
                "<div style='max-width: 240px;'>Compra la cantidad seleccionada de este camión "
                "y los guarda en tus garajes libres.</div>"
            )
            btn_max.setToolTip(
                f"<div style='max-width: 240px;'>Compra hasta {max_comprar} unidades de este modelo "
                f"según tu dinero y espacio libre en garajes.</div>"
            )

        btn_vender.setStyleSheet(self._estilo_btn("rojo" if en_flota > 0 else "vender_off", compacto=True))
        btn_vender.setProperty("bloqueado_por_estado", en_flota <= 0)
        btn_vender.setEnabled(en_flota > 0)
        btn_vender.setToolTip(
            "<div style='max-width: 240px;'>Vende la cantidad indicada en el selector de este modelo "
            "de camión que tengas en tus garajes.</div>"
        )

    def _ir_a_tab_empresa(self):
        if hasattr(self, "tabs") and self.tabs is not None:
            for i in range(self.tabs.count()):
                tab_t = self.tabs.tabText(i)
                if "Exploración" in tab_t or "Empresa" in tab_t:
                    self.tabs.setCurrentIndex(i)
                    return

    def _siguiente_clave_camion(self, prefijo: str) -> str:
        seq = getattr(self, "_secuencia_cola", 0) + 1
        self._secuencia_cola = seq
        return f"{prefijo}_{seq}"

    def _action_comprar_modelo_tab(self, offer_id: str, cantidad: int, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or cantidad <= 0 or not self._juego_cerrado_o_alertar():
            return

        # Actualizacion optimista de la UI antes de guardar en segundo plano
        datos = self.datos_partida_actual
        ofertas = datos.get("used_trucks", [])
        oferta_obj = next((o for o in ofertas if o.get("offer_id") == offer_id), None)
        if oferta_obj is not None:
            precio = max(0, int(oferta_obj.get("price", 0)))
            dinero = max(0, int(datos.get("money", 0)))
            plazas = max(0, int(datos.get("free_truck_slots", 0)))
            max_dinero = dinero // precio if precio > 0 else cantidad
            n_real = min(int(cantidad), plazas, max_dinero)
            if n_real > 0:
                datos["money"] = max(0, dinero - n_real * precio)
                datos["free_truck_slots"] = max(0, plazas - n_real)
                datos["company_trucks_count"] = max(0, int(datos.get("company_trucks_count", 0)) + n_real)
                datos["empty_trucks_count"] = max(0, int(datos.get("empty_trucks_count", 0)) + n_real)
                clave_m = (oferta_obj.get("brand_id", ""), oferta_obj.get("model_id", ""))
                for of in ofertas:
                    if (of.get("brand_id", ""), of.get("model_id", "")) == clave_m:
                        of["owned_count"] = int(of.get("owned_count", 0)) + n_real
                self._marcar_otras_tabs_sucias()
                self._refrescar_camiones_flota(datos)
                notificar_exito_boton(boton, "¡Comprado!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_camion("cam_buy"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g, oid=offer_id, cant=cantidad: profile_manager.comprar_camiones_usados(r, [(oid, cant)]),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True
        )

    def _action_vender_modelo_tab(self, brand_id: str, model_id: str, cantidad: int, precio: int, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or cantidad <= 0 or not self._juego_cerrado_o_alertar():
            return

        datos = self.datos_partida_actual
        ofertas = datos.get("used_trucks", [])
        clave_m = (brand_id, model_id)
        owned_actual = max((int(of.get("owned_count", 0)) for of in ofertas
                            if (of.get("brand_id", ""), of.get("model_id", "")) == clave_m), default=0)
        n_real = min(int(cantidad), owned_actual)
        if n_real > 0:
            reembolso_u = max(10000, int(max(1, int(precio)) * 0.7))
            datos["money"] = max(0, int(datos.get("money", 0))) + n_real * reembolso_u
            datos["company_trucks_count"] = max(0, int(datos.get("company_trucks_count", 0)) - n_real)
            datos["free_truck_slots"] = max(0, int(datos.get("free_truck_slots", 0)) + n_real)
            for of in ofertas:
                if (of.get("brand_id", ""), of.get("model_id", "")) == clave_m:
                    of["owned_count"] = max(0, int(of.get("owned_count", 0)) - n_real)
            self._marcar_otras_tabs_sucias()
            self._refrescar_camiones_flota(datos)
            notificar_exito_boton(boton, "¡Vendido!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_camion("cam_sell"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g, b=brand_id, m=model_id, c=cantidad, p=precio: profile_manager.vender_camiones_flota(
                r, brand_id=b, model_id=m, cantidad=c, precio_unitario=p
            ),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True
        )

    def _action_comprar_flota_variada(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or not self._juego_cerrado_o_alertar():
            return

        # Simulacion local de la compra variada para refrescar la UI al instante
        datos = self.datos_partida_actual
        usados = datos.get("used_trucks", [])
        plazas = max(0, int(datos.get("free_truck_slots", 0)))
        saldo = max(0, int(datos.get("money", 0)))
        if usados and plazas > 0:
            por_modelo = {}
            gasto = 0
            comprados = 0
            while comprados < plazas:
                progreso = False
                for u in usados:
                    if comprados >= plazas:
                        break
                    p_u = max(0, int(u.get("price", 0)))
                    if gasto + p_u <= saldo:
                        km = (u.get("brand_id", ""), u.get("model_id", ""))
                        por_modelo[km] = por_modelo.get(km, 0) + 1
                        gasto += p_u
                        comprados += 1
                        progreso = True
                if not progreso:
                    break
            if comprados > 0:
                datos["money"] = max(0, saldo - gasto)
                datos["free_truck_slots"] = max(0, plazas - comprados)
                datos["company_trucks_count"] = max(0, int(datos.get("company_trucks_count", 0)) + comprados)
                datos["empty_trucks_count"] = max(0, int(datos.get("empty_trucks_count", 0)) + comprados)
                for of in usados:
                    km = (of.get("brand_id", ""), of.get("model_id", ""))
                    if km in por_modelo:
                        of["owned_count"] = int(of.get("owned_count", 0)) + por_modelo[km]
                self._marcar_otras_tabs_sucias()
                self._refrescar_camiones_flota(datos)
                notificar_exito_boton(self.btn_comprar_variados_tab, "¡Flota Comprada!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_camion("cam_buy_var"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g: profile_manager.comprar_camiones_usados_variados(r),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True
        )

    def _action_vender_toda_la_flota(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        resp = QMessageBox.question(
            self,
            "Confirmar venta de camiones",
            "¿Deseas vender todos los camiones de flota comprados desde el launcher?\n\n"
            "• Tu camión personal activo está 100% protegido.\n"
            "• Los camiones de mods o comprados manualmente en concesionarios no se tocarán.\n"
            "• Si tenían conductores asignados, estos quedarán en el garaje listos para un nuevo camión.\n\n"
            "El dinero de la venta se sumará a tu cuenta bancaria.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if resp != QMessageBox.Yes:
            return
        if not self._juego_cerrado_o_alertar():
            return

        datos = self.datos_partida_actual
        total_comp = max(0, int(datos.get("company_trucks_count", 0)))
        if total_comp > 0:
            reembolso_est = 0
            vistos_mod = set()
            cont_usados = 0
            for of in datos.get("used_trucks", []):
                km = (of.get("brand_id", ""), of.get("model_id", ""))
                if km not in vistos_mod:
                    vistos_mod.add(km)
                    own = max(0, int(of.get("owned_count", 0)))
                    cont_usados += own
                    reembolso_est += own * max(10000, int(max(1, int(of.get("price", 45000))) * 0.7))
                of["owned_count"] = 0
            if total_comp > cont_usados:
                reembolso_est += (total_comp - cont_usados) * 35000
            datos["money"] = max(0, int(datos.get("money", 0))) + reembolso_est
            datos["free_truck_slots"] = max(0, int(datos.get("free_truck_slots", 0)) + total_comp)
            datos["company_trucks_count"] = 0
            datos["empty_trucks_count"] = 0
            drv_con_trk = max(0, int(datos.get("drivers_with_truck_count", 0)))
            datos["idle_hired_drivers_count"] = max(0, int(datos.get("idle_hired_drivers_count", 0)) + drv_con_trk)
            datos["drivers_with_truck_count"] = 0
            self._marcar_otras_tabs_sucias()
            self._refrescar_camiones_flota(datos)
            notificar_exito_boton(self.btn_vender_flota_tab, "¡Vendidos!")

        self._encolar_edicion_ligera_async(
            self._siguiente_clave_camion("cam_sell_all"),
            ruta_g,
            tr("Guardando..."),
            lambda r=ruta_g: profile_manager.vender_camiones_flota(r),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
            reconciliar=True
        )

    def _actualizar_idioma_tab_camiones(self):
        """Actualiza todos los textos estáticos y dinámicos de la pestaña Camiones."""
        if hasattr(self, "lbl_tit_camiones") and self.lbl_tit_camiones:
            self.lbl_tit_camiones.setText(tr("Concesionario de Camiones Usados y Flota en Garajes"))
        if hasattr(self, "btn_comprar_variados_tab") and self.btn_comprar_variados_tab:
            self.btn_comprar_variados_tab.setText(tr("Comprar Camiones Variados para Llenar Garajes"))
        if hasattr(self, "btn_vender_flota_tab") and self.btn_vender_flota_tab:
            self.btn_vender_flota_tab.setText(tr("Vender Todos los Camiones"))

        for inf in getattr(self, "filas_camiones", []):
            if "btn_comprar" in inf and inf["btn_comprar"]:
                inf["btn_comprar"].setText(tr("Comprar"))
            if "btn_max" in inf and inf["btn_max"]:
                inf["btn_max"].setText(tr("Comprar Máx."))
            if "btn_vender" in inf and inf["btn_vender"]:
                inf["btn_vender"].setText(tr("Vender"))
            if "lbl_comprados" in inf and inf["lbl_comprados"]:
                en_flota = inf.get("en_flota", 0)
                inf["lbl_comprados"].setText(f"{tr('Comprados:')} {en_flota}")

        if hasattr(self, "datos_partida_actual") and self.datos_partida_actual:
            self._refrescar_camiones_flota(self.datos_partida_actual)

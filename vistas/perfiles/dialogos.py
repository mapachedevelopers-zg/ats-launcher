import threading
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QDialog,
                               QScrollArea, QWidget, QFrame)
from PySide6.QtCore import Qt, QLocale, QObject, Signal
import profile_manager
from i18n import tr
from .comun import (QMessageBox, estilo_boton, notificar_exito_boton, VERDE_TXT, AZUL_TXT,
                    AMBAR_TXT, TXT_PRINCIPAL, TXT_SECUNDARIO, NEUTRO_BORDE)


# =============================================================================
# Utilidades de entrada numerica
# =============================================================================

def configurar_formato_millares_en_vivo(spn: QSpinBox, callback_cambio=None, max_val: int = 2000000000):
    """Mantiene las comas de miles y millones recalculadas dinámicamente en tiempo real mientras el usuario escribe."""
    le = spn.lineEdit()
    if not le:
        return

    def _al_editar_texto(texto_actual):
        pos_cursor = le.cursorPosition()
        digitos_antes = sum(1 for c in texto_actual[:pos_cursor] if c.isdigit())
        solo_digitos = "".join(c for c in texto_actual if c.isdigit())

        if not solo_digitos:
            val = 0
            nuevo = ""
        else:
            val = min(max_val, int(solo_digitos))
            nuevo = f"{val:,}"

        spn.blockSignals(True)
        spn.setValue(val)
        spn.blockSignals(False)

        le.blockSignals(True)
        le.setText(nuevo)
        nueva_pos = 0
        cont = 0
        for i, ch in enumerate(nuevo):
            if ch.isdigit():
                cont += 1
            nueva_pos = i + 1
            if cont >= digitos_antes:
                break
        le.setCursorPosition(nueva_pos)
        le.blockSignals(False)

        if callback_cambio:
            callback_cambio(val)

    le.textEdited.connect(_al_editar_texto)


class DialogoDinero(QDialog):
    def __init__(self, saldo_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Cambiar Dinero"))
        self.setFixedSize(380, 200)
        self.setStyleSheet(f"background: #11161B; color: {TXT_PRINCIPAL};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lbl = QLabel(tr("Añade la cantidad exacta de dinero en dólares para tu perfil:"))
        lbl.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 13px;")

        fila_input = QHBoxLayout()
        fila_input.setSpacing(8)

        self.spn_dinero = QSpinBox()
        self.spn_dinero.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.spn_dinero.setRange(0, 2000000000)
        self.spn_dinero.setGroupSeparatorShown(True)
        self.spn_dinero.setValue(min(2000000000, max(0, int(saldo_actual))))
        self.spn_dinero.setFixedHeight(40)
        self.spn_dinero.setStyleSheet(f"""
            QSpinBox {{
                background: #12161D; color: {VERDE_TXT}; font-size: 15px; font-weight: 800;
                border: 1px solid {NEUTRO_BORDE}; border-radius: 6px; padding-left: 10px;
            }}
            QSpinBox:focus {{
                border: 1px solid #2563EB;
            }}
        """)
        configurar_formato_millares_en_vivo(self.spn_dinero)

        lbl_unidad = QLabel("USD")
        lbl_unidad.setFixedHeight(40)
        lbl_unidad.setFixedWidth(54)
        lbl_unidad.setAlignment(Qt.AlignCenter)
        lbl_unidad.setStyleSheet(f"""
            background: #161B22; color: {VERDE_TXT}; font-size: 12px; font-weight: 800;
            border: 1px solid {NEUTRO_BORDE}; border-radius: 6px;
        """)

        fila_input.addWidget(self.spn_dinero, 1)
        fila_input.addWidget(lbl_unidad)

        lay_btns = QHBoxLayout()
        btn_cerrar = QPushButton(tr("Cerrar"))
        btn_cerrar.setFixedHeight(34)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(estilo_boton("rojo"))
        btn_cerrar.setAutoDefault(False)
        btn_cerrar.setDefault(False)
        btn_cerrar.clicked.connect(self.reject)

        btn_aplicar = QPushButton(tr("Aplicar"))
        btn_aplicar.setFixedHeight(34)
        btn_aplicar.setCursor(Qt.PointingHandCursor)
        btn_aplicar.setStyleSheet(estilo_boton("verde"))
        btn_aplicar.setAutoDefault(True)
        btn_aplicar.setDefault(True)
        btn_aplicar.clicked.connect(self.accept)

        lay_btns.addWidget(btn_cerrar)
        lay_btns.addStretch()
        lay_btns.addWidget(btn_aplicar)

        lay.addWidget(lbl)
        lay.addLayout(fila_input)
        lay.addLayout(lay_btns)

        # Seleccionar todo para que el usuario pueda escribir directamente
        if self.spn_dinero.lineEdit():
            self.spn_dinero.lineEdit().selectAll()
        self.spn_dinero.setFocus()

    def accept(self):
        self.spn_dinero.interpretText()
        super().accept()


class DialogoExperiencia(QDialog):
    def __init__(self, xp_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Cambiar Experiencia"))
        self.setFixedSize(380, 220)
        self.setStyleSheet(f"background: #11161B; color: {TXT_PRINCIPAL};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        lbl = QLabel(tr("Introduce la cantidad exacta de puntos de experiencia:"))
        lbl.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 13px;")

        fila_input = QHBoxLayout()
        fila_input.setSpacing(8)

        self.spn_xp = QSpinBox()
        self.spn_xp.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.spn_xp.setRange(0, 2000000000)
        self.spn_xp.setGroupSeparatorShown(True)
        self.spn_xp.setValue(min(2000000000, max(0, int(xp_actual))))
        self.spn_xp.setFixedHeight(40)
        self.spn_xp.setStyleSheet(f"""
            QSpinBox {{
                background: #12161D; color: {AZUL_TXT}; font-size: 15px; font-weight: 800;
                border: 1px solid {NEUTRO_BORDE}; border-radius: 6px; padding-left: 10px;
            }}
            QSpinBox:focus {{
                border: 1px solid #2563EB;
            }}
        """)
        configurar_formato_millares_en_vivo(self.spn_xp, callback_cambio=self._actualizar_preview)

        lbl_unidad = QLabel("PE")
        lbl_unidad.setFixedHeight(40)
        lbl_unidad.setFixedWidth(54)
        lbl_unidad.setAlignment(Qt.AlignCenter)
        lbl_unidad.setStyleSheet(f"""
            background: #161B22; color: {AZUL_TXT}; font-size: 12px; font-weight: 800;
            border: 1px solid {NEUTRO_BORDE}; border-radius: 6px;
        """)

        fila_input.addWidget(self.spn_xp, 1)
        fila_input.addWidget(lbl_unidad)

        self.lbl_preview_nivel = QLabel()
        self.lbl_preview_nivel.setStyleSheet(f"color: {VERDE_TXT}; font-weight: 800; font-size: 12px;")
        self.spn_xp.valueChanged.connect(self._actualizar_preview)
        self._actualizar_preview(xp_actual)

        lay_btns = QHBoxLayout()
        btn_cerrar = QPushButton(tr("Cerrar"))
        btn_cerrar.setFixedHeight(34)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(estilo_boton("rojo"))
        btn_cerrar.setAutoDefault(False)
        btn_cerrar.setDefault(False)
        btn_cerrar.clicked.connect(self.reject)

        btn_aplicar = QPushButton(tr("Aplicar"))
        btn_aplicar.setFixedHeight(34)
        btn_aplicar.setCursor(Qt.PointingHandCursor)
        btn_aplicar.setStyleSheet(estilo_boton("azul"))
        btn_aplicar.setAutoDefault(True)
        btn_aplicar.setDefault(True)
        btn_aplicar.clicked.connect(self.accept)

        lay_btns.addWidget(btn_cerrar)
        lay_btns.addStretch()
        lay_btns.addWidget(btn_aplicar)

        lay.addWidget(lbl)
        lay.addLayout(fila_input)
        lay.addWidget(self.lbl_preview_nivel)
        lay.addLayout(lay_btns)

        # Seleccionar todo para que el usuario pueda escribir directamente
        if self.spn_xp.lineEdit():
            self.spn_xp.lineEdit().selectAll()
        self.spn_xp.setFocus()

    def accept(self):
        self.spn_xp.interpretText()
        super().accept()

    def _actualizar_preview(self, val):
        lvl, prog, req = profile_manager.calcular_nivel_ats(val)
        self.lbl_preview_nivel.setText(f"{tr('Nivel Resultante:')} {lvl}  ·  {prog:,} {tr('de')} {req:,} PE")


class _SeñalesCatalogo(QObject):
    compra_terminada = Signal(bool, str, dict, object, str)


class DialogoCamionesUsados(QDialog):
    """Ventana modal para inspeccionar y comprar camiones usados del concesionario de la partida."""

    def __init__(self, ruta_guardado: str, datos_partida: dict, callback_refrescar=None, parent=None):
        super().__init__(parent)
        self.ruta_guardado = ruta_guardado
        self.datos_partida = datos_partida
        self.callback_refrescar = callback_refrescar
        self.hubo_compras = False
        self._compra_en_curso = False
        self._señales = _SeñalesCatalogo(self)
        self._señales.compra_terminada.connect(self._on_compra_terminada)

        self.setWindowTitle("Catálogo de Camiones Usados para tus Garajes")
        self.setMinimumSize(940, 560)
        self.resize(980, 580)
        self.setStyleSheet(f"background: #11161B; color: {TXT_PRINCIPAL};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        # --- Cabecera con resumen ---
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }"
            "QLabel { background: transparent; border: none; }"
        )
        lay_h = QVBoxLayout(header)
        lay_h.setContentsMargins(14, 10, 14, 10)
        lay_h.setSpacing(6)

        fila_top = QHBoxLayout()
        lbl_tit = QLabel("Concesionario de Camiones Usados de esta Partida")
        lbl_tit.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800;")
        fila_top.addWidget(lbl_tit)
        fila_top.addStretch()

        self.btn_variados = QPushButton("Comprar Camiones Variados para Llenar Garajes")
        self.btn_variados.setFixedHeight(30)
        self.btn_variados.setCursor(Qt.PointingHandCursor)
        self.btn_variados.setStyleSheet(estilo_boton("verde"))
        self.btn_variados.setAutoDefault(False)
        self.btn_variados.setDefault(False)
        self.btn_variados.setToolTip(
            "<div style='max-width: 260px;'>Compra automáticamente una combinación variada de estos camiones usados "
            "hasta llenar tus plazas libres o hasta donde alcance tu dinero.</div>"
        )
        self.btn_variados.clicked.connect(self._action_comprar_variados)
        fila_top.addWidget(self.btn_variados)
        lay_h.addLayout(fila_top)

        self.lbl_info_resumen = QLabel("")
        self.lbl_info_resumen.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: 600;")
        lay_h.addWidget(self.lbl_info_resumen)
        lay.addWidget(header)

        # --- Lista con scroll ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: #13151B; border: 1px solid #262932; border-radius: 8px; }
            QScrollBar:vertical { background: #13151B; width: 10px; border-radius: 5px; margin: 2px; }
            QScrollBar::handle:vertical { background: #2E3440; border-radius: 5px; min-height: 24px; }
            QScrollBar::handle:vertical:hover { background: #3B82F6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.contenedor_lista = QWidget()
        self.contenedor_lista.setStyleSheet("background: transparent;")
        self.lay_lista = QVBoxLayout(self.contenedor_lista)
        self.lay_lista.setContentsMargins(10, 10, 10, 10)
        self.lay_lista.setSpacing(8)
        self.scroll.setWidget(self.contenedor_lista)
        lay.addWidget(self.scroll, 1)

        # --- Pie ---
        fila_pie = QHBoxLayout()
        lbl_nota = QLabel("Todos los camiones comprados se entregan reparados al 100% y con el tanque lleno en tus garajes.")
        lbl_nota.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 11px;")
        btn_cerrar = QPushButton("Cerrar Catálogo")
        btn_cerrar.setFixedSize(140, 32)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet(estilo_boton("neutro"))
        btn_cerrar.setAutoDefault(True)
        btn_cerrar.setDefault(True)
        btn_cerrar.setFocus()
        btn_cerrar.clicked.connect(self.accept)

        fila_pie.addWidget(lbl_nota)
        fila_pie.addStretch()
        fila_pie.addWidget(btn_cerrar)
        lay.addLayout(fila_pie)

        self._construir_lista()

    def _recargar_datos_locales(self):
        self.datos_partida = profile_manager.leer_datos_partida(self.ruta_guardado)
        if self.callback_refrescar:
            self.callback_refrescar(self.datos_partida)
        self._construir_lista()

    def _construir_lista(self):
        while self.lay_lista.count():
            item = self.lay_lista.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        dinero = int(self.datos_partida.get("money", 0))
        plazas_libres = int(self.datos_partida.get("free_truck_slots", 0))
        ofertas = self.datos_partida.get("used_trucks", [])

        self.lbl_info_resumen.setText(
            f"Dinero disponible: ${dinero:,}   ·   Espacios libres para camiones en garajes: {plazas_libres}"
            f"   ·   Modelos usados en oferta: {len(ofertas)}"
        )

        precio_min = min((int(o.get("price", 0)) for o in ofertas if int(o.get("price", 0)) > 0), default=0)
        puede_comprar_algo = plazas_libres > 0 and len(ofertas) > 0 and dinero >= precio_min
        self.btn_variados.setEnabled(puede_comprar_algo)

        if not ofertas:
            lbl_vacio = QLabel("No se encontraron ofertas de camiones usados en esta partida guardada.")
            lbl_vacio.setAlignment(Qt.AlignCenter)
            lbl_vacio.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 13px; padding: 30px;")
            self.lay_lista.addWidget(lbl_vacio)
            self.lay_lista.addStretch()
            return

        estilo_spin = (
            "QSpinBox { background: #12141A; color: #F8FAFC; border: 1px solid #2B303C; "
            "border-radius: 6px; padding: 2px 6px; font-size: 12px; font-weight: bold; }"
        )

        for of in ofertas:
            fila = QFrame()
            fila.setFixedHeight(62)
            fila.setStyleSheet(
                "QFrame { background: #1A1D24; border: 1px solid #262932; border-radius: 6px; }"
                "QLabel { background: transparent; border: none; }"
            )
            lay_f = QHBoxLayout(fila)
            lay_f.setContentsMargins(12, 6, 12, 6)
            lay_f.setSpacing(10)

            # Informacion del modelo
            col_info = QVBoxLayout()
            col_info.setSpacing(2)
            nombre = of.get("name", "Camión Usado")
            precio = max(1, int(of.get("price", 45000)))
            odometro = int(of.get("odometer", 0))
            motor = of.get("engine", "Estándar")
            trans = of.get("transmission", "Estándar")

            lbl_nom = QLabel(nombre)
            lbl_nom.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 800;")
            lbl_det = QLabel(f"Motor: {motor}  ·  Caja: {trans}  ·  Kilometraje: {odometro:,} km")
            lbl_det.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 11px;")
            col_info.addWidget(lbl_nom)
            col_info.addWidget(lbl_det)

            # Precio
            lbl_precio = QLabel(f"${precio:,}")
            lbl_precio.setFixedWidth(95)
            lbl_precio.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_precio.setStyleSheet(f"color: {VERDE_TXT if dinero >= precio else AMBAR_TXT}; font-size: 14px; font-weight: 900;")

            max_este = min(plazas_libres, dinero // precio) if plazas_libres > 0 else 0

            spn_cant = QSpinBox()
            spn_cant.setStyleSheet(estilo_spin)
            spn_cant.setFixedSize(64, 30)
            spn_cant.setRange(0, max(0, max_este))
            spn_cant.setValue(1 if max_este > 0 else 0)
            spn_cant.setEnabled(max_este > 0)

            btn_comprar = QPushButton("Comprar")
            btn_comprar.setFixedSize(92, 30)
            btn_comprar.setCursor(Qt.PointingHandCursor)
            btn_comprar.setStyleSheet(estilo_boton("azul", compacto=True))
            btn_comprar.setAutoDefault(False)
            btn_comprar.setEnabled(max_este > 0)
            btn_comprar.setToolTip(
                "<div style='max-width: 240px;'>Compra la cantidad indicada de este camión usado "
                "y los guarda en tus garajes libres.</div>"
            )

            btn_max = QPushButton("Comprar Máximo")
            btn_max.setFixedSize(126, 30)
            btn_max.setCursor(Qt.PointingHandCursor)
            btn_max.setStyleSheet(estilo_boton("verde", compacto=True))
            btn_max.setAutoDefault(False)
            btn_max.setEnabled(max_este > 0)
            btn_max.setToolTip(
                f"<div style='max-width: 240px;'>Compra hasta {max_este} unidades de este modelo "
                f"según tu dinero y espacio libre en garajes.</div>"
            )

            offer_id = of.get("offer_id", "")
            btn_comprar.clicked.connect(
                lambda _, oid=offer_id, sp=spn_cant, b=btn_comprar: self._action_comprar_modelo(oid, sp.value(), b)
            )
            btn_max.clicked.connect(
                lambda _, oid=offer_id, m=max_este, b=btn_max: self._action_comprar_modelo(oid, m, b)
            )

            lay_f.addLayout(col_info, 1)
            lay_f.addWidget(lbl_precio)
            lay_f.addWidget(spn_cant)
            lay_f.addWidget(btn_comprar)
            lay_f.addWidget(btn_max)

            self.lay_lista.addWidget(fila)

        self.lay_lista.addStretch()

    def _ejecutar_compra_async(self, fn_compra, boton: QPushButton, texto_exito: str):
        if self._compra_en_curso:
            return
        self._compra_en_curso = True
        self.btn_variados.setEnabled(False)
        if boton is not None:
            boton.setEnabled(False)
            boton.setText(tr("⏳ Comprando..."))

        def _hilo():
            exito, msg = fn_compra()
            nuevos_datos = {}
            if exito:
                nuevos_datos = profile_manager.leer_datos_partida(self.ruta_guardado, sanear=False)
            try:
                # El dialogo pudo cerrarse mientras se compraba
                self._señales.compra_terminada.emit(exito, msg, nuevos_datos, boton, texto_exito)
            except RuntimeError:
                pass

        threading.Thread(target=_hilo, daemon=True).start()

    def _on_compra_terminada(self, exito: bool, msg: str, nuevos_datos: dict, boton, texto_exito: str):
        self._compra_en_curso = False
        self.btn_variados.setText(tr("Comprar Camiones Variados para Llenar Garajes"))
        if exito:
            self.hubo_compras = True
            if nuevos_datos:
                self.datos_partida = nuevos_datos
                if self.callback_refrescar:
                    self.callback_refrescar(self.datos_partida)
            self._construir_lista()
            target_btn = boton if boton else self.btn_variados
            if target_btn and target_btn.isEnabled():
                notificar_exito_boton(target_btn, texto_exito)
        else:
            self._construir_lista()
            QMessageBox.warning(self, "Atención", msg)

    def _action_comprar_modelo(self, offer_id: str, cantidad: int, boton: QPushButton):
        if cantidad <= 0:
            QMessageBox.information(self, "Aviso", "Selecciona al menos 1 unidad para comprar.")
            return
        self._ejecutar_compra_async(
            lambda oid=offer_id, cant=cantidad: profile_manager.comprar_camiones_usados(self.ruta_guardado, [(oid, cant)]),
            boton,
            "¡Comprado!"
        )

    def _action_comprar_variados(self):
        self._ejecutar_compra_async(
            lambda: profile_manager.comprar_camiones_usados_variados(self.ruta_guardado),
            self.btn_variados,
            "¡Flota Comprada!"
        )


class DialogoInfoTipoPerfil(QDialog):
    """Muestra información explicativa concisa sobre las diferencias entre
    Perfiles Locales y Perfiles de Steam Cloud, con los pasos directos para convertirlos."""

    def __init__(self, tipo: str = "locales", parent=None):
        super().__init__(parent)
        self.tipo = tipo
        self.es_local = (tipo == "locales")

        self.setWindowTitle(
            tr("Información: Perfiles Locales") if self.es_local else tr("Información: Perfiles de Steam Cloud")
        )
        self.setFixedSize(490, 315)
        self.setModal(True)

        color_borde = "#38BDF8" if self.es_local else "#F59E0B"
        bg_hdr = "#141E2D" if self.es_local else "#231B13"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0E131A;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }}
            QFrame#HdrCard {{
                background-color: {bg_hdr};
                border: 1px solid {color_borde};
                border-radius: 8px;
            }}
            QFrame#HdrCard QLabel {{
                border: none;
                background: transparent;
            }}
            QFrame#PasosCard {{
                background-color: #121822;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }}
            QFrame#PasosCard QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(12)

        # --- Cabecera ---
        hdr = QFrame()
        hdr.setObjectName("HdrCard")
        lay_hdr = QHBoxLayout(hdr)
        lay_hdr.setContentsMargins(12, 8, 12, 8)
        lay_hdr.setSpacing(12)

        lbl_icono = QLabel("💻" if self.es_local else "☁️")
        lbl_icono.setStyleSheet("font-size: 24px; background: transparent;")
        lay_hdr.addWidget(lbl_icono)

        lay_tit = QVBoxLayout()
        lay_tit.setSpacing(2)
        tit = QLabel(tr("Perfiles Locales") if self.es_local else tr("Perfiles de Steam Cloud"))
        tit.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color_borde}; background: transparent;")
        sub = QLabel(
            tr("Compatibles con este Launcher (editables)") if self.es_local
            else tr("Bloqueados por Steam (solo lectura)")
        )
        sub.setStyleSheet("font-size: 11px; color: #94A3B8; background: transparent;")
        lay_tit.addWidget(tit)
        lay_tit.addWidget(sub)
        lay_hdr.addLayout(lay_tit)
        lay_hdr.addStretch()

        lay.addWidget(hdr)

        # --- Pasos ---
        pasos_card = QFrame()
        pasos_card.setObjectName("PasosCard")
        lay_pasos = QVBoxLayout(pasos_card)
        lay_pasos.setContentsMargins(14, 10, 14, 12)
        lay_pasos.setSpacing(6)

        if self.es_local:
            frase_intro = tr("Estos perfiles se guardan en tu equipo y se pueden editar. Si deseas pasarlo a Steam Cloud:")
            p1 = tr("En ATS, ve a 'Cambiar trayectoria'.")
            p2 = tr("Elige tu perfil y pulsa 'Editar trayectoria'.")
            p3 = tr("Marca 'Sincronización con Steam Cloud' y haz clic en 'Confirm'.")
            p4 = tr("Nota: En Steam Cloud no podrá modificarse desde el Launcher.")
            pasos_txt = f"1. {p1}\n2. {p2}\n3. {p3}\n⚠️ {p4}"
        else:
            frase_intro = tr("Estos perfiles están protegidos en la nube de Steam. Para editarlos en el Launcher, pásalos a Local:")
            p1 = tr("En ATS, ve a 'Cambiar trayectoria'.")
            p2 = tr("Elige tu perfil y pulsa 'Editar trayectoria'.")
            p3 = tr("Desmarca 'Sincronización con Steam Cloud' y pulsa 'Confirm'.")
            p4 = tr("Cierra el juego y pulsa ↻ (Recargar) en este Launcher.")
            pasos_txt = f"1. {p1}\n2. {p2}\n3. {p3}\n4. {p4}"

        lbl_intro = QLabel(frase_intro)
        lbl_intro.setWordWrap(True)
        lbl_intro.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color_borde};")
        lay_pasos.addWidget(lbl_intro)

        lbl_p_desc = QLabel(pasos_txt)
        lbl_p_desc.setWordWrap(True)
        lbl_p_desc.setStyleSheet("font-size: 11px; color: #CBD5E1; line-height: 140%;")
        lay_pasos.addWidget(lbl_p_desc)
        lay.addWidget(pasos_card)

        # --- Boton ---
        lay_btn = QHBoxLayout()
        lay_btn.addStretch()
        btn_cerrar = QPushButton(tr("¡Entendido!"))
        btn_cerrar.setFixedSize(110, 30)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)
        btn_cerrar.setAutoDefault(True)
        btn_cerrar.setDefault(True)
        btn_cerrar.setFocus()
        btn_cerrar.clicked.connect(self.accept)
        lay_btn.addWidget(btn_cerrar)
        lay.addLayout(lay_btn)

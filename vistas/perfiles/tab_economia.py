from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QProgressBar)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import (QMessageBox, notificar_exito_boton, CSS_PROGRESO,
                    VERDE_TXT, ROJO_TXT, TXT_PRINCIPAL, TXT_SECUNDARIO)



from .dialogos import DialogoDinero, DialogoExperiencia


class TabEconomiaMixin:
    """Pestaña Economía y Nivel: dinero, experiencia y banco."""

    def _tab_economia(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(14)

        # --- Dinero ---
        card_d = QFrame()
        card_d.setStyleSheet("QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }")
        lay_d = QVBoxLayout(card_d)
        lay_d.setContentsMargins(18, 14, 18, 14)
        lay_d.setSpacing(12)

        fila_top_d = QHBoxLayout()
        self.lbl_val_dinero = QLabel(f"{tr('Saldo en Cuenta:')} 0 USD")
        self.lbl_val_dinero.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800; border: none;")

        self.btn_mod_dinero = QPushButton(tr("Editar Manualmente"))
        self.btn_mod_dinero.setFixedHeight(32)
        self.btn_mod_dinero.setCursor(Qt.PointingHandCursor)
        self.btn_mod_dinero.setStyleSheet(self._estilo_btn("verde"))
        self.btn_mod_dinero.clicked.connect(self._abrir_modal_dinero)

        fila_top_d.addWidget(self.lbl_val_dinero, 1)
        fila_top_d.addWidget(self.btn_mod_dinero)

        fila_presets_d = QHBoxLayout()
        fila_presets_d.setSpacing(8)
        self.lbl_pre_d = QLabel(tr("Ajustes rápidos:"))
        self.lbl_pre_d.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: bold; border: none;")
        fila_presets_d.addWidget(self.lbl_pre_d)

        self.presets_dinero_btns = []
        lista_d = [
            (50000, "+$50 Mil"),
            (100000, "+$100 Mil"),
            (500000, "+$500 Mil"),
            (1000000, "+$1 Millón"),
            (10000000, "+$10 Millones"),
            (500000000, "+$500 Millones"),
        ]
        for val, txt in lista_d:
            btn = QPushButton(tr(txt))
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._estilo_btn("neutro"))
            btn.clicked.connect(lambda _, v=val, b=btn: self._aplicar_preset_dinero(v, sumar=True, boton=b))
            fila_presets_d.addWidget(btn)
            self.presets_dinero_btns.append((btn, txt))

        fila_presets_d.addStretch()

        lay_d.addLayout(fila_top_d)
        lay_d.addLayout(fila_presets_d)

        # --- Experiencia ---
        card_x = QFrame()
        card_x.setStyleSheet("QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }")
        lay_x = QVBoxLayout(card_x)
        lay_x.setContentsMargins(18, 14, 18, 14)
        lay_x.setSpacing(10)

        fila_top_x = QHBoxLayout()
        self.lbl_val_xp = QLabel(f"{tr('Experiencia (XP):')} 0 PE")
        self.lbl_val_xp.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800; border: none;")

        self.btn_mod_xp = QPushButton(tr("Editar Manualmente"))
        self.btn_mod_xp.setFixedHeight(32)
        self.btn_mod_xp.setCursor(Qt.PointingHandCursor)
        self.btn_mod_xp.setStyleSheet(self._estilo_btn("azul"))
        self.btn_mod_xp.clicked.connect(self._abrir_modal_xp)

        fila_top_x.addWidget(self.lbl_val_xp, 1)
        fila_top_x.addWidget(self.btn_mod_xp)

        self.lbl_nivel_calculado = QLabel(f"{tr('Nivel Conductor:')} 0")
        self.lbl_nivel_calculado.setStyleSheet(f"color: {VERDE_TXT}; font-size: 13px; font-weight: bold; border: none;")

        self.pbar_xp = QProgressBar()
        self.pbar_xp.setFixedHeight(8)
        self.pbar_xp.setStyleSheet(CSS_PROGRESO)

        fila_presets_x = QHBoxLayout()
        fila_presets_x.setSpacing(8)
        self.lbl_pre_x = QLabel(tr("Niveles rápidos:"))
        self.lbl_pre_x.setStyleSheet(f"color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: bold; border: none;")
        fila_presets_x.addWidget(self.lbl_pre_x)

        self.presets_xp_btns = []
        lista_x = [
            (15, "Nivel 15"),
            (30, "Nivel 30"),
            (50, "Nivel 50"),
            (100, "Nivel 100 (Desbloquea Todo)"),
            (150, "Nivel 150 (Leyenda)"),
        ]
        for lvl, txt in lista_x:
            btn = QPushButton(tr(txt))
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._estilo_btn("neutro"))
            btn.clicked.connect(lambda _, l=lvl, b=btn: self._aplicar_preset_nivel(l, b))
            fila_presets_x.addWidget(btn)
            self.presets_xp_btns.append((btn, txt))

        fila_presets_x.addStretch()

        lay_x.addLayout(fila_top_x)
        lay_x.addWidget(self.lbl_nivel_calculado)
        lay_x.addWidget(self.pbar_xp)
        lay_x.addLayout(fila_presets_x)

        # --- Banco ---
        card_b = QFrame()
        card_b.setStyleSheet("QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }")
        lay_b = QHBoxLayout(card_b)
        lay_b.setContentsMargins(18, 14, 18, 14)

        col_b_info = QVBoxLayout()
        col_b_info.setSpacing(4)
        self.lbl_b_tit = QLabel(tr("Estado Bancario y Préstamos"))
        self.lbl_b_tit.setStyleSheet(f"color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800; border: none;")
        self.lbl_estado_banco = QLabel(tr("Sin préstamos ni deudas bancarias activas (0 USD)"))
        self.lbl_estado_banco.setStyleSheet(f"color: {VERDE_TXT}; font-size: 13px; font-weight: bold; border: none;")
        col_b_info.addWidget(self.lbl_b_tit)
        col_b_info.addWidget(self.lbl_estado_banco)

        self.btn_liquidar_deuda = QPushButton(tr("Liquidar Préstamos Bancarios"))
        self.btn_liquidar_deuda.setFixedHeight(34)
        self.btn_liquidar_deuda.setCursor(Qt.PointingHandCursor)
        self.btn_liquidar_deuda.setStyleSheet(self._estilo_btn("azul"))
        self.btn_liquidar_deuda.clicked.connect(self._action_liquidar_prestamos)

        lay_b.addLayout(col_b_info, 1)
        lay_b.addWidget(self.btn_liquidar_deuda)

        lay.addWidget(card_d)
        lay.addWidget(card_x)
        lay.addWidget(card_b)
        lay.addStretch()
        return w

    def _aplicar_dinero_optimista(self, ruta_g: str, nuevo_val: int, boton, texto_exito: str | None = None):
        if not self._juego_cerrado_o_alertar():
            return
        self.datos_partida_actual["money"] = nuevo_val
        self._marcar_otras_tabs_sucias()
        self._refrescar_economia(self.datos_partida_actual)
        if texto_exito is not None:
            notificar_exito_boton(boton, texto_exito)
        else:
            notificar_exito_boton(boton)
        self._encolar_edicion_ligera_async(
            "money", ruta_g, tr("Guardando..."),
            lambda r=ruta_g, v=nuevo_val: profile_manager.guardar_dinero_partida(r, v),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
        )

    def _aplicar_xp_optimista(self, ruta_g: str, xp_val: int, boton, texto_exito: str | None = None):
        if not self._juego_cerrado_o_alertar():
            return
        self.datos_partida_actual["xp"] = xp_val
        self._marcar_otras_tabs_sucias()
        self._refrescar_economia(self.datos_partida_actual)
        if texto_exito is not None:
            notificar_exito_boton(boton, texto_exito)
        else:
            notificar_exito_boton(boton)
        self._encolar_edicion_ligera_async(
            "xp", ruta_g, tr("Guardando..."),
            lambda r=ruta_g, v=xp_val: profile_manager.guardar_xp_partida(r, v),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
        )

    def _abrir_modal_dinero(self):
        dlg = DialogoDinero(self.datos_partida_actual["money"], self)
        if dlg.exec():
            nuevo_val = dlg.spn_dinero.value()
            ruta_g = self._obtener_ruta_guardado_actual()
            if ruta_g:
                self._aplicar_dinero_optimista(ruta_g, nuevo_val, self.btn_mod_dinero)

    def _aplicar_preset_dinero(self, monto: int, sumar: bool, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        actual = self.datos_partida_actual.get("money", 0)
        nuevo_val = min(2000000000, max(0, actual + monto if sumar else monto))
        self._aplicar_dinero_optimista(ruta_g, nuevo_val, boton, "¡Aplicado!")

    def _abrir_modal_xp(self):
        dlg = DialogoExperiencia(self.datos_partida_actual["xp"], self)
        if dlg.exec():
            nuevo_val = dlg.spn_xp.value()
            ruta_g = self._obtener_ruta_guardado_actual()
            if ruta_g:
                self._aplicar_xp_optimista(ruta_g, nuevo_val, self.btn_mod_xp)

    def _aplicar_preset_nivel(self, nivel_objetivo: int, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        xp_necesaria = profile_manager.calcular_xp_para_nivel(nivel_objetivo)
        self._aplicar_xp_optimista(ruta_g, xp_necesaria, boton, "¡Nivel Aplicado!")

    def _action_liquidar_prestamos(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or not self._juego_cerrado_o_alertar():
            return
        self.datos_partida_actual["loans_count"] = 0
        self.datos_partida_actual["loans_amount"] = 0
        self.datos_partida_actual["overdraft"] = False
        self._refrescar_economia(self.datos_partida_actual)
        notificar_exito_boton(self.btn_liquidar_deuda, "¡Deuda Liquidada!")
        self._encolar_edicion_ligera_async(
            "loans", ruta_g, tr("Guardando..."),
            lambda r=ruta_g: profile_manager.liquidar_prestamos_partida(r),
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
        )

    def _refrescar_economia(self, datos: dict):
        saldo_fmt = profile_manager.formatear_saldo_usd(datos["money"])
        self.lbl_val_dinero.setText(f"{tr('Saldo en Cuenta:')} {saldo_fmt}")
        self.lbl_val_xp.setText(f"{tr('Experiencia (XP):')} {datos['xp']:,} PE")

        lvl, prog, req = profile_manager.calcular_nivel_ats(datos["xp"])
        self.lbl_nivel_calculado.setText(f"{tr('Nivel Conductor:')} {lvl}  ({prog:,} / {req:,} PE)")
        self.pbar_xp.setMaximum(max(1, req))
        self.pbar_xp.setValue(prog)

        loans_cnt = datos.get("loans_count", 0)
        loans_amt = datos.get("loans_amount", 0)
        overdraft = datos.get("overdraft", False)
        if loans_cnt > 0 or overdraft:
            deuda_fmt = profile_manager.formatear_saldo_usd(loans_amt)
            extra_ov = " + Sobregiro activo" if overdraft else ""
            self.lbl_estado_banco.setText(f"Deuda activa: {deuda_fmt} ({loans_cnt} préstamo(s){extra_ov})")
            self.lbl_estado_banco.setStyleSheet(f"color: {ROJO_TXT}; font-size: 13px; font-weight: bold; border: none;")
        else:
            self.lbl_estado_banco.setText(tr("Sin préstamos ni deudas bancarias activas (0 USD)"))
            self.lbl_estado_banco.setStyleSheet(f"color: {VERDE_TXT}; font-size: 13px; font-weight: bold; border: none;")

    def _actualizar_idioma_tab_economia(self):
        """Actualiza los textos fijos de la pestaña Economía y Nivel."""
        if hasattr(self, "btn_mod_dinero"):
            self.btn_mod_dinero.setText(tr("Editar Manualmente"))
        if hasattr(self, "btn_mod_xp"):
            self.btn_mod_xp.setText(tr("Editar Manualmente"))
        if hasattr(self, "lbl_pre_d"):
            self.lbl_pre_d.setText(tr("Ajustes rápidos:"))
        if hasattr(self, "lbl_pre_x"):
            self.lbl_pre_x.setText(tr("Niveles rápidos:"))
        if hasattr(self, "lbl_b_tit"):
            self.lbl_b_tit.setText(tr("Estado Bancario y Préstamos"))
        if hasattr(self, "btn_liquidar_deuda"):
            self.btn_liquidar_deuda.setText(tr("Liquidar Préstamos Bancarios"))
        for btn, txt in getattr(self, "presets_dinero_btns", []):
            btn.setText(tr(txt))
        for btn, txt in getattr(self, "presets_xp_btns", []):
            btn.setText(tr(txt))
        if hasattr(self, "datos_partida_actual") and self.datos_partida_actual:
            self._refrescar_economia(self.datos_partida_actual)

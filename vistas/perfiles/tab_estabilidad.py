from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame


from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import QMessageBox, notificar_exito_boton, TXT_PRINCIPAL, TXT_SECUNDARIO





class TabEstabilidadMixin:
    """Pestaña dedicada exclusivamente a la Física y Estabilidad Antivuelco del perfil."""

    def _tab_estabilidad_antivuelco(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        card = QFrame()
        card.setStyleSheet('QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }')
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(20, 18, 20, 18)
        c_lay.setSpacing(14)

        # Cabecera
        cab = QHBoxLayout()
        cab.setSpacing(12)
        col_tit = QVBoxLayout()
        col_tit.setSpacing(3)
        self.lbl_tit_estab = QLabel(tr('⚖️ Física y Estabilidad Antivuelco'))
        self.lbl_tit_estab.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800; border: none;')
        self.lbl_sub_estab = QLabel(tr('Configura los parámetros de rigidez y suspensión para evitar volcamientos en curvas a alta velocidad.'))
        self.lbl_sub_estab.setStyleSheet(f'color: {TXT_SECUNDARIO}; font-size: 12px; border: none;')
        col_tit.addWidget(self.lbl_tit_estab)
        col_tit.addWidget(self.lbl_sub_estab)
        cab.addLayout(col_tit, 1)

        self.btn_estab_todos_on = QPushButton(tr('Activar Todo'))
        self.btn_estab_todos_on.setFixedHeight(32)
        self.btn_estab_todos_on.setCursor(Qt.PointingHandCursor)
        self.btn_estab_todos_on.setStyleSheet(self._estilo_btn('verde', compacto=True))
        self.btn_estab_todos_on.clicked.connect(lambda: self._action_toggle_todos_estabilidad(True))

        self.btn_estab_todos_off = QPushButton(tr('Poner Todo Normal'))
        self.btn_estab_todos_off.setFixedHeight(32)
        self.btn_estab_todos_off.setCursor(Qt.PointingHandCursor)
        self.btn_estab_todos_off.setStyleSheet(self._estilo_btn('azul', compacto=True))
        self.btn_estab_todos_off.clicked.connect(lambda: self._action_toggle_todos_estabilidad(False))

        cab.addWidget(self.btn_estab_todos_on)
        cab.addWidget(self.btn_estab_todos_off)
        c_lay.addLayout(cab)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: #262932; border: none;')
        c_lay.addWidget(sep)

        # Filas de parámetros
        self.filas_estabilidad = {}
        for clave, nombre, val_max, val_def in profile_manager.OPCIONES_ESTABILIDAD:
            fila = QHBoxLayout()
            fila.setContentsMargins(6, 8, 6, 8)
            fila.setSpacing(12)

            col_izq = QVBoxLayout()
            col_izq.setSpacing(3)
            lbl_nom = QLabel(tr(nombre))
            lbl_nom.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 700; border: none;')
            lbl_est = QLabel(f"{tr('Estado actual:')} ...")
            lbl_est.setStyleSheet(f'color: {TXT_SECUNDARIO}; font-size: 12px; border: none;')
            col_izq.addWidget(lbl_nom)
            col_izq.addWidget(lbl_est)

            btn_tog = QPushButton('...')
            btn_tog.setFixedHeight(32)
            btn_tog.setFixedWidth(230)
            btn_tog.setCursor(Qt.PointingHandCursor)
            btn_tog.setStyleSheet(self._estilo_btn('neutro'))
            btn_tog.clicked.connect(lambda _=False, c=clave: self._action_toggle_parametro_estabilidad(c))

            fila.addLayout(col_izq, 1)
            fila.addWidget(btn_tog)
            c_lay.addLayout(fila)

            self.filas_estabilidad[clave] = {
                'nombre': nombre,
                'lbl_nom': lbl_nom,
                'lbl_estado': lbl_est,
                'btn_toggle': btn_tog,
                'val_actual': val_def,
            }

        lay.addWidget(card)
        lay.addStretch()
        return w

    def _actualizar_ui_estabilidad_completa(self, valores: dict):
        for clave, info in getattr(self, 'filas_estabilidad', {}).items():
            val = valores.get(clave, '0.5')
            info['val_actual'] = val
            try:
                is_max = float(val) >= 1.0
            except ValueError:
                is_max = val == '1.0'

            es_susp = 'suspension' in clave
            txt_estado = tr('Estado actual:')
            if is_max:
                if es_susp:
                    tag = tr('Máxima (Rígida)')
                    txt_btn = tr('Poner rigidez normal')
                else:
                    tag = tr('Máxima (Antivuelco activo)')
                    txt_btn = tr('Poner estabilidad normal')
                info['lbl_estado'].setText(f"{txt_estado} <span style='color: #6EE7B7; font-weight: 700;'>{tag}</span>")
                info['btn_toggle'].setText(txt_btn)
                info['btn_toggle'].setProperty('texto_base', txt_btn)
                info['btn_toggle'].setStyleSheet(self._estilo_btn('azul'))
            else:
                if es_susp:
                    tag = tr('Normal (Estándar)')
                    txt_btn = tr('Activar rigidez máxima')
                else:
                    tag = tr('Normal (Realista)')
                    txt_btn = tr('Activar estabilidad máxima')
                info['lbl_estado'].setText(f"{txt_estado} <span style='color: #94A3B8; font-weight: 600;'>{tag}</span>")
                info['btn_toggle'].setText(txt_btn)
                info['btn_toggle'].setProperty('texto_base', txt_btn)
                info['btn_toggle'].setStyleSheet(self._estilo_btn('verde'))

    def _actualizar_idioma_tab_estabilidad(self):
        """Actualiza todos los textos estáticos y dinámicos de la pestaña Física y Antivuelco."""
        if hasattr(self, 'lbl_tit_estab') and self.lbl_tit_estab:
            self.lbl_tit_estab.setText(tr('⚖️ Física y Estabilidad Antivuelco'))
        if hasattr(self, 'lbl_sub_estab') and self.lbl_sub_estab:
            self.lbl_sub_estab.setText(tr('Configura los parámetros de rigidez y suspensión para evitar volcamientos en curvas a alta velocidad.'))
        if hasattr(self, 'btn_estab_todos_on') and self.btn_estab_todos_on:
            self.btn_estab_todos_on.setText(tr('Activar Todo'))
        if hasattr(self, 'btn_estab_todos_off') and self.btn_estab_todos_off:
            self.btn_estab_todos_off.setText(tr('Poner Todo Normal'))

        vals = {}
        for clave, info in getattr(self, 'filas_estabilidad', {}).items():
            if 'lbl_nom' in info and info['lbl_nom']:
                info['lbl_nom'].setText(tr(info.get('nombre', '')))
            vals[clave] = info.get('val_actual', '0.5')
        self._actualizar_ui_estabilidad_completa(vals)

    def _refrescar_estabilidad(self, datos: dict):
        ruta_g = self._obtener_ruta_guardado_actual()
        if ruta_g:
            valores_estab = profile_manager.obtener_valores_estabilidad_perfil(ruta_g)
            self._actualizar_ui_estabilidad_completa(valores_estab)

    def _on_error_estabilidad(self, exito: bool, msg: str, ruta_g: str):
        if exito:
            return
        if ruta_g == self._obtener_ruta_guardado_actual():
            valores = profile_manager.obtener_valores_estabilidad_perfil(ruta_g)
            self._actualizar_ui_estabilidad_completa(valores)
        QMessageBox.warning(self, 'Atención', msg)

    def _action_toggle_parametro_estabilidad(self, clave: str):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or not self._juego_cerrado_o_alertar():
            return
        info = self.filas_estabilidad.get(clave)
        if not info:
            return
        val_actual = info.get('val_actual', '0.5')
        try:
            is_max = float(val_actual) >= 1.0
        except ValueError:
            is_max = val_actual == '1.0'
        nuevo_val = '0.5' if is_max else '1.0'
        opt_vals = {k: v.get('val_actual', '0.5') for k, v in self.filas_estabilidad.items()}
        opt_vals[clave] = nuevo_val
        self._actualizar_ui_estabilidad_completa(opt_vals)
        notificar_exito_boton(info['btn_toggle'], '¡Ajuste aplicado!')
        self._encolar_edicion_ligera_async(
            f'estab:{clave}',
            ruta_g,
            tr('Guardando...'),
            lambda r=ruta_g, c=clave, v=nuevo_val: profile_manager.modificar_parametro_config_perfil(r, c, v),
            on_result=lambda ok, msg, r=ruta_g: self._on_error_estabilidad(ok, msg, r),
        )

    def _action_toggle_todos_estabilidad(self, activar: bool):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g or not self._juego_cerrado_o_alertar():
            return
        btn = self.btn_estab_todos_on if activar else self.btn_estab_todos_off
        nuevo_val = '1.0' if activar else '0.5'
        opt_vals = {k: nuevo_val for k in self.filas_estabilidad}
        self._actualizar_ui_estabilidad_completa(opt_vals)
        notificar_exito_boton(btn, '¡Aplicado a todos!')
        self._encolar_edicion_ligera_async(
            'estab_all',
            ruta_g,
            tr('Guardando...'),
            lambda r=ruta_g, act=activar: profile_manager.modificar_todos_parametros_estabilidad(r, act),
            on_result=lambda ok, msg, r=ruta_g: self._on_error_estabilidad(ok, msg, r),
        )

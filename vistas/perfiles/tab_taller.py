from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QProgressBar, QLineEdit, QScrollArea,
)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import (
    QMessageBox, notificar_exito_boton,
    CSS_TARJETA, CSS_PROGRESO,
    AZUL_TXT, AZUL_BORDE, AZUL_FONDO,
    TXT_PRINCIPAL, TXT_SECUNDARIO, TXT_APAGADO,
)


class TabTallerMixin:
    """Pestaña Taller y Vehículo: info del camión, reparación, combustible, placa y odómetro."""

    def _tab_taller_vehiculo(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(14)

        # Tarjeta de mantenimiento mecánico
        card_mec = QFrame()
        card_mec.setStyleSheet('QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }')
        lay_mec = QVBoxLayout(card_mec)
        lay_mec.setContentsMargins(18, 14, 18, 16)
        lay_mec.setSpacing(12)

        self.lbl_tit_mec = QLabel(tr('Mantenimiento Mecánico y Combustible'))
        self.lbl_tit_mec.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800; border: none;')
        lay_mec.addWidget(self.lbl_tit_mec)
        lay_mec.addSpacing(4)

        # Reparación
        fila_rep = QHBoxLayout()
        self.lbl_estado_dano = QLabel(f"{tr('Daño mecánico:')} 0%  |  {tr('Desgaste permanente:')} 0%")
        self.lbl_estado_dano.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold; border: none;')

        self.btn_reparar_todo = QPushButton(tr('Reparar Camión y Flota (0% Daño y Desgaste)'))
        self.btn_reparar_todo.setFixedHeight(32)
        self.btn_reparar_todo.setCursor(Qt.PointingHandCursor)
        self.btn_reparar_todo.setStyleSheet(self._estilo_btn('verde'))
        self.btn_reparar_todo.clicked.connect(self._action_reparar_flota)

        fila_rep.addWidget(self.lbl_estado_dano, 1)
        fila_rep.addWidget(self.btn_reparar_todo)

        # Combustible
        fila_fuel = QHBoxLayout()
        self.lbl_estado_fuel = QLabel(f"{tr('Combustible en tanque:')} 100%")
        self.lbl_estado_fuel.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold; border: none;')

        self.pbar_fuel = QProgressBar()
        self.pbar_fuel.setRange(0, 100)
        self.pbar_fuel.setValue(100)
        self.pbar_fuel.setFixedHeight(10)
        self.pbar_fuel.setFixedWidth(180)
        self.pbar_fuel.setStyleSheet(CSS_PROGRESO)

        self.btn_llenar_fuel = QPushButton(tr('Llenar Tanque al 100%'))
        self.btn_llenar_fuel.setFixedHeight(32)
        self.btn_llenar_fuel.setCursor(Qt.PointingHandCursor)
        self.btn_llenar_fuel.setStyleSheet(self._estilo_btn('azul'))
        self.btn_llenar_fuel.clicked.connect(self._action_llenar_combustible)

        fila_fuel.addWidget(self.lbl_estado_fuel)
        fila_fuel.addWidget(self.pbar_fuel)
        fila_fuel.addStretch()
        fila_fuel.addWidget(self.btn_llenar_fuel)

        lay_mec.addLayout(fila_rep)
        lay_mec.addLayout(fila_fuel)

        # Tarjeta de personalización
        card_per = QFrame()
        card_per.setStyleSheet('QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }')
        lay_per = QVBoxLayout(card_per)
        lay_per.setContentsMargins(18, 14, 18, 16)
        lay_per.setSpacing(12)

        self.lbl_tit_per = QLabel(tr('Personalización del Camión Activo (Matrícula y Odómetro)'))
        self.lbl_tit_per.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800; border: none;')
        lay_per.addWidget(self.lbl_tit_per)
        lay_per.addSpacing(4)

        # Placa
        fila_placa = QHBoxLayout()
        fila_placa.setSpacing(10)
        self.lbl_placa_tit = QLabel(tr('Matrícula / Placa:'))
        self.lbl_placa_tit.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold; border: none;')

        self.txt_placa_texto = QLineEdit()
        self.txt_placa_texto.setPlaceholderText('Ej: XTRINK')
        self.txt_placa_texto.setFixedHeight(32)
        self.txt_placa_texto.setStyleSheet(self._estilo_input())
        self.txt_placa_texto.returnPressed.connect(self._action_guardar_placa)

        self.btn_guardar_placa = QPushButton(tr('Guardar Placa'))
        self.btn_guardar_placa.setFixedHeight(32)
        self.btn_guardar_placa.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_placa.setStyleSheet(self._estilo_btn('azul'))
        self.btn_guardar_placa.clicked.connect(self._action_guardar_placa)

        fila_placa.addWidget(self.lbl_placa_tit)
        fila_placa.addWidget(self.txt_placa_texto, 1)
        fila_placa.addWidget(self.btn_guardar_placa)

        # Odómetro
        fila_odo = QHBoxLayout()
        fila_odo.setSpacing(10)
        self.lbl_odo_tit = QLabel(tr('Kilometraje en Tablero (Odómetro):'))
        self.lbl_odo_tit.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold; border: none;')

        self.spn_odometro = QSpinBox()
        self.spn_odometro.setRange(0, 99999999)
        self.spn_odometro.setFixedHeight(32)
        self.spn_odometro.setMinimumWidth(160)
        self.spn_odometro.setStyleSheet(self._estilo_input())
        if self.spn_odometro.lineEdit() is not None:
            self.spn_odometro.lineEdit().returnPressed.connect(
                lambda: (self.spn_odometro.interpretText(), self._action_guardar_odo())
            )

        self.btn_guardar_odo = QPushButton(tr('Actualizar Odómetro'))
        self.btn_guardar_odo.setFixedHeight(32)
        self.btn_guardar_odo.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_odo.setStyleSheet(self._estilo_btn('azul'))
        self.btn_guardar_odo.clicked.connect(self._action_guardar_odo)

        fila_odo.addWidget(self.lbl_odo_tit)
        fila_odo.addWidget(self.spn_odometro)
        fila_odo.addStretch()
        fila_odo.addWidget(self.btn_guardar_odo)

        lay_per.addLayout(fila_placa)
        lay_per.addLayout(fila_odo)

        lay.addWidget(self._crear_tarjeta_info_camion())
        lay.addWidget(card_mec)
        lay.addWidget(card_per)
        lay.addStretch()
        return w

    def _ejecutar_taller_optimista(self, clave: str, ruta_g: str, boton, texto_exito: str, fn_write, fn_opt):
        if not self._juego_cerrado_o_alertar():
            return
        trk = self.datos_partida_actual.get('truck')
        if isinstance(trk, dict) and trk.get('found'):
            fn_opt(trk)
            self._refrescar_taller(self.datos_partida_actual)
        notificar_exito_boton(boton, texto_exito)
        self._encolar_edicion_ligera_async(
            clave,
            ruta_g,
            tr('Guardando...'),
            fn_write,
            on_result=lambda ok, msg, r=ruta_g: self._manejar_error_edicion_ligera(ok, msg, r),
        )

    def _action_reparar_flota(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return

        def _opt(trk):
            trk['max_wear_pct'] = 0.0
            trk['max_unfixable_pct'] = 0.0

        self._ejecutar_taller_optimista(
            'repair', ruta_g, self.btn_reparar_todo, '¡Reparado al 100%!',
            lambda r=ruta_g: profile_manager.reparar_vehiculos_partida(r),
            _opt,
        )

    def _action_llenar_combustible(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return

        def _opt(trk):
            trk['fuel_pct'] = 100

        self._ejecutar_taller_optimista(
            'fuel', ruta_g, self.btn_llenar_fuel, '¡Tanque Lleno!',
            lambda r=ruta_g: profile_manager.llenar_combustible_partida(r),
            _opt,
        )

    def _action_guardar_placa(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        texto = self.txt_placa_texto.text()
        texto_limpio = texto.strip().replace('"', '')
        if not texto_limpio:
            QMessageBox.warning(self, 'Atención', 'El texto de la placa no puede estar vacío.')
            return

        def _opt(trk):
            trk['plate_text'] = texto_limpio

        self._ejecutar_taller_optimista(
            'plate', ruta_g, self.btn_guardar_placa, '¡Placa Guardada!',
            lambda r=ruta_g, t=texto: profile_manager.cambiar_placa_camion(r, t),
            _opt,
        )

    def _action_guardar_odo(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        val = max(0, int(self.spn_odometro.value()))

        def _opt(trk):
            trk['odometer'] = val

        self._ejecutar_taller_optimista(
            'odometer', ruta_g, self.btn_guardar_odo, '¡Odómetro Actualizado!',
            lambda r=ruta_g, v=val: profile_manager.cambiar_odometro_camion(r, v),
            _opt,
        )

    def _crear_tarjeta_info_camion(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card')
        card.setStyleSheet(CSS_TARJETA)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 12, 16, 14)
        c_lay.setSpacing(10)

        cab = QHBoxLayout()
        cab.setSpacing(8)
        self.lbl_camion_nombre = QLabel('Sin camión activo')
        self.lbl_camion_nombre.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 17px; font-weight: 900;')
        self.lbl_camion_mod = QLabel('MOD')
        self.lbl_camion_mod.setStyleSheet(
            f'background: {AZUL_FONDO}; color: {AZUL_TXT}; font-size: 10px; font-weight: 800; '
            f'border: 1px solid {AZUL_BORDE}; border-radius: 4px; padding: 2px 6px;'
        )
        self.lbl_camion_mod.setToolTip('Camión añadido por un mod (marca no oficial de ATS)')
        self.lbl_camion_mod.hide()

        self.btn_reiniciar_viaje = QPushButton(tr('Reiniciar contador de viaje'))
        self.btn_reiniciar_viaje.setFixedHeight(28)
        self.btn_reiniciar_viaje.setCursor(Qt.PointingHandCursor)
        self.btn_reiniciar_viaje.setStyleSheet(self._estilo_btn('neutro', compacto=True))
        self.btn_reiniciar_viaje.clicked.connect(self._action_reiniciar_viaje)

        cab.addWidget(self.lbl_camion_nombre)
        cab.addWidget(self.lbl_camion_mod)
        cab.addStretch()
        cab.addWidget(self.btn_reiniciar_viaje)
        c_lay.addLayout(cab)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        self.lbls_camion = {}
        self.lbl_caps_camion = {}
        campos = [
            ('motor', 'Motor'),
            ('transmision', 'Transmisión'),
            ('chasis', 'Chasis'),
            ('cabina', 'Cabina'),
            ('placa', 'Matrícula'),
            ('odometro', 'Odómetro'),
            ('combustible', 'Combustible'),
            ('viaje', 'Viaje actual'),
        ]
        for i, (clave, titulo) in enumerate(campos):
            celda = QVBoxLayout()
            celda.setSpacing(1)
            cap = QLabel(tr(titulo))
            cap.setStyleSheet(f'color: {TXT_APAGADO}; font-size: 11px; font-weight: 700;')
            val = QLabel('--')
            val.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 700;')
            celda.addWidget(cap)
            celda.addWidget(val)
            grid.addLayout(celda, i // 4, i % 4)
            self.lbls_camion[clave] = val
            self.lbl_caps_camion[clave] = (cap, titulo)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        c_lay.addLayout(grid)
        return card

    def _refrescar_taller(self, datos: dict):
        trk = datos.get('truck', {})
        L = self.lbls_camion
        if trk.get('found'):
            nombre = f"{trk.get('brand_name', '')} {trk.get('model_name', '')}".strip() or tr('Camión sin identificar')
            self.lbl_camion_nombre.setText(nombre)
            self.lbl_camion_mod.setVisible(bool(trk.get('is_mod')))
            L['motor'].setText(trk.get('engine') or '--')
            L['transmision'].setText(trk.get('transmission') or '--')
            L['chasis'].setText(trk.get('chassis') or '--')
            L['cabina'].setText(trk.get('cabin') or '--')
            placa = trk.get('plate_text', '')
            estado = trk.get('plate_state', '')
            L['placa'].setText(f'{placa} ({estado})' if placa and estado else placa or '--')
            L['odometro'].setText(f"{trk.get('odometer', 0):,}")
            L['combustible'].setText(f"{trk.get('fuel_pct', 100)}%")
            L['viaje'].setText(
                f"{trk.get('trip_km', 0):,} km · {trk.get('trip_fuel_l', 0)} L · {trk.get('trip_min', 0)} min"
            )

            self.lbl_estado_dano.setText(
                f"{tr('Daño mecánico:')} {trk.get('max_wear_pct', 0.0)}%  |  {tr('Desgaste permanente:')} {trk.get('max_unfixable_pct', 0.0)}%"
            )
            fuel_p = trk.get('fuel_pct', 100)
            self.lbl_estado_fuel.setText(f"{tr('Combustible en tanque:')} {fuel_p}%")
            self.pbar_fuel.setValue(fuel_p)
            self.txt_placa_texto.setText(trk.get('plate_text', ''))
            self.spn_odometro.setValue(trk.get('odometer', 0))
        else:
            self.lbl_camion_nombre.setText(tr('Sin camión activo'))
            self.lbl_camion_mod.hide()
            for v in L.values():
                v.setText('--')
            self.lbl_estado_dano.setText(tr('Sin camión activo'))
            self.lbl_estado_fuel.setText(f"{tr('Combustible en tanque:')} --")
            self.pbar_fuel.setValue(0)
            self.txt_placa_texto.clear()
            self.spn_odometro.setValue(0)

    def _actualizar_idioma_tab_taller(self):
        """Actualiza todos los textos estáticos y dinámicos de la pestaña Taller y Vehículo."""
        if hasattr(self, 'lbl_tit_mec') and self.lbl_tit_mec:
            self.lbl_tit_mec.setText(tr('Mantenimiento Mecánico y Combustible'))
        if hasattr(self, 'btn_reparar_todo') and self.btn_reparar_todo:
            self.btn_reparar_todo.setText(tr('Reparar Camión y Flota (0% Daño y Desgaste)'))
        if hasattr(self, 'btn_llenar_fuel') and self.btn_llenar_fuel:
            self.btn_llenar_fuel.setText(tr('Llenar Tanque al 100%'))
        if hasattr(self, 'lbl_tit_per') and self.lbl_tit_per:
            self.lbl_tit_per.setText(tr('Personalización del Camión Activo (Matrícula y Odómetro)'))
        if hasattr(self, 'lbl_placa_tit') and self.lbl_placa_tit:
            self.lbl_placa_tit.setText(tr('Matrícula / Placa:'))
        if hasattr(self, 'btn_guardar_placa') and self.btn_guardar_placa:
            self.btn_guardar_placa.setText(tr('Guardar Placa'))
        if hasattr(self, 'lbl_odo_tit') and self.lbl_odo_tit:
            self.lbl_odo_tit.setText(tr('Kilometraje en Tablero (Odómetro):'))
        if hasattr(self, 'btn_guardar_odo') and self.btn_guardar_odo:
            self.btn_guardar_odo.setText(tr('Actualizar Odómetro'))
        if hasattr(self, 'btn_reiniciar_viaje') and self.btn_reiniciar_viaje:
            self.btn_reiniciar_viaje.setText(tr('Reiniciar contador de viaje'))

        for cap_lbl, tit in getattr(self, 'lbl_caps_camion', {}).values():
            cap_lbl.setText(tr(tit))

        if hasattr(self, 'datos_partida_actual') and self.datos_partida_actual:
            self._refrescar_taller(self.datos_partida_actual)

    def _action_reiniciar_viaje(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return

        def _opt(trk):
            trk['trip_km'] = 0
            trk['trip_fuel_l'] = 0
            trk['trip_min'] = 0

        self._ejecutar_taller_optimista(
            'trip', ruta_g, self.btn_reiniciar_viaje, '¡Viaje reiniciado!',
            lambda r=ruta_g: profile_manager.restablecer_viaje_camion(r),
            _opt,
        )

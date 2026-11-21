from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSlider, QSpinBox,
)
from PySide6.QtCore import Qt
import profile_manager
from i18n import tr
from .comun import QMessageBox, notificar_exito_boton, TXT_PRINCIPAL, TXT_SECUNDARIO
from .tab_conductores import ESTILO_SLIDER, ESTILO_SPIN


class TabEmpresaMixin:
    """Pestaña Exploración y Mapa: ciudades, concesionarios y agencias del mundo."""

    def _tab_empresa_exploracion(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(14)

        # Tarjeta de exploración del mapa
        card_map = QFrame()
        card_map.setStyleSheet(
            'QFrame { background: #181A20; border: 1px solid #262932; border-radius: 8px; }'
            'QLabel { background: transparent; border: none; }'
        )
        lay_map = QVBoxLayout(card_map)
        lay_map.setContentsMargins(20, 18, 20, 20)
        lay_map.setSpacing(12)

        self.lbl_tit_map = QLabel(tr('Exploración y Desbloqueos del Mundo'))
        self.lbl_tit_map.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 15px; font-weight: 800;')
        self.lbl_desc_map = QLabel(tr('desc_exploracion'))
        self.lbl_desc_map.setStyleSheet(f'color: {TXT_SECUNDARIO}; font-size: 12px;')
        lay_map.addWidget(self.lbl_tit_map)
        lay_map.addWidget(self.lbl_desc_map)
        lay_map.addSpacing(6)

        # Ciudades
        self.ctrl_ciudades = self._crear_fila_exploracion_slider(
            titulo='Ciudades descubiertas para viaje rápido:',
            tooltip_aplicar='Guarda la cantidad seleccionada de ciudades descubiertas en el mapa.',
            tipo='ciudades',
        )
        lay_map.addLayout(self.ctrl_ciudades['layout'])

        # Concesionarios
        self.ctrl_concesionarios = self._crear_fila_exploracion_slider(
            titulo='Concesionarios de camiones desbloqueados:',
            tooltip_aplicar='Guarda la cantidad seleccionada de concesionarios de camiones desbloqueados.',
            tipo='concesionarios',
        )
        lay_map.addLayout(self.ctrl_concesionarios['layout'])

        # Agencias
        self.ctrl_agencias = self._crear_fila_exploracion_slider(
            titulo='Agencias de contratación de conductores:',
            tooltip_aplicar='Guarda la cantidad seleccionada de agencias de empleo desbloqueadas. Cuantas más agencias tengas, más conductores aparecerán disponibles para contratar.',
            tipo='agencias',
        )
        lay_map.addLayout(self.ctrl_agencias['layout'])

        lay_map.addSpacing(14)

        # Botones maestros
        fila_master = QHBoxLayout()
        fila_master.setSpacing(12)

        self.btn_desc_todo = QPushButton(tr('Desbloquear Todo al Máximo'))
        self.btn_desc_todo.setFixedHeight(34)
        self.btn_desc_todo.setCursor(Qt.PointingHandCursor)
        self.btn_desc_todo.setStyleSheet(self._estilo_btn('verde'))
        self.btn_desc_todo.setToolTip(
            "<div style='max-width: 270px;'>Desbloquea al 100% todas las ciudades del mapa, concesionarios de camiones y agencias de contratación de conductores.</div>"
        )
        self.btn_desc_todo.clicked.connect(
            lambda: self._action_desbloquear_exploracion(
                ciudades=True, concesionarios=True, agencias=True, boton=self.btn_desc_todo
            )
        )

        self.btn_bloq_todo = QPushButton(tr('Reiniciar Todo a Cero'))
        self.btn_bloq_todo.setFixedHeight(34)
        self.btn_bloq_todo.setCursor(Qt.PointingHandCursor)
        self.btn_bloq_todo.setStyleSheet(self._estilo_btn('rojo'))
        self.btn_bloq_todo.setToolTip(
            "<div style='max-width: 270px;'>Reinicia a cero las ciudades descubiertas, concesionarios y agencias de contratación para volver a explorarlos conduciendo.</div>"
        )
        self.btn_bloq_todo.clicked.connect(
            lambda: self._action_bloquear_exploracion(
                ciudades=True, concesionarios=True, agencias=True, boton=self.btn_bloq_todo
            )
        )

        fila_master.addWidget(self.btn_desc_todo, 1)
        fila_master.addWidget(self.btn_bloq_todo, 1)
        lay_map.addLayout(fila_master)

        lay.addWidget(card_map)
        lay.addStretch()
        return w

    def _crear_fila_exploracion_slider(self, titulo: str, tooltip_aplicar: str, tipo: str) -> dict:
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 3, 0, 3)
        fila.setSpacing(10)

        lbl_tit = QLabel(tr(titulo))
        lbl_tit.setFixedWidth(285)
        lbl_tit.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: bold;')

        slider = QSlider(Qt.Horizontal)
        slider.setStyleSheet(ESTILO_SLIDER)
        slider.setRange(0, 0)
        slider.setFixedHeight(24)

        spin = QSpinBox()
        spin.setStyleSheet(ESTILO_SPIN)
        spin.setRange(0, 0)
        spin.setFixedSize(72, 30)

        lbl_total = QLabel(f"{tr('de')} 0")
        lbl_total.setFixedWidth(56)
        lbl_total.setStyleSheet(f'color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: 700;')

        btn_aplicar = QPushButton(tr('Aplicar'))
        btn_aplicar.setFixedSize(95, 30)
        btn_aplicar.setCursor(Qt.PointingHandCursor)
        btn_aplicar.setStyleSheet(self._estilo_btn('azul'))
        btn_aplicar.setToolTip(f"<div style='max-width: 250px;'>{tooltip_aplicar}</div>")

        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(lambda _val, t=tipo: self._marcar_slider_empresa_modificado(t))
        spin.valueChanged.connect(lambda _val, t=tipo: self._marcar_slider_empresa_modificado(t))
        btn_aplicar.clicked.connect(
            lambda _, t=tipo, sp=spin, b=btn_aplicar: (
                sp.interpretText(),
                self._action_ajustar_exploracion_individual(t, sp.value(), b),
            )
        )

        fila.addWidget(lbl_tit)
        fila.addWidget(slider, 1)
        fila.addWidget(spin)
        fila.addWidget(lbl_total)
        fila.addWidget(btn_aplicar)

        return {
            'layout': fila,
            'slider': slider,
            'spin': spin,
            'lbl_total': lbl_total,
            'btn': btn_aplicar,
            'lbl_tit': lbl_tit,
            'titulo': titulo,
            'tipo': tipo,
            'dirty': False,
        }

    def _controles_empresa(self) -> tuple[dict, ...]:
        return (self.ctrl_ciudades, self.ctrl_concesionarios, self.ctrl_agencias)

    def _marcar_slider_empresa_modificado(self, tipo: str):
        for ctrl in self._controles_empresa():
            if ctrl.get('tipo') == tipo:
                ctrl['dirty'] = True
                return

    def _limpiar_dirty_empresa(self, ciudades: bool = False, concesionarios: bool = False, agencias: bool = False):
        mapa = {
            'ciudades': ciudades,
            'concesionarios': concesionarios,
            'agencias': agencias,
        }
        for ctrl in self._controles_empresa():
            if mapa.get(ctrl.get('tipo'), False):
                ctrl['dirty'] = False

    def _action_ajustar_exploracion_individual(self, tipo: str, cantidad: int, boton: QPushButton):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        self._limpiar_dirty_empresa(
            ciudades=tipo == 'ciudades',
            concesionarios=tipo == 'concesionarios',
            agencias=tipo == 'agencias',
        )
        kwargs = {}
        if tipo == 'ciudades':
            kwargs['n_ciudades'] = cantidad
        elif tipo == 'concesionarios':
            kwargs['n_concesionarios'] = cantidad
        elif tipo == 'agencias':
            kwargs['n_agencias'] = cantidad

        self._ejecutar_accion_partida_async(
            lambda: profile_manager.ajustar_exploracion_partida(ruta_guardado=ruta_g, **kwargs),
            boton=boton,
            texto_exito='¡Guardado!',
        )

    def _action_desbloquear_exploracion(
        self,
        ciudades: bool = False,
        concesionarios: bool = False,
        agencias: bool = False,
        boton: QPushButton = None,
    ):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        self._limpiar_dirty_empresa(ciudades=ciudades, concesionarios=concesionarios, agencias=agencias)
        self._ejecutar_accion_partida_async(
            lambda: profile_manager.desbloquear_exploracion_partida(
                ruta_g, ciudades=ciudades, concesionarios=concesionarios, agencias=agencias
            ),
            boton=boton,
            texto_exito='¡Todo Desbloqueado!',
        )

    def _action_bloquear_exploracion(
        self,
        ciudades: bool = False,
        concesionarios: bool = False,
        agencias: bool = False,
        boton: QPushButton = None,
    ):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        self._limpiar_dirty_empresa(ciudades=ciudades, concesionarios=concesionarios, agencias=agencias)
        self._ejecutar_accion_partida_async(
            lambda: profile_manager.bloquear_exploracion_partida(
                ruta_g, ciudades=ciudades, concesionarios=concesionarios, agencias=agencias
            ),
            boton=boton,
            texto_exito='¡Reiniciado!',
        )

    def _refrescar_empresa(self, datos: dict):
        ruta_g = self._obtener_ruta_guardado_actual()
        if ruta_g != getattr(self, '_empresa_dirty_ruta', None):
            self._empresa_dirty_ruta = ruta_g
            self._limpiar_dirty_empresa(ciudades=True, concesionarios=True, agencias=True)

        tc_cnt = max(0, int(datos.get('total_cities_count', 0)))
        vc_cnt = min(tc_cnt, max(0, int(datos.get('visited_cities_count', 0))))
        dl_cnt = min(tc_cnt, max(0, int(datos.get('unlocked_dealers_count', 0))))
        ag_cnt = min(tc_cnt, max(0, int(datos.get('unlocked_recruitments_count', 0))))

        for ctrl, val in (
            (self.ctrl_ciudades, vc_cnt),
            (self.ctrl_concesionarios, dl_cnt),
            (self.ctrl_agencias, ag_cnt),
        ):
            # Si el usuario movió el control y aún no aplicó, se respeta su valor
            val_mostrar = min(tc_cnt, max(0, ctrl['spin'].value())) if ctrl.get('dirty') and tc_cnt > 0 else val
            ctrl['slider'].blockSignals(True)
            ctrl['spin'].blockSignals(True)
            ctrl['slider'].setRange(0, tc_cnt)
            ctrl['spin'].setRange(0, tc_cnt)
            ctrl['slider'].setValue(val_mostrar)
            ctrl['spin'].setValue(val_mostrar)
            ctrl['lbl_total'].setText(f"{tr('de')} {tc_cnt}")
            ctrl['slider'].blockSignals(False)
            ctrl['spin'].blockSignals(False)
            ctrl['btn'].setEnabled(tc_cnt > 0)

    def _actualizar_idioma_tab_empresa(self):
        """Actualiza títulos y etiquetas de la pestaña Exploración y Mapa."""
        if hasattr(self, 'lbl_tit_map'):
            self.lbl_tit_map.setText(tr('Exploración y Desbloqueos del Mundo'))
        if hasattr(self, 'lbl_desc_map'):
            self.lbl_desc_map.setText(tr('desc_exploracion'))
        if hasattr(self, 'btn_desc_todo'):
            self.btn_desc_todo.setText(tr('Desbloquear Todo al Máximo'))
        if hasattr(self, 'btn_bloq_todo'):
            self.btn_bloq_todo.setText(tr('Reiniciar Todo a Cero'))
        for ctrl in (
            getattr(self, 'ctrl_ciudades', None),
            getattr(self, 'ctrl_concesionarios', None),
            getattr(self, 'ctrl_agencias', None),
        ):
            if ctrl:
                ctrl['lbl_tit'].setText(tr(ctrl['titulo']))
                ctrl['btn'].setText(tr('Aplicar'))
        if hasattr(self, 'datos_partida_actual') and self.datos_partida_actual:
            self._refrescar_empresa(self.datos_partida_actual)

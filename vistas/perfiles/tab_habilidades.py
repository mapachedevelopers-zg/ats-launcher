from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, QTimer
import threading
import profile_manager
from i18n import tr
from .comun import (
    QMessageBox, notificar_exito_boton, CSS_TARJETA,
    VERDE_TXT, VERDE_BORDE, VERDE_FONDO, VERDE_HOVER,
    NEUTRO_BORDE, NEUTRO_FONDO, NEUTRO_HOVER,
    TXT_PRINCIPAL, TXT_SECUNDARIO, TXT_APAGADO,
)


# (bit de máscara, nombre, descripción)
CLASES_ADR = [
    (1, 'Explosivos', 'Clase 1 · Dinamita, municiones y fuegos artificiales'),
    (2, 'Gases', 'Clase 2 · Gases inflamables, no inflamables y venenosos'),
    (4, 'Líquidos inflamables', 'Clase 3 · Gasolina, diésel, queroseno y petróleo'),
    (8, 'Sólidos inflamables', 'Clase 4 · Sólidos combustibles, magnesio y nitrato'),
    (16, 'Tóxicos e infecciosos', 'Clase 6 · Pesticidas, cianuro y residuos médicos'),
    (32, 'Corrosivos', 'Clase 8 · Ácidos industriales, baterías y sosa cáustica'),
]

# (clave, nombre, descripción)
HABILIDADES_NIVEL = [
    ('long_dist', 'Larga Distancia', 'Habilita rutas de mayor kilometraje y bonificación por distancia.'),
    ('heavy', 'Carga de Gran Valor', 'Bonificación extra en maquinaria pesada y mercancía costosa.'),
    ('fragile', 'Carga Frágil', 'Mayor recompensa al transportar cristal, electrónica y carga delicada.'),
    ('urgent', 'Entrega Justo a Tiempo', 'Habilita contratos urgentes con alta remuneración.'),
    ('mechanical', 'Conducción Eficiente', 'Reduce el consumo de diésel en ruta y transporte de carga.'),
]

_CSS_NIVEL_OFF = (
    f'QPushButton {{ background: #13171E; color: {TXT_APAGADO}; font-size: 11px; font-weight: 700; '
    f'border: 1px solid #222834; border-radius: 4px; padding: 0px; }}'
    f'QPushButton:hover {{ background: {NEUTRO_HOVER}; border-color: #475569; color: {TXT_PRINCIPAL}; }}'
)
_CSS_NIVEL_ON = (
    f'QPushButton {{ background: {VERDE_FONDO}; color: {VERDE_TXT}; font-size: 11px; font-weight: 800; '
    f'border: 1px solid {VERDE_BORDE}; border-radius: 4px; padding: 0px; }}'
    f'QPushButton:hover {{ background: {VERDE_HOVER}; color: #A7F3D0; border-color: #10B981; }}'
)
_CSS_NIVEL_CERO = (
    f'QPushButton {{ background: #1E2530; color: {TXT_PRINCIPAL}; font-size: 11px; font-weight: 800; '
    f'border: 1px solid #475569; border-radius: 4px; padding: 0px; }}'
)
_CSS_CHIP_ON = (
    f'QPushButton {{ background: {VERDE_FONDO}; color: {VERDE_TXT}; font-size: 12px; font-weight: 800; '
    f'border: 1px solid {VERDE_BORDE}; border-radius: 6px; padding: 0 10px; }}'
    f'QPushButton:hover {{ background: {VERDE_HOVER}; color: #A7F3D0; border-color: #10B981; }}'
)
_CSS_CHIP_OFF = (
    f'QPushButton {{ background: {NEUTRO_FONDO}; color: {TXT_SECUNDARIO}; font-size: 12px; font-weight: 700; '
    f'border: 1px solid {NEUTRO_BORDE}; border-radius: 6px; padding: 0 10px; }}'
    f'QPushButton:hover {{ background: {NEUTRO_HOVER}; border-color: #475569; color: {TXT_PRINCIPAL}; }}'
)


class TabHabilidadesMixin:
    """Pestaña Habilidades: certificaciones ADR (activada/desactivada) y habilidades por nivel (0 a 6)."""

    def _tab_habilidades(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(14)

        # Barra superior
        barra = QHBoxLayout()
        self.lbl_tit_habilidades = QLabel(tr('Habilidades del conductor'))
        self.lbl_tit_habilidades.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 14px; font-weight: 800;')
        barra.addWidget(self.lbl_tit_habilidades)
        barra.addStretch()
        lay.addLayout(barra)

        lay.addWidget(self._crear_tarjeta_adr())
        lay.addWidget(self._crear_tarjeta_niveles())
        lay.addStretch()
        return w

    def _crear_tarjeta_adr(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card')
        card.setStyleSheet(CSS_TARJETA)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(18, 14, 18, 14)
        c_lay.setSpacing(10)

        cab = QHBoxLayout()
        cab.setSpacing(6)
        self.lbl_tit_adr = QLabel(tr('Mercancías peligrosas (ADR)'))
        self.lbl_tit_adr.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 800;')
        self.lbl_resumen_adr = QLabel(f"0 / 6 {tr('activas')}")
        self.lbl_resumen_adr.setStyleSheet(f'color: {VERDE_TXT}; font-size: 12px; font-weight: 800;')

        self.btn_todas_adr = QPushButton(tr('Activar todas'))
        self.btn_todas_adr.setFixedHeight(24)
        self.btn_todas_adr.setCursor(Qt.PointingHandCursor)
        self.btn_todas_adr.setStyleSheet(self._estilo_btn('neutro', compacto=True))
        self.btn_todas_adr.setToolTip('Activa todas las certificaciones ADR y guarda inmediatamente')
        self.btn_todas_adr.clicked.connect(lambda: self._action_adr_todas(self.btn_todas_adr))

        self.btn_ninguna_adr = QPushButton(tr('Desactivar todas'))
        self.btn_ninguna_adr.setFixedHeight(24)
        self.btn_ninguna_adr.setCursor(Qt.PointingHandCursor)
        self.btn_ninguna_adr.setStyleSheet(self._estilo_btn('neutro', compacto=True))
        self.btn_ninguna_adr.setToolTip('Desactiva todas las certificaciones ADR y guarda inmediatamente')
        self.btn_ninguna_adr.clicked.connect(lambda: self._action_adr_ninguna(self.btn_ninguna_adr))

        cab.addWidget(self.lbl_tit_adr)
        cab.addSpacing(8)
        cab.addWidget(self.lbl_resumen_adr)
        cab.addStretch()
        cab.addWidget(self.btn_todas_adr)
        cab.addWidget(self.btn_ninguna_adr)
        c_lay.addLayout(cab)

        # Separador
        sep_adr = QFrame()
        sep_adr.setFixedHeight(1)
        sep_adr.setStyleSheet('background: #262932; border: none;')
        c_lay.addSpacing(2)
        c_lay.addWidget(sep_adr)
        c_lay.addSpacing(4)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.controles_adr = {}
        for idx, (mask, texto, tooltip) in enumerate(CLASES_ADR):
            chip = QPushButton(tr(texto))
            chip.setFixedHeight(32)
            chip.setCursor(Qt.PointingHandCursor)
            chip.setToolTip(tooltip)
            chip.clicked.connect(lambda checked=False, m=mask: self._toggle_clase_adr_ui(m))
            self.controles_adr[mask] = chip
            grid.addWidget(chip, idx // 3, idx % 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        c_lay.addLayout(grid)
        return card

    def _actualizar_ui_adr_mask(self, mask: int):
        mask = max(0, min(63, int(mask)))
        self.skills_editadas['adr'] = mask
        activas = 0
        for bit, chip in self.controles_adr.items():
            on = bool(mask & bit)
            activas += on
            chip.setStyleSheet(_CSS_CHIP_ON if on else _CSS_CHIP_OFF)
        if self.lbl_resumen_adr:
            self.lbl_resumen_adr.setText(f"{activas} / 6 {tr('activas')}")

    def _toggle_clase_adr_ui(self, bit_mask: int):
        juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
        if not juego_ok:
            QMessageBox.warning(self, 'Atención', msg_juego)
            return
        self._actualizar_ui_adr_mask(int(self.skills_editadas.get('adr', 0)) ^ bit_mask)
        self._programar_guardado_skills_debounce()

    def _action_adr_todas(self, boton=None):
        juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
        if not juego_ok:
            QMessageBox.warning(self, 'Atención', msg_juego)
            return
        self._actualizar_ui_adr_mask(63)
        self._guardar_skills_inmediato(boton_feedback=boton)

    def _action_adr_ninguna(self, boton=None):
        juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
        if not juego_ok:
            QMessageBox.warning(self, 'Atención', msg_juego)
            return
        self._actualizar_ui_adr_mask(0)
        self._guardar_skills_inmediato(boton_feedback=boton)

    def _crear_tarjeta_niveles(self) -> QFrame:
        card = QFrame()
        card.setObjectName('card')
        card.setStyleSheet(CSS_TARJETA)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(18, 14, 18, 14)
        c_lay.setSpacing(0)

        cab = QHBoxLayout()
        cab.setSpacing(6)
        self.lbl_tit_niveles = QLabel(tr('Niveles de habilidad'))
        self.lbl_tit_niveles.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 800;')

        self.btn_max_niveles = QPushButton(tr('Maximizar todos'))
        self.btn_max_niveles.setFixedHeight(24)
        self.btn_max_niveles.setCursor(Qt.PointingHandCursor)
        self.btn_max_niveles.setStyleSheet(self._estilo_btn('neutro', compacto=True))
        self.btn_max_niveles.setToolTip('Maximiza todos los niveles a 6/6 (sin alterar ADR) y guarda inmediatamente')
        self.btn_max_niveles.clicked.connect(self._action_maximizar_niveles_skills)

        cab.addWidget(self.lbl_tit_niveles)
        cab.addStretch()
        cab.addWidget(self.btn_max_niveles)
        c_lay.addLayout(cab)

        # Separador
        sep_niveles = QFrame()
        sep_niveles.setFixedHeight(1)
        sep_niveles.setStyleSheet('background: #262932; border: none;')
        c_lay.addSpacing(4)
        c_lay.addWidget(sep_niveles)
        c_lay.addSpacing(4)

        self.controles_skills = {}
        for i, (clave, titulo, tooltip) in enumerate(HABILIDADES_NIVEL):
            if i:
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet('background: #222630;')
                c_lay.addWidget(sep)

            fila = QHBoxLayout()
            fila.setContentsMargins(0, 8, 0, 8)
            fila.setSpacing(12)

            lbl_t = QLabel(tr(titulo))
            lbl_t.setToolTip(tooltip)
            lbl_t.setMinimumWidth(170)
            lbl_t.setStyleSheet(f'color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 700;')

            barra = QHBoxLayout()
            barra.setSpacing(4)
            botones = []
            for n in range(7):
                b = QPushButton(str(n))
                b.setFixedSize(40, 26)
                b.setCursor(Qt.PointingHandCursor)
                b.clicked.connect(lambda checked=False, k=clave, v=n: self._seleccionar_nivel_skill_ui(k, v))
                barra.addWidget(b)
                botones.append(b)

            lbl_val = QLabel('0 / 6')
            lbl_val.setFixedWidth(56)
            lbl_val.setAlignment(Qt.AlignCenter)

            fila.addWidget(lbl_t, 1)
            fila.addLayout(barra)
            fila.addWidget(lbl_val)
            c_lay.addLayout(fila)

            self.controles_skills[clave] = {'label': lbl_val, 'botones': botones, 'lbl_t': lbl_t, 'titulo': titulo}
        return card

    def _actualizar_idioma_tab_habilidades(self):
        """Actualiza todos los textos estáticos y dinámicos de la pestaña Habilidades."""
        if hasattr(self, 'lbl_tit_habilidades') and self.lbl_tit_habilidades:
            self.lbl_tit_habilidades.setText(tr('Habilidades del conductor'))
        if hasattr(self, 'lbl_tit_adr') and self.lbl_tit_adr:
            self.lbl_tit_adr.setText(tr('Mercancías peligrosas (ADR)'))
        if hasattr(self, 'btn_todas_adr') and self.btn_todas_adr:
            self.btn_todas_adr.setText(tr('Activar todas'))
        if hasattr(self, 'btn_ninguna_adr') and self.btn_ninguna_adr:
            self.btn_ninguna_adr.setText(tr('Desactivar todas'))
        if hasattr(self, 'btn_max_niveles') and self.btn_max_niveles:
            self.btn_max_niveles.setText(tr('Maximizar todos'))
        if hasattr(self, 'lbl_tit_niveles') and self.lbl_tit_niveles:
            self.lbl_tit_niveles.setText(tr('Niveles de habilidad'))

        for mask, texto, tooltip in CLASES_ADR:
            if hasattr(self, 'controles_adr') and mask in self.controles_adr:
                self.controles_adr[mask].setText(tr(texto))

        for clave, info in getattr(self, 'controles_skills', {}).items():
            if 'lbl_t' in info and 'titulo' in info:
                info['lbl_t'].setText(tr(info['titulo']))

        if hasattr(self, 'skills_editadas'):
            self._actualizar_ui_adr_mask(int(self.skills_editadas.get('adr', 0)))

    def _seleccionar_nivel_skill_ui(self, clave: str, nivel: int, debounce: bool = True):
        if debounce:
            juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
            if not juego_ok:
                QMessageBox.warning(self, 'Atención', msg_juego)
                return
        nivel = max(0, min(6, int(nivel)))
        self.skills_editadas[clave] = nivel
        ctrl = self.controles_skills.get(clave)
        if ctrl:
            ctrl['label'].setText(f'{nivel} / 6')
            color = VERDE_TXT if nivel > 0 else TXT_APAGADO
            ctrl['label'].setStyleSheet(f'background: transparent; border: none; padding: 0px; color: {color}; font-size: 12px; font-weight: 800;')

            # El botón 0 se resalta solo cuando el nivel es 0; el resto se llena hasta el nivel actual
            for i, btn in enumerate(ctrl['botones']):
                if i == 0:
                    btn.setStyleSheet(_CSS_NIVEL_CERO if nivel == 0 else _CSS_NIVEL_OFF)
                else:
                    btn.setStyleSheet(_CSS_NIVEL_ON if i <= nivel else _CSS_NIVEL_OFF)
        if debounce:
            self._programar_guardado_skills_debounce()

    def _refrescar_habilidades(self, datos: dict):
        skills = datos.get('skills', {})
        self._actualizar_ui_adr_mask(skills.get('adr', 0))
        for clave, _, _ in HABILIDADES_NIVEL:
            self._seleccionar_nivel_skill_ui(clave, skills.get(clave, 0), debounce=False)
        self._skills_guardadas = dict(self.skills_editadas)
        self._skills_dirty = False

    def _action_maximizar_niveles_skills(self):
        """Maximiza solo los niveles de habilidad a 6/6 (sin tocar ADR) y guarda silenciosamente de inmediato."""
        juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
        if not juego_ok:
            QMessageBox.warning(self, 'Atención', msg_juego)
            return
        for clave, _, _ in HABILIDADES_NIVEL:
            self._seleccionar_nivel_skill_ui(clave, 6, debounce=False)
        self._guardar_skills_inmediato(boton_feedback=getattr(self, 'btn_max_niveles', None))

    def _programar_guardado_skills_debounce(self):
        """Buffer ultrarrápido y silencioso (800ms) para guardar automáticamente en segundo plano."""
        self._skills_dirty = True
        if not hasattr(self, '_timer_guardar_skills') or self._timer_guardar_skills is None:
            self._timer_guardar_skills = QTimer(self)
            self._timer_guardar_skills.setSingleShot(True)
            self._timer_guardar_skills.timeout.connect(self._guardar_skills_inmediato)
        self._timer_guardar_skills.start(800)

    def _guardar_skills_inmediato(self, boton_feedback=None):
        """Guarda en disco mediante la cola serializada en segundo plano para evitar bloqueos y carreras."""
        if hasattr(self, '_timer_guardar_skills') and self._timer_guardar_skills and self._timer_guardar_skills.isActive():
            self._timer_guardar_skills.stop()

        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return

        if getattr(self, '_skills_guardadas', None) == self.skills_editadas and not getattr(self, '_skills_dirty', False):
            return

        self._skills_dirty = False
        snapshot_skills = dict(self.skills_editadas)

        self._encolar_edicion_ligera_async(
            'skills',
            ruta_g,
            tr('Guardando...'),
            lambda r=ruta_g, s=snapshot_skills: profile_manager.guardar_skills_partida(r, s),
            boton=boton_feedback,
            texto_exito='¡Guardado!',
            on_result=lambda exito, msg, r=ruta_g, s=snapshot_skills: self._on_guardado_skills_async_completado(exito, msg, s, None),
        )

    def _on_guardado_skills_async_completado(self, exito: bool, msg: str, snapshot_skills: dict, boton_feedback=None):
        self._guardando_skills_en_hilo = False

        if exito:
            self._skills_guardadas = dict(snapshot_skills)
            if hasattr(self, 'datos_partida_actual') and self.datos_partida_actual:
                self.datos_partida_actual['skills'] = dict(snapshot_skills)
            if boton_feedback is not None:
                notificar_exito_boton(boton_feedback, '¡Guardado!')
        else:
            if hasattr(self, '_skills_guardadas') and self._skills_guardadas:
                self.skills_editadas = dict(self._skills_guardadas)
                self._actualizar_ui_adr_mask(self.skills_editadas.get('adr', 0))
                for clave, _, _ in HABILIDADES_NIVEL:
                    self._seleccionar_nivel_skill_ui(clave, self.skills_editadas.get(clave, 0), debounce=False)
            self._skills_dirty = False
            QMessageBox.warning(self, 'Atención', msg)

        if getattr(self, '_skills_dirty', False):
            self._guardar_skills_inmediato()

import threading
import time

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
                               QComboBox, QFrame, QTabWidget, QSpinBox, QDialog, QMenu, QInputDialog,
                               QProgressBar, QScrollArea, QLineEdit, QToolButton, QStyledItemDelegate)
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEvent, QPoint, QSize, QRect
from PySide6.QtGui import QColor, QFont, QCursor, QPainter, QPen, QBrush
from utils import aplicar_sombra
from temas import obtener_tema_actual
from i18n import tr
import profile_manager
from .comun import QMessageBox, EstilosMixin, SeñalesPerfilUI, notificar_exito_boton
from .dialogos import DialogoInfoTipoPerfil
from .tab_economia import TabEconomiaMixin
from .tab_habilidades import TabHabilidadesMixin
from .tab_garajes import TabGarajesMixin
from .tab_conductores import TabConductoresMixin
from .tab_camiones import TabCamionesMixin
from .tab_empresa import TabEmpresaMixin
from .tab_taller import TabTallerMixin
from .tab_estabilidad import TabEstabilidadMixin


class TabDragFilter(QObject):
    """Permite cambiar de pestaña arrastrando horizontalmente con el ratón (drag to swipe)."""

    def __init__(self, tab_widget: QTabWidget):
        super().__init__(tab_widget)
        self.tab_widget = tab_widget
        self._start_x = None
        self._is_dragging = False

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._start_x = event.position().toPoint().x()
            self._is_dragging = False
        elif event.type() == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
            if self._start_x is not None:
                dx = event.position().toPoint().x() - self._start_x
                if abs(dx) > 10:
                    self._is_dragging = True
                    self.tab_widget.tabBar().setCursor(Qt.ClosedHandCursor)

                if dx < -35:
                    curr = self.tab_widget.currentIndex()
                    if curr < self.tab_widget.count() - 1:
                        self.tab_widget.setCurrentIndex(curr + 1)
                    self._start_x = event.position().toPoint().x()
                    return True
                elif dx > 35:
                    curr = self.tab_widget.currentIndex()
                    if curr > 0:
                        self.tab_widget.setCurrentIndex(curr - 1)
                    self._start_x = event.position().toPoint().x()
                    return True
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.tab_widget.tabBar().setCursor(Qt.PointingHandCursor)
            was_dragging = self._is_dragging
            self._start_x = None
            self._is_dragging = False
            if was_dragging:
                return True
        return super().eventFilter(obj, event)


class ProfileItemDelegate(QStyledItemDelegate):
    """Renderiza los elementos del desplegable de perfiles con secciones estilizadas
    para 'PERFILES LOCALES' y 'PERFILES DE STEAM CLOUD' y un botón de información interactivo (!)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_row = -1

    def sizeHint(self, option, index):
        if index.data(Qt.UserRole + 10):
            if index.data(Qt.UserRole + 11) == 'steam':
                return QSize(option.rect.width(), 40)
            return QSize(option.rect.width(), 32)
        return QSize(option.rect.width(), 28)

    def paint(self, painter, option, index):
        is_header = index.data(Qt.UserRole + 10)
        if is_header:
            header_type = index.data(Qt.UserRole + 11)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            rect = option.rect

            # Separador superior para la sección de Steam
            if header_type == 'steam':
                line_y = rect.top() + 8
                painter.setPen(QPen(QColor('#243042'), 1))
                painter.drawLine(rect.left() + 10, line_y, rect.right() - 10, line_y)
                title_rect = QRect(rect.left(), rect.top() + 12, rect.width(), rect.height() - 12)
            else:
                title_rect = rect

            accent_color = QColor('#38BDF8') if header_type == 'locales' else QColor('#F59E0B')

            # Barra de acento
            bar_y = title_rect.top() + (title_rect.height() - 12) // 2
            painter.setBrush(QBrush(accent_color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(title_rect.left() + 10, bar_y, 3, 12, 1.5, 1.5)

            # Título de la categoría
            painter.setPen(QColor('#94A3B8'))
            font_cat = QFont('Segoe UI', 8, QFont.Bold)
            font_cat.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
            painter.setFont(font_cat)
            text_rect = title_rect.adjusted(20, 0, -45, 0)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole))

            # Botón de información (!)
            btn_size = 18
            btn_x = title_rect.right() - btn_size - 10
            btn_y = title_rect.top() + (title_rect.height() - btn_size) // 2
            btn_rect = QRect(btn_x, btn_y, btn_size, btn_size)

            is_hovered = self.hover_row == index.row()
            if is_hovered:
                painter.setBrush(QBrush(QColor(56, 189, 248, 50) if header_type == 'locales' else QColor(245, 158, 11, 50)))
                painter.setPen(QPen(accent_color, 1.2))
            else:
                painter.setBrush(QBrush(QColor('#161D27')))
                painter.setPen(QPen(QColor('#334155'), 1))

            painter.drawEllipse(btn_rect)

            painter.setPen(accent_color if is_hovered else QColor('#94A3B8'))
            font_sym = QFont('Segoe UI', 9, QFont.Bold)
            painter.setFont(font_sym)
            painter.drawText(btn_rect, Qt.AlignCenter, '!')

            painter.restore()
            return

        # Elemento normal (perfil)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        is_steam_item = not option.state & option.state.State_Enabled
        is_hovered = self.hover_row == index.row() or bool(option.state & option.state.State_MouseOver)
        is_selected = bool(option.state & option.state.State_Selected) and not is_steam_item

        item_rect = option.rect.adjusted(4, 1, -4, -1)

        if is_selected:
            if is_hovered:
                painter.setBrush(QBrush(QColor('#253A54')))
                painter.setPen(QPen(QColor('#38BDF8'), 1))
            else:
                painter.setBrush(QBrush(QColor('#1E2D42')))
                painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(item_rect, 4, 4)
        elif is_hovered:
            if is_steam_item:
                # Hover en perfil bloqueado por Steam Cloud
                painter.setBrush(QBrush(QColor('#231C14')))
                painter.setPen(QPen(QColor(245, 158, 11, 70), 1))
            else:
                # Hover en perfil local
                painter.setBrush(QBrush(QColor('#1A2638')))
                painter.setPen(QPen(QColor(56, 189, 248, 60), 1))
            painter.drawRoundedRect(item_rect, 4, 4)

        # Texto
        text_rect = option.rect.adjusted(18, 0, -10, 0)
        if is_steam_item:
            font_item = QFont('Segoe UI', 9)
            font_item.setItalic(True)
            painter.setPen(QColor('#CBD5E1') if is_hovered else QColor('#64748B'))
        else:
            font_item = QFont('Segoe UI', 9, QFont.Bold)
            painter.setPen(QColor('#FFFFFF') if is_hovered or is_selected else QColor('#F8FAFC'))

        painter.setFont(font_item)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole))

        painter.restore()


class ProfileHeaderFilter(QObject):
    """Intercepta clics y movimiento sobre los elementos del combo de perfiles
    para gestionar cursores interactivos, hover dinámico y el diálogo explicativo de los encabezados."""

    def __init__(self, combo: QComboBox, delegate: ProfileItemDelegate, callback_info):
        super().__init__(combo)
        self.combo = combo
        self.delegate = delegate
        self.callback_info = callback_info

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            idx = self.combo.view().indexAt(pos)
            if idx.isValid():
                if idx.data(Qt.UserRole + 10):
                    self.combo.view().viewport().setCursor(Qt.PointingHandCursor)
                    self.combo.view().setCursor(Qt.PointingHandCursor)
                else:
                    # Perfil de Steam Cloud (deshabilitado) o perfil local
                    is_steam = not idx.flags() & Qt.ItemIsEnabled
                    cursor = Qt.PointingHandCursor if not is_steam else Qt.PointingHandCursor
                    self.combo.view().viewport().setCursor(cursor)
                    self.combo.view().setCursor(cursor)

                if self.delegate.hover_row != idx.row():
                    self.delegate.hover_row = idx.row()
                    self.combo.view().viewport().update()
            else:
                self.combo.view().viewport().setCursor(Qt.ArrowCursor)
                self.combo.view().setCursor(Qt.ArrowCursor)
                if self.delegate.hover_row != -1:
                    self.delegate.hover_row = -1
                    self.combo.view().viewport().update()

        elif event.type() == QEvent.Leave:
            self.combo.view().viewport().setCursor(Qt.ArrowCursor)
            self.combo.view().setCursor(Qt.ArrowCursor)
            if self.delegate.hover_row != -1:
                self.delegate.hover_row = -1
                self.combo.view().viewport().update()

        elif event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            idx = self.combo.view().indexAt(pos)
            if idx.isValid() and idx.data(Qt.UserRole + 10):
                if event.type() == QEvent.MouseButtonRelease:
                    tipo = idx.data(Qt.UserRole + 11)
                    self.combo.hidePopup()
                    if callable(self.callback_info):
                        self.callback_info(tipo)
                return True

        return super().eventFilter(obj, event)


class PaginaPerfiles(EstilosMixin, TabEconomiaMixin, TabHabilidadesMixin, TabGarajesMixin,
                     TabConductoresMixin, TabCamionesMixin, TabEmpresaMixin, TabTallerMixin,
                     TabEstabilidadMixin, QWidget):
    """Editor de perfiles: barra de selección + pestañas (cada pestaña vive en su propio módulo)."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.perfiles = []
        self.guardados = []
        self.datos_partida_actual = {
            'money': 0,
            'xp': 0,
            'skills': {'adr': 0, 'long_dist': 0, 'heavy': 0, 'fragile': 0, 'urgent': 0, 'mechanical': 0},
            'loans_count': 0,
            'loans_amount': 0,
            'overdraft': False,
            'garages': [],
            'hq_city': '',
            'all_cities': [],
            'visited_cities_count': 0,
            'total_cities_count': 0,
            'unlocked_dealers_count': 0,
            'unlocked_recruitments_count': 0,
            'hired_drivers_count': 0,
            'pool_drivers_count': 0,
            'free_driver_slots': 0,
            'free_truck_slots': 0,
            'avg_driver_rating': 5.0,
            'company_trucks_count': 0,
            'idle_hired_drivers_count': 0,
            'empty_trucks_count': 0,
            'drivers_with_truck_count': 0,
            'used_trucks': [],
            'truck': {
                'found': False, 'id': '', 'fuel_pct': 100,
                'max_wear_pct': 0.0, 'max_unfixable_pct': 0.0,
                'odometer': 0, 'plate_raw': '', 'plate_text': '', 'plate_state': '',
            },
        }
        self.skills_editadas = {
            'adr': 0, 'long_dist': 0, 'heavy': 0, 'fragile': 0, 'urgent': 0, 'mechanical': 0,
        }
        self._skills_dirty = False
        self._skills_guardadas = {}
        self._timer_guardar_skills = None
        self.controles_skills = {}
        self.controles_adr = {}
        self.lbl_resumen_adr = None
        self.filas_garajes = []
        self.filas_camiones = []
        self._operacion_en_curso = False
        self._operacion_perfil_en_curso = False
        self._reparacion_en_curso = False
        self._secuencia_cola = 0
        self._req_id_perfil = 0
        self._req_id_partida = 0
        self._tabs_sucias = set(range(8))
        self._lock_saneamiento = threading.Lock()
        self._cola_escrituras = []
        self._escritura_en_vuelo = None
        self._cond_escrituras = threading.Condition()
        self._trabajador_escrituras_iniciado = False
        self._estado_async_activo = False
        self._texto_estado_async = tr('Procesando...')
        self._anim_frame = 0
        self._timer_anim_carga = None
        self._timer_ocultar_estado = None

        self.señales = SeñalesPerfilUI()
        self.señales.datos_cargados.connect(self._on_datos_partida_cargados)
        self.señales.datos_cargados_req.connect(self._on_datos_partida_cargados_req)
        self.señales.guardados_cargados.connect(self._on_guardados_cargados)
        self.señales.lista_perfiles_lista.connect(self._on_perfiles_cargados)
        self.señales.operacion_perfil_terminada.connect(self._on_operacion_perfil_terminada)
        self.señales.accion_partida_terminada.connect(self._on_accion_partida_terminada)
        self.señales.edicion_ligera_terminada.connect(self._on_edicion_ligera_terminada)
        self.señales.reparacion_terminada.connect(self._on_reparacion_terminada)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 15, 25, 20)
        layout_principal.setSpacing(12)

        # --- Barra superior: perfil + partida ---
        self.barra_sup = QFrame()
        aplicar_sombra(self.barra_sup)
        lay_bar = QHBoxLayout(self.barra_sup)
        lay_bar.setContentsMargins(14, 8, 14, 8)
        lay_bar.setSpacing(10)

        self.lbl_perfil = QLabel(tr('Perfil:'))
        self.lbl_perfil.setStyleSheet('color: #94A3B8; font-weight: bold; border: none;')
        self.combo_perfiles = QComboBox()
        self.combo_perfiles.setFixedHeight(34)
        self.combo_perfiles.setStyleSheet(self._estilo_combo())
        self.combo_perfiles.setToolTip('Selecciona el perfil activo')
        self.combo_perfiles.view().setMouseTracking(True)
        self.combo_perfiles.view().viewport().setMouseTracking(True)
        self._profile_delegate = ProfileItemDelegate(self.combo_perfiles)
        self.combo_perfiles.setItemDelegate(self._profile_delegate)
        self._configurar_combo_un_clic(self.combo_perfiles, self._on_perfil_seleccionado)
        self._header_filter = ProfileHeaderFilter(
            self.combo_perfiles, self._profile_delegate, self._mostrar_info_tipo_perfil
        )
        self.combo_perfiles.view().viewport().installEventFilter(self._header_filter)
        self.combo_perfiles.view().installEventFilter(self._header_filter)

        self.btn_opciones = QPushButton(tr('Opciones'))
        self.btn_opciones.setFixedHeight(34)
        self.btn_opciones.setCursor(Qt.PointingHandCursor)
        self.btn_opciones.setToolTip(
            'Gestionar perfil (Clonar, Renombrar, Eliminar)')
        self.btn_opciones.setStyleSheet(self._estilo_btn('azul'))
        self._configurar_menu_opciones()

        self.lbl_partida = QLabel(tr('Partida:'))
        self.lbl_partida.setStyleSheet('color: #94A3B8; font-weight: bold; border: none;')
        self.combo_guardados = QComboBox()
        self.combo_guardados.setFixedHeight(34)
        self.combo_guardados.setStyleSheet(self._estilo_combo())
        self.combo_guardados.setToolTip('Selecciona la partida guardada')
        self._configurar_combo_un_clic(self.combo_guardados, self._on_guardado_seleccionado)

        self.lbl_estado_async = QLabel('')
        self.lbl_estado_async.setFixedHeight(28)
        self.lbl_estado_async.setStyleSheet(
            'background: rgba(59, 130, 246, 0.14); color: #60A5FA; '
            'border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 6px; '
            'padding: 0 10px; font-size: 11px; font-weight: 700;'
        )
        self.lbl_estado_async.hide()

        self.btn_refrescar = QPushButton('↻')
        self.btn_refrescar.setFixedSize(34, 34)
        self.btn_refrescar.setCursor(Qt.PointingHandCursor)
        self.btn_refrescar.setToolTip(
            'Recargar lista de perfiles y desencriptar datos')
        self.btn_refrescar.setStyleSheet(self._estilo_btn('neutro', compacto=True))
        self.btn_refrescar.clicked.connect(lambda *_: self.cargar_perfiles_async())

        lay_bar.addWidget(self.lbl_perfil)
        lay_bar.addWidget(self.combo_perfiles, 2)
        lay_bar.addWidget(self.btn_opciones)
        lay_bar.addWidget(self.lbl_partida)
        lay_bar.addWidget(self.combo_guardados, 2)
        lay_bar.addWidget(self.lbl_estado_async)
        lay_bar.addWidget(self.btn_refrescar)

        layout_principal.addWidget(self.barra_sup)

        # --- Pestañas ---
        self.tabs = QTabWidget()
        self.tabs.tabBar().setCursor(Qt.PointingHandCursor)
        self.actualizar_estilo_tabs()

        # Cambio de pestaña arrastrando con el ratón
        self._drag_filter = TabDragFilter(self.tabs)
        self.tabs.tabBar().installEventFilter(self._drag_filter)

        self.tabs.addTab(self._tab_economia(), 'Economía y Nivel')
        self.tabs.addTab(self._tab_habilidades(), 'Habilidades')
        self.tabs.addTab(self._tab_garajes(), 'Garajes')
        self.tabs.addTab(self._tab_conductores(), 'Conductores')
        self.tabs.addTab(self._tab_camiones_flota(), 'Camiones')
        self.tabs.addTab(self._tab_empresa_exploracion(), 'Exploración y Mapa')
        self.tabs.addTab(self._tab_taller_vehiculo(), 'Taller y Vehículo')
        self.tabs.addTab(self._tab_estabilidad_antivuelco(), 'Física y Antivuelco')
        self.tabs.currentChanged.connect(self._on_tab_cambiada)

        self._scroll_conectado = False
        self._configurar_botones_scroll()

        layout_principal.addWidget(self.tabs, 1)

        self.cargar_perfiles_async()

    def _formatear_nombre_guardado(self, g: dict) -> str:
        gid = g.get('id', '')
        nombre_base = g.get('nombre_base') or g.get('nombre', '')
        prefix = f"[{tr('Más reciente')}] " if g.get('es_mas_reciente') else ''
        if gid == 'quicksave':
            base = tr('Guardado Rápido')
        elif gid == 'autosave':
            base = tr('Autoguardado')
        elif gid.startswith('autosave_drive'):
            sufijo = gid.replace('autosave_drive', '').replace('_', ' ').strip()
            base = f"{tr('Autoguardado en ruta')} {sufijo}".strip()
        elif gid.startswith('autosave_job'):
            sufijo = gid.replace('autosave_job', '').replace('_', ' ').strip()
            base = f"{tr('Autoguardado de trabajo')} {sufijo}".strip()
        elif gid.startswith('multiplayer_backup'):
            sufijo = gid.replace('multiplayer_backup', '').replace('_', ' ').strip()
            base = f"{tr('Autoguardado Convoy')} {sufijo}".strip()
        elif gid.isdigit():
            base = f"{tr('Partida')} {gid}"
        else:
            base = tr(nombre_base)
        return f'{prefix}{base}'

    def actualizar_textos_idioma(self):
        """Actualiza los títulos de las pestañas y textos de la cabecera al cambiar de idioma."""
        if hasattr(self, 'lbl_perfil') and self.lbl_perfil:
            self.lbl_perfil.setText(tr('Perfil:'))
        if hasattr(self, 'lbl_partida') and self.lbl_partida:
            self.lbl_partida.setText(tr('Partida:'))
        if hasattr(self, 'btn_opciones') and self.btn_opciones:
            self.btn_opciones.setText(tr('Opciones'))
            self._configurar_menu_opciones()
        if hasattr(self, 'tabs') and self.tabs:
            pestanas = [
                'Economía y Nivel',
                'Habilidades',
                'Garajes',
                'Conductores',
                'Camiones',
                'Exploración y Mapa',
                'Taller y Vehículo',
                'Física y Antivuelco',
            ]
            for idx, clave in enumerate(pestanas):
                if idx < self.tabs.count():
                    self.tabs.setTabText(idx, tr(clave))

        # Cada pestaña refresca sus propios textos
        if hasattr(self, '_actualizar_idioma_tab_economia'):
            self._actualizar_idioma_tab_economia()
        if hasattr(self, '_actualizar_idioma_tab_habilidades'):
            self._actualizar_idioma_tab_habilidades()
        if hasattr(self, '_actualizar_idioma_tab_garajes'):
            self._actualizar_idioma_tab_garajes()
        if hasattr(self, '_actualizar_idioma_tab_conductores'):
            self._actualizar_idioma_tab_conductores()
        if hasattr(self, '_actualizar_idioma_tab_camiones'):
            self._actualizar_idioma_tab_camiones()
        if hasattr(self, '_actualizar_idioma_tab_empresa'):
            self._actualizar_idioma_tab_empresa()
        if hasattr(self, '_actualizar_idioma_tab_taller'):
            self._actualizar_idioma_tab_taller()
        if hasattr(self, '_actualizar_idioma_tab_estabilidad'):
            self._actualizar_idioma_tab_estabilidad()

        # Encabezados del combo de perfiles
        if hasattr(self, 'combo_perfiles') and self.combo_perfiles:
            model = self.combo_perfiles.model()
            for i in range(self.combo_perfiles.count()):
                if hasattr(model, 'item'):
                    it = model.item(i)
                    if it and it.data(Qt.UserRole + 10):
                        htype = it.data(Qt.UserRole + 11)
                        self.combo_perfiles.setItemText(i, tr('PERFILES LOCALES') if htype == 'locales' else tr('PERFILES DE STEAM CLOUD'))
                    elif it and not it.isEnabled():
                        it.setToolTip(tr("⚠️ Perfil bloqueado por Steam Cloud.\nPara editarlo: en el juego desmarca 'Sincronización con Steam Cloud' en Editar trayectoria."))

        # Nombres de las partidas guardadas
        if hasattr(self, 'combo_guardados') and self.combo_guardados:
            for i in range(self.combo_guardados.count()):
                g = self.combo_guardados.itemData(i)
                if isinstance(g, dict):
                    self.combo_guardados.setItemText(i, self._formatear_nombre_guardado(g))

    def actualizar_estilo_tabs(self):
        """Aplica los colores del tema activo a las pestañas y botones de desplazamiento."""
        tema = obtener_tema_actual()
        acento = tema.get('acento', '#E5A93C')
        contraste = tema.get('contraste', '#0F172A')
        fondo_tab = tema.get('fondo_boton_menu', '#181A20')
        fondo_hover = tema.get('fondo_boton_hover', '#22252E')
        fondo_pane = tema.get('fondo_tarjeta', '#0F172A')
        fondo_sub = tema.get('fondo_sidebar', '#111317')
        borde = tema.get('borde_tarjeta', '#262932')

        if hasattr(self, 'barra_sup') and self.barra_sup:
            self.barra_sup.setStyleSheet(
                f'QFrame {{ background: {fondo_tab}; border: 1px solid {borde}; border-radius: 8px; }}'
            )

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {borde}; background: {fondo_pane}; border-radius: 8px; }}
            QTabWidget QLabel {{ background: transparent; border: none; }}
            QTabBar::tab {{
                background: {fondo_tab}; color: #94A3B8; font-weight: 700; font-size: 12px;
                padding: 8px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 3px;
            }}
            QTabBar::tab:selected {{ background: {acento}; color: {contraste}; font-weight: 900; }}
            QTabBar::tab:hover:!selected {{ background: {fondo_hover}; color: #F8FAFC; }}
            QTabBar QToolButton {{
                background: {fondo_tab}; border: 1px solid {borde}; border-radius: 4px;
                color: #CBD5E1; margin: 1px;
            }}
            QTabBar QToolButton:hover {{
                background: {fondo_hover}; border-color: {acento}; color: {acento};
            }}
            QTabBar QToolButton:disabled {{
                background: {fondo_sub}; color: #475569; border-color: {borde};
            }}
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self._configurar_botones_scroll()

    def _configurar_botones_scroll(self):
        """Conecta las flechas del tab bar para cambiar de sección directamente y evitar recortes."""
        if getattr(self, '_scroll_conectado', False):
            return
        tb = self.tabs.tabBar()
        encontrados = 0
        for btn in tb.findChildren(QToolButton):
            name = btn.objectName()
            if name == 'ScrollLeftButton':
                btn.clicked.connect(self._scroll_tab_anterior)
                encontrados += 1
            elif name == 'ScrollRightButton':
                btn.clicked.connect(self._scroll_tab_siguiente)
                encontrados += 1
        if encontrados >= 2:
            self._scroll_conectado = True

    def _scroll_tab_anterior(self):
        curr = self.tabs.currentIndex()
        if curr > 0:
            self.tabs.setCurrentIndex(curr - 1)

    def _scroll_tab_siguiente(self):
        curr = self.tabs.currentIndex()
        if curr < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(curr + 1)

    def _configurar_menu_opciones(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            'QMenu { background: #181A20; color: #F8FAFC; border: 1px solid #334155; } '
            'QMenu::item:selected { background: #334155; color: #FFFFFF; }'
        )

        act_clonar = menu.addAction(tr('Clonar Perfil'))
        act_clonar.setToolTip('Crea un duplicado del perfil completo')
        act_clonar.triggered.connect(self._action_clonar_perfil)

        act_renombrar = menu.addAction(tr('Renombrar Perfil'))
        act_renombrar.setToolTip(
            'Cambia el nombre visible y la carpeta del perfil')
        act_renombrar.triggered.connect(self._action_renombrar_perfil)

        menu.addSeparator()

        act_reparar = menu.addAction(tr('Comprobar y Reparar Partida'))
        act_reparar.setToolTip(
            'Inspecciona la partida seleccionada y repara automáticamente posibles anomalías o garajes corruptos')
        act_reparar.triggered.connect(self._action_comprobar_y_reparar_partida)

        menu.addSeparator()

        act_eliminar = menu.addAction(tr('Eliminar Perfil'))
        act_eliminar.setToolTip(
            'Elimina permanentemente la carpeta del perfil')
        act_eliminar.triggered.connect(self._action_eliminar_perfil)

        self.btn_opciones.setMenu(menu)

    def _iniciar_animacion_carga(self, texto: str = 'Cargando perfiles...', bloquear_refrescar: bool = False):
        """Muestra el indicador animado no bloqueante en la barra superior."""
        if bloquear_refrescar:
            self.btn_refrescar.setEnabled(False)
        if hasattr(self, '_timer_ocultar_estado') and self._timer_ocultar_estado and self._timer_ocultar_estado.isActive():
            self._timer_ocultar_estado.stop()
        self._estado_async_activo = True
        self._texto_estado_async = texto or tr('Procesando...')
        if hasattr(self, 'lbl_estado_async') and self.lbl_estado_async:
            self.lbl_estado_async.setStyleSheet(
                'background: rgba(59, 130, 246, 0.14); color: #60A5FA; '
                'border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 6px; '
                'padding: 0 10px; font-size: 11px; font-weight: 700;'
            )
            self.lbl_estado_async.setText(f'⠋ {self._texto_estado_async}')
            self.lbl_estado_async.show()
        if not hasattr(self, '_timer_anim_carga') or self._timer_anim_carga is None:
            self._timer_anim_carga = QTimer(self)
            self._timer_anim_carga.setInterval(90)
            self._anim_frame = 0
            frames = ('⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏')

            def _tick():
                self._anim_frame = (getattr(self, '_anim_frame', 0) + 1) % len(frames)
                if hasattr(self, 'lbl_estado_async') and self.lbl_estado_async and self._estado_async_activo:
                    self.lbl_estado_async.setText(f'{frames[self._anim_frame]} {self._texto_estado_async}')

            self._timer_anim_carga.timeout.connect(_tick)
        if not self._timer_anim_carga.isActive():
            self._anim_frame = 0
            self._timer_anim_carga.start()

    def _detener_animacion_carga(self, mostrar_guardado: bool = False):
        """Detiene el spinner cuando no quedan operaciones pendientes y opcionalmente confirma guardado."""
        self.btn_refrescar.setEnabled(True)
        with self._cond_escrituras:
            quedan_escrituras = bool(self._cola_escrituras) or self._escritura_en_vuelo is not None
        if quedan_escrituras:
            self._texto_estado_async = tr('Guardando...')
            return
        self._estado_async_activo = False
        if hasattr(self, '_timer_anim_carga') and self._timer_anim_carga and self._timer_anim_carga.isActive():
            self._timer_anim_carga.stop()
        if hasattr(self, 'lbl_estado_async') and self.lbl_estado_async:
            if mostrar_guardado:
                self.lbl_estado_async.setStyleSheet(
                    'background: rgba(34, 197, 94, 0.14); color: #4ADE80; '
                    'border: 1px solid rgba(34, 197, 94, 0.35); border-radius: 6px; '
                    'padding: 0 10px; font-size: 11px; font-weight: 700;'
                )
                self.lbl_estado_async.setText(tr('✓ Guardado'))
                self.lbl_estado_async.show()
                if self._timer_ocultar_estado is None:
                    self._timer_ocultar_estado = QTimer(self)
                    self._timer_ocultar_estado.setSingleShot(True)
                    self._timer_ocultar_estado.timeout.connect(
                        lambda: self.lbl_estado_async.hide() if not self._estado_async_activo else None
                    )
                self._timer_ocultar_estado.start(1600)
            else:
                self.lbl_estado_async.hide()

    def _juego_cerrado_o_alertar(self) -> bool:
        """Verifica en <20 ms si ATS está abierto antes de aplicar cambios optimistas."""
        juego_ok, msg_juego = profile_manager.verificar_juego_cerrado()
        if not juego_ok:
            QMessageBox.warning(self, 'Atención', msg_juego)
            return False
        return True

    def _manejar_error_edicion_ligera(self, exito: bool, msg: str, ruta_g: str):
        if exito:
            return
        if ruta_g == self._obtener_ruta_guardado_actual():
            self._on_guardado_seleccionado()
        QMessageBox.warning(self, 'Atención', msg)

    def _iniciar_trabajador_escrituras(self):
        if self._trabajador_escrituras_iniciado:
            return
        self._trabajador_escrituras_iniciado = True

        def _worker():
            while True:
                with self._cond_escrituras:
                    while not self._cola_escrituras:
                        self._cond_escrituras.wait()
                    _, ruta_g, desc, fn_write, boton, texto_exito, on_result, reconciliar = self._cola_escrituras.pop(0)
                    self._escritura_en_vuelo = ruta_g

                exito, msg, nuevos_datos = False, '', {}
                try:
                    res = fn_write()
                    if isinstance(res, tuple) and len(res) == 3:
                        exito, msg, nuevos_datos = res
                    else:
                        exito, msg = res
                except Exception as e:
                    exito, msg = False, str(e)

                if reconciliar and exito and not nuevos_datos and ruta_g:
                    with self._cond_escrituras:
                        mas_antes = bool(self._cola_escrituras)
                    if not mas_antes:
                        try:
                            nuevos_datos = profile_manager.leer_datos_partida(ruta_g, sanear=False)
                        except Exception:
                            nuevos_datos = {}

                with self._cond_escrituras:
                    self._escritura_en_vuelo = None
                    quedan_mas = bool(self._cola_escrituras)
                    self._cond_escrituras.notify_all()

                if nuevos_datos and not quedan_mas:
                    cb_orig = on_result

                    def _on_con_datos(ok_res, msg_res, d_rec=nuevos_datos, r_g=ruta_g, cb=cb_orig):
                        if ok_res and d_rec and r_g == self._obtener_ruta_guardado_actual():
                            with self._cond_escrituras:
                                aun_vacio = not self._cola_escrituras and self._escritura_en_vuelo is None
                            if aun_vacio:
                                self._aplicar_reconciliacion_silenciosa(d_rec)
                        if callable(cb):
                            cb(ok_res, msg_res)

                    cb_final = _on_con_datos
                else:
                    cb_final = on_result

                try:
                    self.señales.edicion_ligera_terminada.emit(
                        exito, msg, ruta_g, boton, texto_exito, cb_final, quedan_mas
                    )
                except RuntimeError:
                    return

        threading.Thread(target=_worker, daemon=True).start()

    def _aplicar_reconciliacion_silenciosa(self, datos: dict):
        """Actualiza datos en memoria y refresca la pestaña activa al vaciarse la cola FIFO."""
        self.datos_partida_actual = datos
        sk = datos.get('skills', {})
        if not getattr(self, '_skills_dirty', False):
            self.skills_editadas = {
                k: sk.get(k, 0) for k in ('adr', 'long_dist', 'heavy', 'fragile', 'urgent', 'mechanical')
            }
            self._skills_guardadas = dict(self.skills_editadas)
        self._tabs_sucias = set(range(8))
        idx_actual = self.tabs.currentIndex()
        self.setUpdatesEnabled(False)
        try:
            self._refrescar_tab_por_indice(idx_actual, datos)
        finally:
            self.setUpdatesEnabled(True)

    def _marcar_otras_tabs_sucias(self):
        idx_act = self.tabs.currentIndex()
        self._tabs_sucias.update(i for i in range(8) if i != idx_act)

    def _esperar_escrituras_pendientes(self, ruta_g: str | None = None, timeout_max: float | None = None):
        limite = time.monotonic() + timeout_max if timeout_max is not None else None
        with self._cond_escrituras:
            while True:
                en_vuelo = self._escritura_en_vuelo
                en_cola = any(ruta_g is None or item[1] == ruta_g for item in self._cola_escrituras)
                activo = en_vuelo is not None and (ruta_g is None or en_vuelo == ruta_g)
                if not en_cola and not activo:
                    return True
                if limite is not None:
                    restante = limite - time.monotonic()
                    if restante <= 0:
                        return False
                    self._cond_escrituras.wait(timeout=min(0.1, restante))
                else:
                    self._cond_escrituras.wait(timeout=0.1)

    def hay_operaciones_pendientes(self) -> bool:
        """Indica si existe alguna escritura, acción sobre partida/perfil o saneamiento activo."""
        if (
            getattr(self, '_skills_dirty', False)
            or self._operacion_en_curso
            or getattr(self, '_operacion_perfil_en_curso', False)
            or getattr(self, '_reparacion_en_curso', False)
        ):
            return True
        if self._lock_saneamiento.locked():
            return True
        with self._cond_escrituras:
            return bool(self._cola_escrituras) or self._escritura_en_vuelo is not None

    def esperar_operaciones_pendientes(self, timeout_max: float = 30.0) -> bool:
        """Espera desde un hilo secundario a que concluyan todas las escrituras y procesos en curso."""
        deadline = time.monotonic() + max(0.5, float(timeout_max))
        while True:
            restante = deadline - time.monotonic()
            if restante <= 0:
                return False
            self._esperar_escrituras_pendientes(None, timeout_max=restante)
            if not (
                self._operacion_en_curso
                or getattr(self, '_operacion_perfil_en_curso', False)
                or getattr(self, '_reparacion_en_curso', False)
                or self._lock_saneamiento.locked()
            ):
                with self._cond_escrituras:
                    if not self._cola_escrituras and self._escritura_en_vuelo is None:
                        return True
            time.sleep(0.05)

    def _encolar_edicion_ligera_async(
        self,
        clave_coalesce: str,
        ruta_g: str,
        desc: str,
        fn_write,
        boton=None,
        texto_exito: str = '¡Guardado!',
        on_result=None,
        reconciliar: bool = False,
    ):
        """Encola escrituras en orden FIFO fusionando ráfagas sobre la misma clave."""
        with self._cond_escrituras:
            self._iniciar_trabajador_escrituras()
            reemplazado = False
            for i, item in enumerate(self._cola_escrituras):
                if item[0] == clave_coalesce and item[1] == ruta_g:
                    self._cola_escrituras[i] = (
                        clave_coalesce, ruta_g, desc, fn_write, boton, texto_exito, on_result, reconciliar
                    )
                    reemplazado = True
                    break
            if not reemplazado:
                self._cola_escrituras.append(
                    (clave_coalesce, ruta_g, desc, fn_write, boton, texto_exito, on_result, reconciliar)
                )
            self._cond_escrituras.notify_all()
        self._iniciar_animacion_carga(desc)

    def _on_edicion_ligera_terminada(self, exito: bool, msg: str, ruta_g: str, boton, texto_exito: str,
                                     on_result, quedan_mas: bool):
        if boton is not None:
            try:
                if exito:
                    notificar_exito_boton(boton, texto_exito)
                else:
                    boton.setEnabled(True)
            except RuntimeError:
                pass
        if callable(on_result):
            on_result(exito, msg)
        if not quedan_mas:
            self._detener_animacion_carga(mostrar_guardado=exito)

    def cargar_perfiles_async(self, perfil_a_seleccionar: str = None, ejecutar_saneamiento: bool = True):
        if not isinstance(perfil_a_seleccionar, str):
            perfil_a_seleccionar = None
        self._iniciar_animacion_carga(tr('Cargando perfiles...'), bloquear_refrescar=True)

        def hilo():
            p_lista = profile_manager.listar_perfiles_ats()
            try:
                self.señales.lista_perfiles_lista.emit((p_lista, perfil_a_seleccionar))
            except RuntimeError:
                return

            if not ejecutar_saneamiento:
                return
            threading.Event().wait(1.2)
            if not self._lock_saneamiento.acquire(blocking=False):
                return
            try:
                profile_manager.saneamiento_pasivo_perfiles_locales_ats()
            except Exception as e:
                print(f'[WARN] Error en saneamiento pasivo de perfiles: {e}')
            finally:
                self._lock_saneamiento.release()

        threading.Thread(target=hilo, daemon=True).start()

    def _mostrar_info_tipo_perfil(self, tipo: str):
        dlg = DialogoInfoTipoPerfil(tipo, parent=self)
        dlg.exec()

    def _on_perfiles_cargados(self, datos_hilo):
        lista, perfil_a_seleccionar = datos_hilo
        self.perfiles = lista
        self.btn_refrescar.setEnabled(True)

        self.combo_perfiles.blockSignals(True)
        self.combo_perfiles.clear()

        # Separar perfiles locales y de Steam Cloud
        locales = sorted([p for p in self.perfiles if not p.get('es_steam_cloud')], key=lambda x: x['nombre'].lower())
        steam = sorted([p for p in self.perfiles if p.get('es_steam_cloud')], key=lambda x: x['nombre'].lower())

        target_index = -1
        first_local_index = -1
        model = self.combo_perfiles.model()

        # Perfiles locales
        if locales:
            idx_hdr_loc = self.combo_perfiles.count()
            self.combo_perfiles.addItem(tr('PERFILES LOCALES'))
            if hasattr(model, 'item'):
                it = model.item(idx_hdr_loc)
                if it:
                    it.setData(True, Qt.UserRole + 10)
                    it.setData('locales', Qt.UserRole + 11)
                    it.setEnabled(False)

            for p in locales:
                curr_idx = self.combo_perfiles.count()
                if first_local_index == -1:
                    first_local_index = curr_idx
                self.combo_perfiles.addItem(p['nombre'], p)
                if perfil_a_seleccionar and p['nombre'] == perfil_a_seleccionar:
                    target_index = curr_idx

        # Perfiles de Steam Cloud (bloqueados)
        if steam:
            idx_hdr_steam = self.combo_perfiles.count()
            self.combo_perfiles.addItem(tr('PERFILES DE STEAM CLOUD'))
            if hasattr(model, 'item'):
                it = model.item(idx_hdr_steam)
                if it:
                    it.setData(True, Qt.UserRole + 10)
                    it.setData('steam', Qt.UserRole + 11)
                    it.setEnabled(False)

            for p in steam:
                curr_idx = self.combo_perfiles.count()
                self.combo_perfiles.addItem(p['nombre'], p)
                if hasattr(model, 'item'):
                    item = model.item(curr_idx)
                    if item:
                        item.setEnabled(False)
                        item.setForeground(QColor('#64748B'))
                        font = item.font()
                        font.setItalic(True)
                        item.setFont(font)
                        item.setToolTip(tr("⚠️ Perfil bloqueado por Steam Cloud.\nPara editarlo: en el juego desmarca 'Sincronización con Steam Cloud' en Editar trayectoria."))

        # Selección por defecto: el primer perfil local
        if target_index == -1:
            target_index = first_local_index if first_local_index != -1 else 0

        self.combo_perfiles.setCurrentIndex(target_index)
        self.combo_perfiles.blockSignals(False)

        self._on_perfil_seleccionado()

    def _on_perfil_seleccionado(self, *args):
        if getattr(self, '_skills_dirty', False):
            self._guardar_skills_inmediato()

        if args and isinstance(args[0], int) and args[0] >= 0:
            perfil_sel = self.combo_perfiles.itemData(args[0])
        else:
            perfil_sel = self.combo_perfiles.currentData()

        if not (perfil_sel and isinstance(perfil_sel, dict) and 'ruta' in perfil_sel):
            for i in range(self.combo_perfiles.count()):
                d = self.combo_perfiles.itemData(i)
                if isinstance(d, dict) and 'ruta' in d and not d.get('es_steam_cloud'):
                    self.combo_perfiles.blockSignals(True)
                    self.combo_perfiles.setCurrentIndex(i)
                    self.combo_perfiles.blockSignals(False)
                    perfil_sel = d
                    break

        if not (perfil_sel and isinstance(perfil_sel, dict) and 'ruta' in perfil_sel):
            self._detener_animacion_carga()
            return

        self._req_id_perfil += 1
        req_p = self._req_id_perfil
        self._req_id_partida += 1
        ruta_perfil = perfil_sel['ruta']
        self._iniciar_animacion_carga(tr('Cargando partidas...'))

        def hilo_guardados():
            gs = profile_manager.listar_guardados_de_perfil(ruta_perfil)
            try:
                self.señales.guardados_cargados.emit(req_p, ruta_perfil, gs)
            except RuntimeError:
                return

        threading.Thread(target=hilo_guardados, daemon=True).start()

    def _on_guardados_cargados(self, req_p: int, ruta_perfil: str, guardados: list):
        if req_p != self._req_id_perfil:
            return
        self.guardados = guardados

        self.combo_guardados.blockSignals(True)
        self.combo_guardados.clear()
        for g in self.guardados:
            self.combo_guardados.addItem(self._formatear_nombre_guardado(g), g)
        if self.guardados:
            self.combo_guardados.setCurrentIndex(0)
        self.combo_guardados.blockSignals(False)

        if self.guardados:
            self._on_guardado_seleccionado()
        else:
            self._detener_animacion_carga()

    def _on_guardado_seleccionado(self, *args):
        if getattr(self, '_skills_dirty', False):
            self._guardar_skills_inmediato()

        if args and isinstance(args[0], int) and args[0] >= 0:
            idx_g = args[0]
        else:
            idx_g = self.combo_guardados.currentIndex()

        if idx_g < 0 or idx_g >= len(self.guardados):
            self._detener_animacion_carga()
            return

        self._req_id_partida += 1
        req_g = self._req_id_partida
        ruta_g = self.guardados[idx_g]['ruta']
        self._iniciar_animacion_carga(tr('Leyendo partida...'))

        def hilo_leer():
            self._esperar_escrituras_pendientes(ruta_g)
            datos = profile_manager.leer_datos_partida(ruta_g)
            try:
                self.señales.datos_cargados_req.emit(req_g, datos)
            except RuntimeError:
                return

        threading.Thread(target=hilo_leer, daemon=True).start()

    def _on_datos_partida_cargados_req(self, req_g: int, datos: dict):
        if req_g != self._req_id_partida:
            return
        self._on_datos_partida_cargados(datos)

    def _obtener_ruta_guardado_actual(self) -> str | None:
        idx_g = self.combo_guardados.currentIndex()
        if 0 <= idx_g < len(self.guardados):
            return self.guardados[idx_g]['ruta']
        return None

    def _refrescar_tab_por_indice(self, idx: int, datos: dict):
        metodos_tab = (
            '_refrescar_economia',
            '_refrescar_habilidades',
            '_refrescar_garajes',
            '_refrescar_conductores',
            '_refrescar_camiones_flota',
            '_refrescar_empresa',
            '_refrescar_taller',
            '_refrescar_estabilidad',
        )
        if 0 <= idx < len(metodos_tab):
            getattr(self, metodos_tab[idx])(datos)
            self._tabs_sucias.discard(idx)

    def _on_tab_cambiada(self, idx: int):
        """Sincroniza perezosamente la pestaña activa solo si tiene datos pendientes."""
        if getattr(self, '_skills_dirty', False):
            self._guardar_skills_inmediato()

        if self.datos_partida_actual and idx in self._tabs_sucias:
            self.setUpdatesEnabled(False)
            try:
                self._refrescar_tab_por_indice(idx, self.datos_partida_actual)
            finally:
                self.setUpdatesEnabled(True)

    def _ejecutar_accion_partida_async(self, fn_accion, boton=None, texto_exito: str = '¡Actualizado!'):
        """Ejecuta una modificación del archivo game.sii y la recarga de datos en un hilo en segundo plano
        para que la interfaz nunca se congele."""
        if self._operacion_en_curso:
            return
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        self._operacion_en_curso = True
        self._iniciar_animacion_carga(tr('Procesando...'))
        if boton is not None:
            boton.setEnabled(False)

        def _hilo():
            self._esperar_escrituras_pendientes(ruta_g)
            exito, msg = fn_accion()
            nuevos_datos = {}
            if exito and ruta_g:
                nuevos_datos = profile_manager.leer_datos_partida(ruta_g, sanear=False)
            try:
                self.señales.accion_partida_terminada.emit(exito, msg, nuevos_datos, boton, texto_exito)
            except RuntimeError:
                return

        threading.Thread(target=_hilo, daemon=True).start()

    def _on_accion_partida_terminada(self, exito: bool, msg: str, nuevos_datos: dict, boton, texto_exito: str):
        self._operacion_en_curso = False
        self._operacion_perfil_en_curso = False
        self._reparacion_en_curso = False
        self._secuencia_cola = 0
        if exito:
            if nuevos_datos:
                self._on_datos_partida_cargados(nuevos_datos)
            else:
                self._detener_animacion_carga()
            if boton is not None:
                notificar_exito_boton(boton, texto_exito)
        else:
            self._detener_animacion_carga()
            if boton is not None:
                boton.setEnabled(True)
            QMessageBox.warning(self, 'Atención', msg)

    def _on_datos_partida_cargados(self, datos: dict):
        self._detener_animacion_carga()
        self.datos_partida_actual = datos
        sk = datos.get('skills', {})
        self.skills_editadas = {
            k: sk.get(k, 0) for k in ('adr', 'long_dist', 'heavy', 'fragile', 'urgent', 'mechanical')
        }
        self._skills_guardadas = dict(self.skills_editadas)
        self._skills_dirty = False
        self._tabs_sucias = set(range(8))
        self.setUpdatesEnabled(False)
        try:
            self._refrescar_tab_por_indice(self.tabs.currentIndex(), datos)
        finally:
            self.setUpdatesEnabled(True)

    def _lanzar_operacion_perfil_async(self, tipo_op: str, desc_carga: str, fn_op, nombre_objetivo: str = ''):
        self._operacion_perfil_en_curso = True
        self.btn_opciones.setEnabled(False)
        self._iniciar_animacion_carga(desc_carga, bloquear_refrescar=True)

        def _hilo():
            exito, msg = fn_op()
            try:
                self.señales.operacion_perfil_terminada.emit(exito, msg, tipo_op, nombre_objetivo)
            except RuntimeError:
                self._operacion_perfil_en_curso = False
                return

        threading.Thread(target=_hilo, daemon=True).start()

    def _on_operacion_perfil_terminada(self, exito: bool, msg: str, tipo_op: str, nombre_objetivo: str):
        self._operacion_perfil_en_curso = False
        self.btn_opciones.setEnabled(True)
        self._detener_animacion_carga()
        if exito:
            if tipo_op == 'eliminar':
                QMessageBox.information(self, 'Éxito', msg)
                self.cargar_perfiles_async(ejecutar_saneamiento=False)
            else:
                self.cargar_perfiles_async(perfil_a_seleccionar=nombre_objetivo, ejecutar_saneamiento=False)
        elif tipo_op == 'eliminar':
            QMessageBox.critical(self, 'Error', msg)
        else:
            QMessageBox.warning(self, 'Atención', msg)

    def _action_clonar_perfil(self):
        perfil_sel = self.combo_perfiles.currentData()
        if perfil_sel and isinstance(perfil_sel, dict) and 'ruta' in perfil_sel:
            nuevo_nombre, ok = QInputDialog.getText(
                self, 'Clonar Perfil', 'Nuevo nombre para el perfil duplicado:', text=f"{perfil_sel['nombre']} copia"
            )
            if ok and nuevo_nombre:
                nombre_obj = nuevo_nombre.strip()
                self._lanzar_operacion_perfil_async(
                    'clonar',
                    tr('Clonando perfil...'),
                    lambda r=perfil_sel['ruta'], n=nuevo_nombre: profile_manager.clonar_perfil_ats(r, n),
                    nombre_obj,
                )

    def _action_renombrar_perfil(self):
        perfil_sel = self.combo_perfiles.currentData()
        if perfil_sel and isinstance(perfil_sel, dict) and 'ruta' in perfil_sel:
            nuevo_nombre, ok = QInputDialog.getText(
                self, 'Renombrar Perfil', 'Nuevo nombre para el perfil:', text=perfil_sel['nombre']
            )
            if ok and nuevo_nombre:
                nombre_obj = nuevo_nombre.strip()
                self._lanzar_operacion_perfil_async(
                    'renombrar',
                    tr('Renombrando perfil...'),
                    lambda r=perfil_sel['ruta'], n=nuevo_nombre: profile_manager.renombrar_perfil_ats(r, n),
                    nombre_obj,
                )

    def _action_eliminar_perfil(self):
        perfil_sel = self.combo_perfiles.currentData()
        if perfil_sel and isinstance(perfil_sel, dict) and 'ruta' in perfil_sel:
            res = QMessageBox.question(
                self,
                'Confirmar Eliminación',
                f"¿Estás seguro de que deseas eliminar permanentemente el perfil '{perfil_sel['nombre']}'?\nEsta acción borra todas sus partidas guardadas.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if res == QMessageBox.Yes:
                self._lanzar_operacion_perfil_async(
                    'eliminar',
                    tr('Eliminando perfil...'),
                    lambda r=perfil_sel['ruta']: profile_manager.eliminar_perfil_ats(r),
                )

    def _action_comprobar_y_reparar_partida(self):
        ruta_g = self._obtener_ruta_guardado_actual()
        if not ruta_g:
            return
        self._reparacion_en_curso = True
        self.btn_opciones.setEnabled(False)
        self._iniciar_animacion_carga(tr('Verificando...'), bloquear_refrescar=True)

        def hilo():
            self._esperar_escrituras_pendientes(ruta_g)
            exito, reps, msg = profile_manager.comprobar_y_reparar_partida_ats(ruta_g)
            try:
                self.señales.reparacion_terminada.emit(exito, reps, msg)
            except RuntimeError:
                self._reparacion_en_curso = False
                return

        threading.Thread(target=hilo, daemon=True).start()

    def _on_reparacion_terminada(self, exito: bool, reps: list, msg: str):
        self._reparacion_en_curso = False
        self.btn_opciones.setEnabled(True)
        self._detener_animacion_carga()
        if not exito:
            QMessageBox.warning(self, 'Atención', msg)
            return
        if reps:
            lista_txt = '\n• ' + '\n• '.join(reps)
            QMessageBox.information(
                self,
                'Partida Reparada con Éxito',
                f'Se inspeccionó la partida guardada y se corrigieron las siguientes anomalías:\n{lista_txt}\n\nTu partida ahora se encuentra en un estado totalmente limpio y seguro.',
            )
            self._on_guardado_seleccionado()
        else:
            QMessageBox.information(
                self,
                'Partida en Buen Estado',
                'Tu partida guardada ha sido inspeccionada minuciosamente. No se detectaron anomalías ni errores estructurales.',
            )

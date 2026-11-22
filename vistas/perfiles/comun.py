from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QPushButton, QComboBox, QFrame, QTabWidget,
                               QMessageBox as _QMessageBox_Original, QSpinBox, QDialog,
                               QMenu, QInputDialog, QProgressBar, QScrollArea, QLineEdit, QToolTip)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEvent, QRect
from i18n import tr


class MensajeSilencioso:
    """Reemplazo directo de QMessageBox para mostrar dialogos completamente limpios y sin el molesto pitido de Windows."""
    Yes = _QMessageBox_Original.StandardButton.Yes
    No = _QMessageBox_Original.StandardButton.No
    Ok = _QMessageBox_Original.StandardButton.Ok
    Cancel = _QMessageBox_Original.StandardButton.Cancel
    StandardButton = _QMessageBox_Original.StandardButton
    Icon = _QMessageBox_Original.Icon

    def __new__(cls, *args, **kwargs):
        dlg = _QMessageBox_Original(*args, **kwargs)
        dlg.setIcon(_QMessageBox_Original.Icon.NoIcon)
        return dlg

    @classmethod
    def _mostrar_limpio(cls, parent, title, text, buttons, defaultButton):
        box = _QMessageBox_Original(parent)
        box.setIcon(_QMessageBox_Original.Icon.NoIcon)
        box.setWindowTitle(tr(title))
        box.setText(tr(text))
        box.setStandardButtons(buttons)
        box.setDefaultButton(defaultButton)
        btn_def = box.button(defaultButton)
        if btn_def is not None:
            btn_def.setAutoDefault(True)
            btn_def.setDefault(True)
            btn_def.setFocus()
        return box.exec()

    @classmethod
    def question(cls, parent, title, text,
                 buttons=_QMessageBox_Original.StandardButton.Yes | _QMessageBox_Original.StandardButton.No,
                 defaultButton=_QMessageBox_Original.StandardButton.Yes):
        return cls._mostrar_limpio(parent, title, text, buttons, defaultButton)

    @classmethod
    def warning(cls, parent, title, text, buttons=_QMessageBox_Original.StandardButton.Ok,
                defaultButton=_QMessageBox_Original.StandardButton.Ok):
        return cls._mostrar_limpio(parent, title, text, buttons, defaultButton)

    @classmethod
    def information(cls, parent, title, text, buttons=_QMessageBox_Original.StandardButton.Ok,
                    defaultButton=_QMessageBox_Original.StandardButton.Ok):
        return cls._mostrar_limpio(parent, title, text, buttons, defaultButton)

    @classmethod
    def critical(cls, parent, title, text, buttons=_QMessageBox_Original.StandardButton.Ok,
                 defaultButton=_QMessageBox_Original.StandardButton.Ok):
        return cls._mostrar_limpio(parent, title, text, buttons, defaultButton)


QMessageBox = MensajeSilencioso


# Paleta sobria compartida por todas las pestañas del editor de perfiles
TXT_PRINCIPAL = "#F1F5F9"
TXT_SECUNDARIO = "#94A3B8"
TXT_APAGADO = "#64748B"

VERDE_TXT = "#6EE7B7"
VERDE_BORDE = "#059669"
VERDE_FONDO = "#13221E"
VERDE_HOVER = "#1A332C"

AZUL_TXT = "#93C5FD"
AZUL_BORDE = "#2563EB"
AZUL_FONDO = "#152033"
AZUL_HOVER = "#1E314D"

AMBAR_TXT = "#FCD34D"
AMBAR_BORDE = "#B45309"
AMBAR_FONDO = "#221C14"
AMBAR_HOVER = "#33281A"

ROJO_TXT = "#FCA5A5"
ROJO_BORDE = "#B91C1C"
ROJO_FONDO = "#24161A"
ROJO_HOVER = "#381F25"

NEUTRO_TXT = "#CBD5E1"
NEUTRO_BORDE = "#334155"
NEUTRO_FONDO = "#161B22"
NEUTRO_HOVER = "#1E2633"

DESHAB_TXT = "#475569"
DESHAB_BORDE = "#1E242E"
DESHAB_FONDO = "#13171E"

CSS_TARJETA = ("QFrame#card { background: #181A20; border: 1px solid #262932; border-radius: 8px; } "
               "QFrame#card QLabel { background: transparent; border: none; }")

CSS_PROGRESO = f"""
    QProgressBar {{ background: #0F172A; border-radius: 4px; text-align: center; color: transparent; border: 1px solid #1E293B; }}
    QProgressBar::chunk {{ background: {VERDE_BORDE}; border-radius: 3px; }}
"""


def estilo_boton(variante: str = "neutro", compacto: bool = False) -> str:
    """Genera el estilo sobrio unificado (fondo oscuro + borde y texto de color suave)."""
    pad = "0 10px" if compacto else "0 14px"
    fsize = "11px" if compacto else "12px"
    radius = "5px" if compacto else "6px"

    paletas = {
        "verde": (VERDE_FONDO, VERDE_TXT, VERDE_BORDE, VERDE_HOVER, "#A7F3D0", "#10B981"),
        "azul": (AZUL_FONDO, AZUL_TXT, AZUL_BORDE, AZUL_HOVER, "#BFDBFE", "#3B82F6"),
        "ambar": (AMBAR_FONDO, AMBAR_TXT, AMBAR_BORDE, AMBAR_HOVER, "#FDE68A", "#D97706"),
        "rojo": (ROJO_FONDO, ROJO_TXT, ROJO_BORDE, ROJO_HOVER, "#FECACA", "#EF4444"),
        "neutro": (NEUTRO_FONDO, NEUTRO_TXT, NEUTRO_BORDE, NEUTRO_HOVER, TXT_PRINCIPAL, "#475569"),
    }

    if variante in ("actual", "deshabilitado", "vender_off"):
        pad_d = "0 4px" if compacto else pad
        return f"""
            QPushButton {{
                background: {DESHAB_FONDO}; color: {DESHAB_TXT};
                border: 1px solid {DESHAB_BORDE}; border-radius: {radius};
                font-size: {fsize}; font-weight: 700; padding: {pad_d};
            }}
        """

    bg, fg, bd, bg_h, fg_h, bd_h = paletas.get(variante, paletas["neutro"])
    return f"""
        QPushButton {{
            background: {bg}; color: {fg};
            border: 1px solid {bd}; border-radius: {radius};
            font-size: {fsize}; font-weight: 800; padding: {pad};
        }}
        QPushButton:hover {{
            background: {bg_h}; color: {fg_h}; border: 1px solid {bd_h};
        }}
        QPushButton:disabled {{
            background: {DESHAB_FONDO}; color: {DESHAB_TXT}; border: 1px solid {DESHAB_BORDE};
        }}
    """


def notificar_exito_boton(boton: QPushButton, texto_exito: str = "¡Actualizado!", ms: int = 500):
    duracion = boton.property("ms_exito") or ms
    texto_original = boton.property("texto_base") or boton.text()
    boton.setProperty("texto_base", texto_original)
    boton.setText(texto_exito)
    boton.setEnabled(False)

    def restaurar():
        try:
            boton.setText(texto_original)
            if not boton.property("bloqueado_por_estado"):
                boton.setEnabled(True)
        except RuntimeError:
            pass

    QTimer.singleShot(duracion, restaurar)


class SeñalesPerfilUI(QObject):
    datos_cargados = Signal(dict)
    datos_cargados_req = Signal(int, dict)
    guardados_cargados = Signal(int, str, list)
    lista_perfiles_lista = Signal(tuple)
    clonacion_terminada = Signal(bool, str, str)
    operacion_perfil_terminada = Signal(bool, str, str, str)
    accion_partida_terminada = Signal(bool, str, dict, object, str)
    edicion_ligera_terminada = Signal(bool, str, str, object, str, object, bool)
    reparacion_terminada = Signal(bool, list, str)


class EstilosMixin:
    """Estilos y utilidades de UI compartidas por todas las pestañas."""

    def _estilo_btn(self, variante: str = "neutro", compacto: bool = False) -> str:
        return estilo_boton(variante, compacto=compacto)

    def _estilo_combo(self):
        return f"""
            QComboBox {{
                background: #161B22; color: {TXT_PRINCIPAL}; font-size: 12px; font-weight: 700;
                border: 1px solid {NEUTRO_BORDE}; border-radius: 6px; padding-left: 8px;
            }}
            QComboBox:hover {{
                border-color: #475569;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: #161B22; color: {TXT_PRINCIPAL}; selection-background-color: #263040;
                border: 1px solid {NEUTRO_BORDE}; outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px; padding-left: 6px;
            }}
            QToolTip {{
                background-color: #1F1607;
                color: #FDE047;
                border: 1px solid #EAB308;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """

    def _configurar_combo_un_clic(self, combo: QComboBox, callback=None):
        def _al_presionar_item(model_index):
            if not model_index.isValid():
                return
            model = combo.model()
            if hasattr(model, "item"):
                item = model.item(model_index.row())
                if item and not item.isEnabled():
                    return
            idx = model_index.row()
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)
            combo.hidePopup()
            if callback:
                callback(idx)

        combo.view().pressed.connect(_al_presionar_item)

        # Muestra el tooltip de cada item al instante (sin el retardo nativo)
        class ToolTipFastFilter(QObject):
            def __init__(self, c_box):
                super().__init__(c_box)
                self.c_box = c_box
                self.ultimo_idx = -1

            def eventFilter(self, obj, event):
                if event.type() == QEvent.MouseMove:
                    idx = self.c_box.view().indexAt(event.pos())
                    if idx.isValid():
                        row = idx.row()
                        if row != self.ultimo_idx:
                            self.ultimo_idx = row
                            model = self.c_box.model()
                            if hasattr(model, "item"):
                                it = model.item(row)
                                tt = it.toolTip() if it else ""
                                if tt:
                                    QToolTip.showText(event.globalPos(), tt, self.c_box.view(),
                                                      QRect(), 3600000)
                                else:
                                    QToolTip.hideText()
                    else:
                        self.ultimo_idx = -1
                        QToolTip.hideText()
                elif event.type() == QEvent.Leave:
                    self.ultimo_idx = -1
                    QToolTip.hideText()
                return super().eventFilter(obj, event)

        combo.view().viewport().installEventFilter(ToolTipFastFilter(combo))

        if callback:
            combo.currentIndexChanged.connect(callback)

    def _estilo_input(self):
        return f"""
            QLineEdit, QSpinBox {{
                background: #12161D; color: {TXT_PRINCIPAL}; font-size: 13px; font-weight: 700;
                border: 1px solid {NEUTRO_BORDE}; border-radius: 6px; padding: 0 10px;
            }}
            QLineEdit:focus, QSpinBox:focus {{
                border: 1px solid {AZUL_BORDE};
            }}
        """

    def _estilo_btn_preset(self, variante: str = "neutro"):
        return estilo_boton(variante, compacto=False)

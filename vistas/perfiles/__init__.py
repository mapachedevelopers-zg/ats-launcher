"""STUB TEMPORAL de vistas.perfiles (editor de perfiles / partidas de ATS).

Este archivo NO es el original. Sustituye provisionalmente al paquete
vistas.perfiles (pagina.py, comun.py, dialogos.py, tab_*.py) hasta que se
reconstruya en la fase 2. Expone solo la interfaz que usan
interfaz/ventana_principal.py y vistas/pagina_mods.py.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PaginaPerfiles(QWidget):
    """Página de perfiles provisional (stub temporal, fase 2)."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        # Atributo consultado por pagina_mods antes de lanzar el juego
        self._skills_dirty = False

        layout = QVBoxLayout(self)
        self.lbl_stub = QLabel("Editor de perfiles — disponible en la fase 2")
        self.lbl_stub.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_stub)

    # --- Llamados desde LauncherUI ---------------------------------------
    def actualizar_textos_idioma(self):
        pass

    def actualizar_estilo_tabs(self):
        pass

    # --- Llamados desde PaginaMods al lanzar el juego -------------------
    def hay_operaciones_pendientes(self):
        return False

    def esperar_operaciones_pendientes(self, timeout_max=30.0):
        return True


__all__ = ["PaginaPerfiles"]

from ui_manager import LauncherUI
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import os
import sys


def _limpiar_restos_actualizacion():
    """Borra ejecutables viejos (*.old) que el instalador renombró durante una actualización."""
    if not getattr(sys, 'frozen', False):
        return None
    try:
        carpeta = os.path.dirname(os.path.abspath(sys.executable))
        for nombre in os.listdir(carpeta):
            if nombre.lower().endswith('.old'):
                try:
                    os.remove(os.path.join(carpeta, nombre))
                except OSError:
                    pass
    except Exception:
        return None


def arrancar_launcher():
    print('Iniciando launcher...')
    _limpiar_restos_actualizacion()

    app = QApplication([])

    # Ruta base: carpeta temporal de PyInstaller o carpeta del script
    if getattr(sys, 'frozen', False):
        ruta_base = sys._MEIPASS
    else:
        ruta_base = os.path.dirname(os.path.abspath(__file__))

    ruta_icono = os.path.join(ruta_base, 'logo.ico')

    # Si no esta en la ruta base, buscar junto al ejecutable
    if not os.path.exists(ruta_icono):
        ruta_icono = os.path.join(os.path.dirname(os.path.abspath(
            sys.executable if getattr(sys, 'frozen', False) else __file__)), 'logo.ico')

    if os.path.exists(ruta_icono):
        app.setWindowIcon(QIcon(ruta_icono))

    ventana = LauncherUI()
    app.processEvents()
    ventana.show()
    app.exec()


if __name__ == '__main__':
    arrancar_launcher()

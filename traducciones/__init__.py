"""Catálogo modular de traducciones del Launcher."""

from .interfaz_principal import TRADUCCIONES_INTERFAZ
from .perfiles_tabs import TRADUCCIONES_PERFILES_TABS
from .vistas_mods_y_extras import TRADUCCIONES_VISTAS
from .perfiles_detalle import TRADUCCIONES_PERFILES_DETALLE
from .mensajes_alertas import TRADUCCIONES_ALERTAS


TRADUCCIONES = {
    **TRADUCCIONES_INTERFAZ,
    **TRADUCCIONES_PERFILES_TABS,
    **TRADUCCIONES_VISTAS,
    **TRADUCCIONES_PERFILES_DETALLE,
    **TRADUCCIONES_ALERTAS,
}


__all__ = ['TRADUCCIONES']

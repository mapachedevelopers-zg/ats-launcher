# Chasis — Launcher de ATS

Repositorio: https://github.com/mapachedevelopers-zg/ats-launcher

Launcher para American Truck Simulator (Python 3.11 + PySide6), basado en el Launcher de Xtrink 2.2.
Logo: `recursos/logo_chasis.png` y `logo.ico`, generados con `python herramientas_dev/generar_logo.py`.
Instala y actualiza mods desde un catálogo en GitHub, gestiona plugins, aplica ajustes al `config.cfg`
y hace copias de seguridad de perfiles.

## Ejecutar

```
pip install -r requirements.txt
python main.py
```

## Configuración (`config_launcher.json`)

| Clave | Para qué sirve |
|---|---|
| `url_launcher_data` | URL del catálogo (`datos/launcher_data.json` de este repo) |
| `recursos` | Imágenes que descarga el launcher (logo, QR, orden, logos de redes). Valor `""` = no descargar |
| `url_emisoras_github` | `live_streams.sii` por defecto para "Emisoras" |
| `donaciones` | `cuenta_breb`, `paypal_url` (vacío = botón desactivado) |
| `redes` | `youtube`, `facebook`, `discord` (vacío = botón desactivado) |

## Catálogo (`datos/launcher_data.json`)

- `launcher_version` / `launcher_download_url`: si la versión es mayor que `VERSION_ACTUAL`
  (`constantes.py`), el launcher descarga ese ejecutable y se actualiza solo.
- `novedades`: texto de la ventana de novedades (una línea por punto).
- `carplay_url`, `reshade_url`, `blinker_url`, `cabin_walk_url`, `emisoras_url`: descargas de plugins/herramientas.
- `mods`: lista de `{id, nombre, version, archivo_scs, md5, url_descarga, imagen_url}`.

## Estructura

- `main.py`: punto de entrada.
- `constantes.py`, `download_manager.py`, `updater.py`, `utils.py`, `i18n.py`: núcleo.
- `interfaz/`: ventana principal, barra de título, modales.
- `vistas/`: páginas (mods, orden, plugins, perfiles, donaciones, herramientas, redes, configuración).
- `temas.py`, `estilos.py`: temas de color y hoja de estilos Qt.
- `traducciones/`: textos en es, en, pt, de, fr, ru, zh.

> Fase 2 pendiente: editor de perfiles (`vistas/perfiles/`, `gestor_perfiles/`).

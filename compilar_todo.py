"""Script para compilar y empaquetar Launcher de Chasis completo:
1. Compila con PyInstaller a dist/Launcher_Chasis
2. Copia config_launcher.json junto al ejecutable
3. Genera el instalador Inno Setup en dist/installer/
4. Genera el archivo comprimido .zip listo para distribuir
"""

import os
import shutil
import subprocess
import sys
import zipfile
from constantes import VERSION_ACTUAL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
APP_DIR = os.path.join(DIST_DIR, "Launcher_Chasis")
INSTALLER_DIR = os.path.join(DIST_DIR, "installer")


def buscar_iscc() -> str:
    rutas = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for r in rutas:
        if os.path.exists(r):
            return r
    try:
        salida = subprocess.check_output(["where", "ISCC.exe"], text=True).strip().splitlines()
        if salida and os.path.exists(salida[0]):
            return salida[0]
    except Exception:
        pass
    raise FileNotFoundError("No se encontró ISCC.exe (Inno Setup 6). Instálalo con 'winget install JRSoftware.InnoSetup'.")


def paso1_pyinstaller():
    print("\n[1/4] Compilando con PyInstaller...")
    spec_path = os.path.join(BASE_DIR, "Launcher_Chasis.spec")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "-y", spec_path]
    subprocess.run(cmd, cwd=BASE_DIR, check=True)
    print(" PyInstaller completado.")


def paso2_copiar_config():
    print("\n[2/4] Copiando config_launcher.json...")
    cfg_origen = os.path.join(BASE_DIR, "config_launcher.json")
    cfg_destino = os.path.join(APP_DIR, "config_launcher.json")
    if os.path.exists(cfg_origen):
        shutil.copy2(cfg_origen, cfg_destino)
        print(f" Copiado a: {cfg_destino}")


def paso3_inno_setup(iscc_path: str):
    print("\n[3/4] Generando instalador con Inno Setup...")
    iss_path = os.path.join(BASE_DIR, "installer.iss")
    subprocess.run([iscc_path, iss_path], cwd=BASE_DIR, check=True)
    
    # Crear copia con nombre Launcher_Chasis.exe y ATS_VIP.exe para Releases de GitHub
    setup_orig = os.path.join(INSTALLER_DIR, f"ATS_VIP_Setup_{VERSION_ACTUAL}.exe")
    setup_release = os.path.join(INSTALLER_DIR, "Launcher_Chasis.exe")
    setup_release_vip = os.path.join(INSTALLER_DIR, "ATS_VIP.exe")
    if os.path.exists(setup_orig):
        shutil.copy2(setup_orig, setup_release)
        shutil.copy2(setup_orig, setup_release_vip)
        print(f" Instalador listo: {setup_orig}")
        print(f" Copia para GitHub Release: {setup_release}")
        print(f" Copia para GitHub Release VIP: {setup_release_vip}")


def paso4_generar_zip():
    print("\n[4/4] Generando archivo comprimido .zip...")
    zip_path = os.path.join(DIST_DIR, f"ATS_VIP_{VERSION_ACTUAL}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(APP_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, APP_DIR)
                zf.write(full_path, rel_path)
    print(f" ZIP generado con éxito: {zip_path} ({os.path.getsize(zip_path):,} bytes)")


if __name__ == "__main__":
    try:
        iscc = buscar_iscc()
        paso1_pyinstaller()
        paso2_copiar_config()
        paso3_inno_setup(iscc)
        paso4_generar_zip()
        print("\n" + "=" * 60)
        print("¡COMPILACIÓN Y EMPAQUETADO COMPLETADOS CON ÉXITO!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] {e}", file=sys.stderr)
        sys.exit(1)

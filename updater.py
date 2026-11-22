import os
import re
import sys
import tempfile
import subprocess
import requests
from constantes import VERSION_ACTUAL


def _parsear_version(v_str: str) -> tuple:
    """Convierte una cadena como '1.8' o '1.10.2' en una tupla numérica (1, 8) para comparación segura."""
    nums = [int(n) for n in re.findall('\\d+', str(v_str))]
    return tuple(nums) if nums else (0,)


def comprobar_actualizacion_launcher(datos_servidor):
    if not datos_servidor:
        return (False, None)

    version_servidor = str(datos_servidor.get('launcher_version', VERSION_ACTUAL))
    url_descarga = datos_servidor.get('launcher_download_url', '')

    if _parsear_version(version_servidor) > _parsear_version(VERSION_ACTUAL) and url_descarga:
        return (True, url_descarga)
    return (False, None)


def _es_instalador_inno_setup(ruta_archivo: str) -> bool:
    """Detecta si el ejecutable descargado es un instalador de Windows creado con Inno Setup.

    OJO: en Inno Setup 6.7 la firma "Inno Setup Setup Data" está a ~740 KB del inicio,
    por eso se leen los primeros 4 MB (antes solo se leían 512 KB y no se detectaba).
    """
    try:
        with open(ruta_archivo, 'rb') as f:
            cabecera = f.read(4194304)
            firmas = (b'Inno Setup', b'Inno.Setup', b'I\x00n\x00n\x00o\x00S\x00e\x00t\x00u\x00p')
            if any(firma in cabecera for firma in firmas):
                return True
    except Exception:
        pass
    return False


def _necesita_elevacion(directorio: str) -> bool:
    """Verifica si escribir en el directorio de destino requiere elevación UAC."""
    try:
        prueba = os.path.join(directorio, '.perm_test_tmp')
        with open(prueba, 'w') as f:
            f.write('1')
        os.remove(prueba)
        return False
    except (PermissionError, OSError):
        return True


def aplicar_actualizacion_y_reiniciar(url_descarga, callback_progreso=None):
    try:
        es_compilado = getattr(sys, 'frozen', False)

        if es_compilado:
            ruta_exe_actual = os.path.abspath(sys.executable)
        else:
            directorio = os.path.dirname(os.path.abspath(__file__))
            ruta_exe_actual = os.path.join(directorio, 'Launcher_Chasis.exe')

        directorio_actual = os.path.dirname(ruta_exe_actual)
        carpeta_temp = tempfile.gettempdir()
        ruta_descarga_temp = os.path.join(carpeta_temp, 'Launcher_Chasis_Update.exe')

        # Descargar el nuevo ejecutable / instalador
        respuesta = requests.get(
            url_descarga,
            headers={'User-Agent': 'Mozilla/5.0'},
            stream=True,
            timeout=15,
        )
        respuesta.raise_for_status()

        peso_total = int(respuesta.headers.get('content-length', 0))
        descargado = 0

        with open(ruta_descarga_temp, 'wb') as f:
            for bloque in respuesta.iter_content(chunk_size=16384):
                if bloque:
                    f.write(bloque)
                    descargado += len(bloque)
                    if peso_total > 0 and callback_progreso:
                        porcentaje = min(99, int(descargado / peso_total * 100))
                        callback_progreso(porcentaje)

        if not es_compilado:
            if callback_progreso:
                callback_progreso(100)
            print(f'[UPDATER] Descargado con éxito en modo desarrollo: {ruta_descarga_temp}')
            return True

        es_instalador = _es_instalador_inno_setup(ruta_descarga_temp)
        tiene_unins = os.path.exists(os.path.join(directorio_actual, 'unins000.exe'))
        requiere_admin = _necesita_elevacion(directorio_actual)

        bat_script = os.path.join(carpeta_temp, 'actualizar_chasis.bat')
        vbs_script = os.path.join(carpeta_temp, 'actualizar_chasis.vbs')

        if es_instalador:
            # Si el launcher se instaló con Inno Setup (existe unins000.exe), se
            # actualiza sobre la misma carpeta de instalación y se relanza al terminar.
            if tiene_unins:
                args_inst = f'/SILENT /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS /NORESTART /DIR="{directorio_actual}"'
                lanzar_post_bat = f'start "" "{ruta_exe_actual}"'
            else:
                args_inst = f'/CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS /DIR="{directorio_actual}"'
                lanzar_post_bat = ''

            if requiere_admin:
                cmd_inst_bat = (
                    f'powershell -NoProfile -ExecutionPolicy Bypass -Command '
                    f'"Start-Process -FilePath \'{ruta_descarga_temp}\' -ArgumentList \'{args_inst}\' -Verb RunAs -Wait"'
                )
            else:
                cmd_inst_bat = f'start "" /wait "{ruta_descarga_temp}" {args_inst}'

            contenido_bat = f'''@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul 2>&1
taskkill /F /IM Launcher_Chasis.exe /T >nul 2>&1
taskkill /F /IM Launcher_Xtrink.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1

:: Ejecutar instalador de actualización
{cmd_inst_bat}

:: Limpiar instalador temporal
del /f /q "{ruta_descarga_temp}" >nul 2>&1

:: Iniciar launcher actualizado automáticamente
{lanzar_post_bat}

:: Eliminar script temporal
del "%~f0" >nul 2>&1
'''
        else:
            contenido_bat = f'''@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul 2>&1
taskkill /F /IM Launcher_Chasis.exe /T >nul 2>&1
taskkill /F /IM Launcher_Xtrink.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul 2>&1

del /f /q "{ruta_exe_actual}" >nul 2>&1
copy /y "{ruta_descarga_temp}" "{ruta_exe_actual}" >nul 2>&1
del /f /q "{ruta_descarga_temp}" >nul 2>&1

start "" "{ruta_exe_actual}"
del "%~f0" >nul 2>&1
'''

        with open(bat_script, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(contenido_bat)

        # También dejamos el .vbs corregido sin errores de sintaxis
        ruta_exe_vbs = ruta_exe_actual.replace('"', '""')
        ruta_temp_vbs = ruta_descarga_temp.replace('"', '""')
        dir_actual_vbs = directorio_actual.replace('"', '""')
        contenido_vbs = f'''Set fso = CreateObject("Scripting.FileSystemObject")
Set oShell = CreateObject("WScript.Shell")
On Error Resume Next
oShell.Run "taskkill.exe /F /IM Launcher_Chasis.exe /T", 0, True
oShell.Run "taskkill.exe /F /IM Launcher_Xtrink.exe /T", 0, True
On Error GoTo 0
WScript.Sleep 1000
On Error Resume Next
oShell.Run """{ruta_temp_vbs}"" /SILENT /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS /NORESTART /DIR=""{dir_actual_vbs}""", 1, True
fso.DeleteFile "{ruta_temp_vbs}", True
If fso.FileExists("{ruta_exe_vbs}") Then
    oShell.Run """{ruta_exe_vbs}""", 1, False
End If
fso.DeleteFile WScript.ScriptFullName
'''
        with open(vbs_script, 'w', encoding='mbcs', errors='ignore') as f:
            f.write(contenido_vbs)

        # Lanzar el proceso de actualización desvinculado e invisible
        subprocess.Popen(
            ['cmd.exe', '/c', bat_script],
            cwd=carpeta_temp,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if callback_progreso:
            callback_progreso(100)

        return True
    except Exception as e:
        print(f'[ERROR UPDATER] Falló la actualización del launcher: {e}')
        return False

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

        vbs_script = os.path.join(carpeta_temp, 'actualizar_chasis.vbs')
        ruta_exe_vbs = ruta_exe_actual.replace('"', '""')
        ruta_temp_vbs = ruta_descarga_temp.replace('"', '""')
        dir_actual_vbs =directorio_actual.replace('"', '""')

        if es_instalador:
            # Si el launcher se instaló con Inno Setup (existe unins000.exe), se
            # actualiza en silencio sobre la misma carpeta y se relanza al terminar.
            # Si no, se muestra el asistente del instalador normalmente.
            if tiene_unins:
                comando_inst = (
                    f'""{ruta_temp_vbs}"" /SILENT /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS /NORESTART /DIR=""'
                    f'{dir_actual_vbs}""'
                )
                lanzar_post = (
                    f'If fso.FileExists("{ruta_exe_vbs}") Then\n    oShell.Run """'
                    f'{ruta_exe_vbs}""", 1, False\nEnd If'
                )
            else:
                comando_inst = f'""{ruta_temp_vbs}"" /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS'
                lanzar_post = ''

            contenido_vbs = f'''Set fso = CreateObject("Scripting.FileSystemObject")
Set oShell = CreateObject("WScript.Shell")

' Asegurar que el launcher se cierre de inmediato y no quede bloqueando archivos
On Error Resume Next
oShell.Run "taskkill.exe /F /IM Launcher_Chasis.exe /T", 0, True
On Error GoTo 0
WScript.Sleep 1000

' Ejecutar el instalador de actualización y esperar a que termine (True)
On Error Resume Next
oShell.Run "{comando_inst}", 1, True
On Error GoTo 0

' Limpiar instalador temporal
If fso.FileExists("{ruta_temp_vbs}") Then
    On Error Resume Next
    fso.DeleteFile "{ruta_temp_vbs}", True
    On Error GoTo 0
End If

' Iniciar el launcher actualizado automáticamente
{lanzar_post}

' Autoborrado del script temporal
On Error Resume Next
fso.DeleteFile WScript.ScriptFullName
'''
        else:
            contenido_vbs = f'''Set fso = CreateObject("Scripting.FileSystemObject")
Set oShell = CreateObject("WScript.Shell")

' Asegurar el cierre del launcher
On Error Resume Next
oShell.Run "taskkill.exe /F /IM Launcher_Chasis.exe /T", 0, True
On Error GoTo 0
WScript.Sleep 1000

Dim intentos
intentos = 0
Do While fso.FileExists("{ruta_exe_vbs}") And intentos < 20
    On Error Resume Next
    fso.DeleteFile "{ruta_exe_vbs}", True
    On Error GoTo 0
    If fso.FileExists("{ruta_exe_vbs}") Then
        WScript.Sleep 500
    End If
    intentos = intentos + 1
Loop

If fso.FileExists("{ruta_temp_vbs}") Then
    On Error Resume Next
    fso.CopyFile "{ruta_temp_vbs}", "{ruta_exe_vbs}", True
    fso.DeleteFile "{ruta_temp_vbs}", True
    On Error GoTo 0
End If

If fso.FileExists("{ruta_exe_vbs}") Then
    oShell.Run """{ruta_exe_vbs}""", 1, False
End If

On Error Resume Next
fso.DeleteFile WScript.ScriptFullName
'''

        with open(vbs_script, 'w', encoding='mbcs', errors='ignore') as f:
            f.write(contenido_vbs)

        subprocess.Popen(
            ['wscript.exe', vbs_script],
            cwd=carpeta_temp,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if callback_progreso:
            callback_progreso(100)

        return True
    except Exception as e:
        print(f'[ERROR UPDATER] Falló la actualización del launcher: {e}')
        return False

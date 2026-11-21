"""Genera el logo de Chasis: recursos/logo_chasis.png (512 px) y logo.ico (16-256 px).

Uso:  python herramientas_dev/generar_logo.py
Diseño: chasis de camión visto desde arriba (largueros, travesaños, 3 ejes con
ruedas dobles) dentro de un anillo dorado sobre fondo azul oscuro.
"""
import os
import sys

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (QGuiApplication, QImage, QPainter, QColor, QPen, QBrush,
                           QRadialGradient, QLinearGradient, QPainterPath, QFont)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORADO = QColor("#E5A93C")
DORADO_CLARO = QColor("#F7D58B")
DORADO_OSCURO = QColor("#9A6B17")
FONDO = QColor("#0F172A")
FONDO_2 = QColor("#1E293B")
LLANTA = QColor("#0B1120")


def dibujar(tam: int) -> QImage:
    img = QImage(tam, tam, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(tam / 512.0, tam / 512.0)  # se dibuja siempre en un lienzo de 512

    # Fondo circular con degradado
    grad = QRadialGradient(QPointF(256, 200), 300)
    grad.setColorAt(0, FONDO_2)
    grad.setColorAt(1, FONDO)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(QRectF(16, 16, 480, 480))

    # Anillo dorado
    anillo = QLinearGradient(0, 16, 0, 496)
    anillo.setColorAt(0, DORADO_CLARO)
    anillo.setColorAt(0.5, DORADO)
    anillo.setColorAt(1, DORADO_OSCURO)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QBrush(anillo), 22))
    p.drawEllipse(QRectF(27, 27, 458, 458))

    metal = QLinearGradient(0, 110, 0, 410)
    metal.setColorAt(0, DORADO_CLARO)
    metal.setColorAt(1, DORADO)

    # El chasis se dibuja un poco más pequeño y más arriba para dejar sitio al texto
    p.save()
    p.translate(256, 222)
    p.scale(0.78, 0.78)
    p.translate(-256, -257)

    # Ruedas (dobles) en 3 ejes: 1 delantero, 2 traseros
    p.setPen(QPen(DORADO, 5))
    p.setBrush(LLANTA)
    for y in (150, 300, 360):
        for x in (150, 334):
            p.drawRoundedRect(QRectF(x, y - 26, 28, 52), 8, 8)

    # Ejes
    p.setPen(Qt.NoPen)
    p.setBrush(DORADO_OSCURO)
    for y in (150, 300, 360):
        p.drawRoundedRect(QRectF(170, y - 6, 172, 12), 5, 5)

    # Largueros (con estrechamiento delantero)
    p.setBrush(QBrush(metal))
    for lado in (-1, 1):
        cam = QPainterPath()
        xi = 256 + lado * 48   # borde interior
        xe = 256 + lado * 78   # borde exterior
        xi_f = 256 + lado * 40
        xe_f = 256 + lado * 66
        cam.moveTo(xi_f, 104)
        cam.lineTo(xe_f, 104)
        cam.lineTo(xe_f, 190)
        cam.lineTo(xe, 225)
        cam.lineTo(xe, 410)
        cam.lineTo(xi, 410)
        cam.lineTo(xi, 225)
        cam.lineTo(xi_f, 190)
        cam.closeSubpath()
        p.drawPath(cam)

    # Travesaños
    for y in (112, 196, 250, 330, 396):
        p.drawRoundedRect(QRectF(204, y - 7, 104, 14), 4, 4)

    # Quinta rueda (enganche)
    p.setBrush(QBrush(metal))
    p.setPen(QPen(FONDO, 6))
    p.drawEllipse(QPointF(256, 330), 34, 34)
    p.setBrush(FONDO)
    p.setPen(Qt.NoPen)
    p.drawPie(QRectF(242, 316, 28, 28), 0, 360 * 16)
    p.drawRect(QRectF(250, 340, 12, 26))
    p.restore()

    # Texto (solo en tamaños grandes)
    if tam >= 128:
        f = QFont("Segoe UI", 34)
        f.setBold(True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 5)
        p.setFont(f)
        p.setPen(DORADO_CLARO)
        p.drawText(QRectF(0, 372, 512, 60), Qt.AlignHCenter | Qt.AlignTop, "CHASIS")

    p.end()
    return img


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    png = os.path.join(RAIZ, "recursos", "logo_chasis.png")
    dibujar(512).save(png)
    print("PNG:", png)

    from PIL import Image
    tmp = []
    for t in (16, 24, 32, 48, 64, 128, 256):
        ruta = os.path.join(RAIZ, f"_tmp_logo_{t}.png")
        dibujar(t).save(ruta)
        tmp.append(ruta)
    # Cada tamaño se dibuja por separado (los pequeños sin texto)
    imagenes = [Image.open(r).convert("RGBA") for r in tmp]
    ico = os.path.join(RAIZ, "logo.ico")
    imagenes[-1].save(ico, format="ICO", sizes=[im.size for im in imagenes],
                      append_images=imagenes[:-1])
    for im in imagenes:
        im.close()
    for r in tmp:
        os.remove(r)
    print("ICO:", ico)


if __name__ == "__main__":
    main()

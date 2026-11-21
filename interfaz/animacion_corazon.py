import math
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def generar_iconos_corazon(fps: int = 30, size: int = 48) -> list[QIcon]:
    """Precalcula fotogramas del corazón animado (giro rápido + latido + pausa)."""
    dur_giro = 0.58
    dur_latido = 1.3
    dur_pausa = 0.9
    dur_total = dur_giro + dur_latido + dur_pausa
    total_frames = int(dur_total * fps)

    iconos = []
    for i in range(total_frames):
        t = i / fps
        rot_deg = 0.0
        scale_x = 1.0
        scale_y = 1.0
        r, g, b = (255, 255, 255)

        if t < dur_giro:
            prog = t / dur_giro
            rot_deg = 1080.0 * (prog ** 1.35)
            factor_vel = math.sin(prog * math.pi)
            scale_x = 1.0 + 0.18 * factor_vel
            scale_y = 1.0 - 0.12 * factor_vel
        elif t < dur_giro + dur_latido:
            t_lat = t - dur_giro
            if t_lat < 0.55:
                factor = math.sin((t_lat / 0.55) * math.pi)
                scale_x = 1.0 + 0.28 * factor
                scale_y = 1.0 + 0.28 * factor
                g = int(255 - 180 * factor)
                b = int(255 - 165 * factor)
            elif t_lat < 1.1:
                factor = math.sin(((t_lat - 0.55) / 0.55) * math.pi)
                scale_x = 1.0 + 0.16 * factor
                scale_y = 1.0 + 0.16 * factor
                g = int(255 - 145 * factor)
                b = int(255 - 135 * factor)

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(size / 2, size / 2)
        painter.rotate(rot_deg)
        painter.scale(scale_x, scale_y)

        path = QPainterPath()
        y_offset = 3.2
        path.moveTo(0, -6 - y_offset)
        path.cubicTo(-2, -14 - y_offset, -16, -14 - y_offset, -16, -2 - y_offset)
        path.cubicTo(-16, 7 - y_offset, -6, 13 - y_offset, 0, 18 - y_offset)
        path.cubicTo(6, 13 - y_offset, 16, 7 - y_offset, 16, -2 - y_offset)
        path.cubicTo(16, -14 - y_offset, 2, -14 - y_offset, 0, -6 - y_offset)

        painter.setBrush(QColor(r, g, b))
        painter.setPen(QPen(QColor(r, g, b, 230), 1.2))
        painter.drawPath(path)
        painter.end()

        iconos.append(QIcon(pixmap))

    return iconos

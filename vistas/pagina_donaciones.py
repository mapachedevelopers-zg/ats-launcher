from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QFrame
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from utils import aplicar_sombra
from i18n import tr
from constantes import DONACIONES, RECURSOS_OFUSCADOS

# CAMBIO: las cuentas ya no estan escritas aqui; se leen de config_launcher.json
# (seccion "donaciones" y recurso "qr"). Vacias = boton desactivado.
TEXTO_SIN_CONFIGURAR = "Sin configurar"


class PaginaDonaciones(QWidget):
    def __init__(self):
        super().__init__()
        self.cuenta_breb = DONACIONES.get("cuenta_breb", "")
        self.paypal_url = DONACIONES.get("paypal_url", "")

        diseño = QVBoxLayout(self)
        self.titulo = QLabel(tr("APOYA EL PROYECTO"))
        self.titulo.setObjectName("tituloSeccion")
        self.titulo.setAlignment(Qt.AlignCenter)
        diseño.addWidget(self.titulo)

        cuadrícula = QGridLayout()
        cuadrícula.setContentsMargins(90, 15, 90, 50)
        cuadrícula.setHorizontalSpacing(22)
        cuadrícula.setVerticalSpacing(22)

        self.tarjeta_qr = self._tarjeta_info("QR NEQUI")
        texto_qr = "Cargando QR…" if RECURSOS_OFUSCADOS.get("qr") else TEXTO_SIN_CONFIGURAR
        self.etiqueta_qr = QLabel(texto_qr)
        self.etiqueta_qr.setAlignment(Qt.AlignCenter)
        self.etiqueta_qr.setObjectName("qr")
        self.tarjeta_qr.layout().addWidget(self.etiqueta_qr, 1)
        cuadrícula.addWidget(self.tarjeta_qr, 0, 0, 2, 1)

        bre = self._tarjeta_info("Transferencia por Bre-B")
        self.boton_breb = QPushButton(self.cuenta_breb or TEXTO_SIN_CONFIGURAR)
        self.boton_breb.setObjectName("datoDonacion")
        self.boton_breb.setEnabled(bool(self.cuenta_breb))
        self.boton_breb.clicked.connect(self.copiar_breb)
        bre.layout().addWidget(self.boton_breb, 1)
        cuadrícula.addWidget(bre, 0, 1)

        paypal = self._tarjeta_info("PayPal")
        self.boton_paypal = QPushButton("" if self.paypal_url else TEXTO_SIN_CONFIGURAR)
        self.boton_paypal.setObjectName("datoDonacion")
        self.boton_paypal.setCursor(Qt.PointingHandCursor)
        self.boton_paypal.setEnabled(bool(self.paypal_url))
        self.boton_paypal.clicked.connect(self._abrir_paypal)

        paypal.layout().addWidget(self.boton_paypal, 1)
        cuadrícula.addWidget(paypal, 1, 1)

        cuadrícula.setColumnStretch(0, 1)
        cuadrícula.setColumnStretch(1, 1)
        cuadrícula.setRowStretch(0, 1)
        cuadrícula.setRowStretch(1, 1)
        diseño.addLayout(cuadrícula, 1)

    def _tarjeta_info(self, titulo):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaInfo")
        aplicar_sombra(tarjeta)
        diseño = QVBoxLayout(tarjeta)
        diseño.setContentsMargins(24, 20, 24, 20)
        etiqueta = QLabel(titulo.upper())
        etiqueta.setObjectName("tituloTarjeta")
        etiqueta.setAlignment(Qt.AlignCenter)
        diseño.addWidget(etiqueta)
        return tarjeta

    def _abrir_paypal(self):
        if self.paypal_url:
            QDesktopServices.openUrl(QUrl(self.paypal_url))

    def copiar_breb(self):
        if not self.cuenta_breb:
            return
        QGuiApplication.clipboard().setText(self.cuenta_breb)
        self.boton_breb.setText("¡Copiado!")
        QTimer.singleShot(
            1500, lambda: self.boton_breb.setText(self.cuenta_breb))

    def actualizar_textos_idioma(self):
        """Actualiza el título de donaciones."""
        if hasattr(self, "titulo"):
            self.titulo.setText(tr("APOYA EL PROYECTO"))

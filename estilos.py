
from temas import obtener_tema_actual, obtener_ruta_recurso, asegurar_flechas_dropdown


def obtener_hoja_estilos():
    tema = obtener_tema_actual()
    color_acento = tema["acento"]
    color_contraste = tema["contraste"]
    fondo_principal = tema.get("fondo_principal", "#0F1115")
    fondo_tarjeta = tema.get("fondo_tarjeta", "#181A20")
    fondo_sidebar = tema.get("fondo_sidebar", "#0B0C0E")
    fondo_boton_menu = tema.get("fondo_boton_menu", "#181A20")
    fondo_boton_hover = tema.get("fondo_boton_hover", "#232731")
    fondo_input = tema.get("fondo_input", "#1E1E1E")
    borde_suave = tema.get("borde_suave", "#1F222A")
    borde_tarjeta = tema.get("borde_tarjeta", "#262932")

    asegurar_flechas_dropdown()
    ruta_arrow = obtener_ruta_recurso("arrow_down.png")
    ruta_arrow_hover = obtener_ruta_recurso("arrow_down_hover.png")

    return f"""
        QMainWindow, QWidget {{ 
            background: {fondo_principal}; 
            color: #E2E8F0; 
            font-family: 'Segoe UI', sans-serif; 
        }}
        #textoCarga {{ 
            font-size: 20px; 
            font-weight: 700; 
            color: {color_acento};
        }}
        #barraLateral {{ 
            background: {fondo_sidebar}; 
            border-right: 1px solid {borde_suave};
        }}

        #logoLabel {{ 
            background: transparent; 
            background-color: transparent;
            border: none; 
        }}

        #marca {{ 
            color: {color_acento}; 
            font-size: 28px; 
            font-weight: 800; 
            letter-spacing: 2px; 
        }}

        #botonMenu {{ 
            background: {fondo_boton_menu}; 
            color: #94A3B8;
            border: 1px solid {borde_tarjeta}; 
            border-radius: 8px; 
            text-align: left; 
            padding-left: 16px; 
            font-weight: 600;
        }}
        #botonMenu:hover {{ 
            background: {fondo_boton_hover}; 
            color: #FFFFFF;
            border-color: {color_acento}; 
        }}
        #botonMenu[activo="true"] {{ 
            background: {fondo_boton_hover}; 
            color: #FFFFFF;
            border-color: {color_acento}; 
            font-weight: 700;
        }}

        #tituloSeccion {{ 
            font-size: 22px; 
            font-weight: 800; 
            color: #F8FAFC;
            letter-spacing: 1px;
            padding: 20px; 
        }}
        #tarjetaMod, #tarjetaInfo {{ 
            background: {fondo_tarjeta}; 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 10px; 
        }}

        #tarjetaMod:hover, #tarjetaInfo:hover {{ 
            border: 1px solid {color_acento}; 
        }}
        #tituloTarjeta {{ 
            font-size: 14px; 
            font-weight: 700; 
            color: #E2E8F0;
        }}
        #imagenMod {{ 
            background: {fondo_sidebar}; 
            border-radius: 4px; 
            color: #64748B; 
        }}
        #capaDescarga {{ 
            background: rgba(229, 169, 60, 0.85); 
            border: 0; 
        }}
        #textoProgreso {{ 
            background: transparent; 
            color: white; 
            font-weight: 800; 
        }}

        QPushButton {{ 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 6px; 
            padding: 7px 12px; 
            color: #E2E8F0; 
            background: {fondo_boton_menu}; 
            font-weight: 600;
            outline: none; 
        }}
        QPushButton:focus, QPushButton:focus:pressed {{ 
            outline: none; 
        }}
        QPushButton:hover {{ 
            background: {fondo_boton_hover}; 
            border-color: {color_acento}; 
            color: #FFFFFF;
        }}
        QPushButton[estado="exito"] {{ 
            background: #059669; 
            color: #FFFFFF;
            font-weight: 800; 
            border: 1px solid #10B981; 
        }}

        QProgressBar {{ 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 4px; 
            background: {fondo_sidebar}; 
            text-align: center;
        }}
        QProgressBar::chunk {{ 
            background: {color_acento}; 
            border-radius: 3px;
        }}

        /* BARRAS DE DESPLAZAMIENTO NATIVAS Y OSCURAS */
        QScrollBar:horizontal {{ 
            background: {fondo_sidebar}; 
            height: 14px; 
            margin: 0 18px; 
            border: 1px solid {borde_tarjeta}; 
        }}
        QScrollBar::handle:horizontal {{ 
            background: {fondo_boton_hover}; 
            min-width: 55px; 
            border-radius: 5px; 
            margin: 2px; 
        }}
        QScrollBar::handle:horizontal:hover {{ 
            background: {color_acento}; 
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ 
            width: 0px; 
            background: transparent; 
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ 
            background: {fondo_sidebar}; 
        }}
        
        QScrollBar:vertical {{ 
            background: {fondo_sidebar}; 
            width: 14px; 
            margin: 18px 0; 
            border: 1px solid {borde_tarjeta}; 
        }}
        QScrollBar::handle:vertical {{ 
            background: {fondo_boton_hover}; 
            min-height: 55px; 
            border-radius: 5px; 
            margin: 2px; 
        }}
        QScrollBar::handle:vertical:hover {{ 
            background: {color_acento}; 
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ 
            height: 0px; 
            background: transparent; 
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ 
            background: {fondo_sidebar}; 
        }}

        #flechaGaleria {{ 
            background: {fondo_boton_menu}; 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 20px; 
            color: #E2E8F0; 
            font-size: 36px; 
            font-weight: 300; 
            padding-bottom: 8px;
        }}
        #flechaGaleria:hover {{ 
            background: {color_acento}; 
            color: {color_contraste};
            font-weight: bold; 
        }}

        #botonValidar {{ 
            background: {fondo_boton_menu}; 
            border: 1px solid {borde_tarjeta}; 
            color: #E2E8F0;
            font-weight: 600; 
            border-radius: 6px; 
        }}
        #botonValidar:hover {{ 
            background: {fondo_boton_hover}; 
            border-color: {color_acento}; 
            color: #FFFFFF;
        }}

        #tarjetaRed {{ 
            background: {fondo_tarjeta}; 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 12px; 
            font-size: 15px; 
            font-weight: 700; 
            color: #E2E8F0;
        }}
        #tarjetaRed:hover {{ 
            border-color: {color_acento}; 
            background: {fondo_boton_hover}; 
        }}

        #datoDonacion {{ 
            color: {color_acento}; 
            font-size: 19px; 
            font-weight: 800; 
        }}

        #notaPlugin {{ 
            color: {color_acento}; 
            font-size: 10px; 
            font-weight: 700; 
            background: transparent; 
        }}

        QComboBox {{ 
            background-color: {fondo_input}; 
            color: #E2E8F0; 
            border: 1px solid {borde_tarjeta}; 
            border-radius: 6px; 
            padding: 6px 12px; 
            font-size: 13px; 
            font-weight: 600; 
        }}
        QComboBox:hover {{ 
            border-color: {color_acento}; 
        }}
        QComboBox::drop-down {{ 
            subcontrol-origin: padding; 
            subcontrol-position: top right; 
            width: 32px; 
            border-left: 1px solid {borde_tarjeta}; 
            border-top-right-radius: 6px; 
            border-bottom-right-radius: 6px; 
        }}
        QComboBox::down-arrow {{ 
            image: url('{ruta_arrow}'); 
            width: 12px; 
            height: 12px; 
            margin-right: 4px; 
        }}
        QComboBox::down-arrow:hover {{ 
            image: url('{ruta_arrow_hover}'); 
            width: 12px; 
            height: 12px; 
            margin-right: 4px; 
        }}
        QComboBox QAbstractItemView {{ 
            background-color: {fondo_tarjeta}; 
            color: #E2E8F0; 
            border: 1px solid {borde_tarjeta}; 
            selection-background-color: {fondo_boton_hover}; 
            selection-color: {color_acento}; 
            padding: 4px; 
            outline: 0; 
        }}

        #paypal {{ 
            background: transparent; 
            border: none; 
        }}
        #paypal:hover {{ 
            background: {fondo_boton_hover}; 
            border-radius: 8px; 
        }}
        /* --- ESTILOS BARRA DE TÍTULO PERSONALIZADA --- */
        #barraTituloCustom {{ 
            background: {fondo_sidebar}; 
            border-bottom: 1px solid {borde_suave}; 
        }}
        #tituloAppCustom {{ 
            color: #94A3B8; 
            font-size: 12px; 
            font-weight: 700; 
            letter-spacing: 1px; 
            background: transparent; 
        }}
        #btnTituloMin, #btnTituloMax {{ 
            background: transparent; 
            color: #94A3B8; 
            border: none; 
            font-size: 13px; 
            font-weight: bold; 
            border-radius: 0px; 
        }}
        #btnTituloMin:hover, #btnTituloMax:hover {{ 
            background: {fondo_boton_hover}; 
            color: #FFFFFF; 
        }}
        #btnTituloCerrar {{ 
            background: transparent; 
            color: #94A3B8; 
            border: none; 
            font-size: 13px; 
            font-weight: bold; 
            border-radius: 0px; 
        }}
        #btnTituloCerrar:hover {{ 
            background: #E11D48; 
            color: #FFFFFF; 
        }}
    """

from typing import Callable, Any
from domain.formatters import pad_left, pad_right, format_date_ddmmaaaa, format_decimal_sicore
from domain.models import RetencionSicore

class SicoreLayout:
    """
    Define la estructura de la cartilla SICORE de forma declarativa.
    Facilita modificar la longitud de los campos, los rellenos y el mapeo.
    """
    
    # Basado en la cartilla oficial y validado contra V3.txt
    FIELDS = [
        ("codigo_comprobante", 2, lambda v, l: pad_left(v, l, '0')),
        ("fecha_emision", 10, lambda v, l: pad_right(format_date_ddmmaaaa(v), l, ' ')),
        ("numero_comprobante", 16, lambda v, l: pad_left(v, l, ' ')),
        ("importe_comprobante", 16, lambda v, l: format_decimal_sicore(v, l)),
        ("codigo_impuesto", 4, lambda v, l: pad_left(v, l, ' ')),
        ("codigo_regimen", 3, lambda v, l: pad_left(v, l, '0')),
        ("codigo_operacion", 1, lambda v, l: pad_left(str(v), l, ' ')),
        ("base_calculo", 14, lambda v, l: format_decimal_sicore(v, l)),
        ("fecha_emision_retencion", 10, lambda v, l: pad_right(format_date_ddmmaaaa(v), l, ' ')),
        ("codigo_condicion", 2, lambda v, l: pad_left(v, l, '0')),
        ("retencion_sujetos_suspendidos", 1, lambda v, l: pad_right(str(v), l, ' ')),
        ("importe_retencion", 14, lambda v, l: format_decimal_sicore(v, l)),
        ("porcentaje_exclusion", 6, lambda v, l: format_decimal_sicore(v, l)),
        ("fecha_publicacion", 10, lambda v, l: pad_right(format_date_ddmmaaaa(v), l, ' ')),
        ("tipo_documento_retenido", 2, lambda v, l: pad_left(v, l, '0')),
        ("numero_documento_retenido", 20, lambda v, l: pad_right(str(v), l, ' ')),
        ("numero_certificado_original", 14, lambda v, l: pad_left(v, l, '0')),
        ("filler_spaces", 30, lambda v, l: " " * l),
        ("filler_zeros", 24, lambda v, l: "0" * l)
    ]

    @classmethod
    def format_line(cls, retencion: RetencionSicore) -> str:
        """
        Ensambla una línea de texto basada en la declaración FIELDS.
        """
        line = ""
        for attr_name, length, formatter in cls.FIELDS:
            # Obtenemos el valor de la entidad de dominio si existe, sino None
            value = getattr(retencion, attr_name, None)
            # Aplicamos la función de formato pasándole la longitud esperada
            formatted_value = formatter(value, length)
            # Aseguramos de que el formateo no exceda la longitud permitida
            if len(formatted_value) > length:
                formatted_value = formatted_value[:length]
            line += formatted_value
        return line

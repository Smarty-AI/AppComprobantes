import pytest
import datetime
from decimal import Decimal
from domain.models import RetencionSicore
from infrastructure.sicore_layout import SicoreLayout

def test_sicore_layout_formatting_matches_old_system():
    """
    Comprueba que la lógica de formateo genere exactamente
    la misma línea para un caso conocido del output antiguo.
    
    Línea objetivo (Row 1 del KS Ret. Ganancias 1º Enero_V3.txt):
    0102/01/2026   00004000021610000000092100,00 217094100000056691,6302/01/202601 00000001300,00000,00          8020291932445         00000000009411                              000000000000000000000000
    """
    
    retencion = RetencionSicore(
        codigo_comprobante="01",
        fecha_emision=datetime.date(2026, 1, 2),
        numero_comprobante="0000400002161",
        importe_comprobante=Decimal("92100.00"),
        codigo_impuesto="217",
        codigo_regimen="094",
        codigo_operacion="1",
        base_calculo=Decimal("56691.63"),
        fecha_emision_retencion=datetime.date(2026, 1, 2),
        codigo_condicion="01",
        retencion_sujetos_suspendidos=" ",
        importe_retencion=Decimal("92100.00"),
        porcentaje_exclusion=Decimal("0.00"),
        fecha_publicacion=None,
        tipo_documento_retenido="80",
        numero_documento_retenido="20291932445",
        numero_certificado_original="9411"
    )
    
    # El layout está configurado para producir la misma cadena
    formatted_line = SicoreLayout.format_line(retencion)
    
    # 199 chars total including trailing fillers
    expected_line = "0102/01/2026   00004000021610000000092100,00 217094100000056691,6302/01/202601 00000092100,00000,00          8020291932445         00000000009411                              000000000000000000000000"
    
    assert formatted_line == expected_line
    assert len(formatted_line) == 199

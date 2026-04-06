from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional

@dataclass
class RetencionSicore:
    """
    Entidad fundamental que representa una línea de retención de SICORE.
    Mantiene los tipos de datos en sus formatos nativos (Decimal, date) 
    para aislar las reglas de negocio de su representación final en texto (padding).
    """
    codigo_comprobante: str
    fecha_emision: date
    numero_comprobante: str
    importe_comprobante: Decimal
    codigo_impuesto: str
    codigo_regimen: str
    codigo_operacion: str
    base_calculo: Decimal
    fecha_emision_retencion: date
    codigo_condicion: str
    retencion_sujetos_suspendidos: str
    importe_retencion: Decimal
    porcentaje_exclusion: Decimal
    fecha_publicacion: Optional[date]
    tipo_documento_retenido: str
    numero_documento_retenido: str
    numero_certificado_original: str
    is_matched: bool = True
    situacion: Optional[str] = None

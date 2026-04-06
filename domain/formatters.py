from datetime import date
from decimal import Decimal
from typing import Optional

def pad_right(value: str, length: int, fillchar: str = " ") -> str:
    """Rellena a la derecha hasta alcanzar la longitud especificada."""
    return str(value)[:length].ljust(length, fillchar)

def pad_left(value: str, length: int, fillchar: str = "0") -> str:
    """Rellena a la izquierda hasta alcanzar la longitud especificada."""
    return str(value)[:length].rjust(length, fillchar)

def format_date_ddmmaaaa(d: Optional[date]) -> str:
    """Formatea una fecha como DD/MM/AAAA. Si es nula, retorna espacios en blanco."""
    if not d:
        return ""
    return d.strftime("%d/%m/%Y")

def format_decimal_sicore(val: Decimal, length: int, decimals: int = 2) -> str:
    """
    Formatea un decimal para SICORE.
    Suele requerir un formato de enteros y decimales sin coma,
    o en algunos casos rellenado con ceros a la izquierda.
    Asumimos formato estándar: coma convertida a punto o directamente sin coma?
    Según SICORE, los importes se suelen reportar con formato especifico.
    Si se requiere decimales separados por coma: "000000000000,00"
    Ajustar según necesidad exacta.
    """
    if val is None:
        val = Decimal("0.00")
        
    # Formateamos con la cantidad de decimales fija
    formatted = f"{val:.{decimals}f}" 
    
    # En SICORE a veces piden cambiar . por , o enviarlo todo junto.
    # Supongamos que pide reemplazar el punto por coma y rellenar con ceros.
    formatted = formatted.replace(".", ",")
    return pad_left(formatted, length, "0")

def clean_string(value: str) -> str:
    """Limpia saltos de línea y espacios extras de un texto."""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.split())

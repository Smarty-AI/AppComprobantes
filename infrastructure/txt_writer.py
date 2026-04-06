from typing import List
from domain.interfaces import IRetencionWriter
from domain.models import RetencionSicore
from infrastructure.sicore_layout import SicoreLayout

class SicoreTxtWriter(IRetencionWriter):
    """
    Escritor configurado para emitir el TXT en formato SICORE.
    Utiliza el SicoreLayout para procesar el formato de cada línea.
    """
    def write(self, retenciones: List[RetencionSicore], dest_path: str) -> None:
        with open(dest_path, 'w', encoding='utf-8', newline='\r\n') as f:
            for i, ret in enumerate(retenciones):
                if not ret.is_matched:
                    continue
                line = SicoreLayout.format_line(ret)
                # No añadir salto de línea al último registro si es requerido por el validador, 
                # pero generalmente es seguro usar \n siempre.
                f.write(line + "\n")

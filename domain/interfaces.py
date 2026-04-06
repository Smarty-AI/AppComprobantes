from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import RetencionSicore

class IComprobanteReader(ABC):
    """
    Interfaz para leer comprobantes desde diversas fuentes (Excel, CSV).
    Debe retornar una lista de diccionarios o entidades crudas para ser procesadas.
    """
    @abstractmethod
    def read(self, filepath: str) -> List[Dict[str, Any]]:
        pass

class IRetencionWriter(ABC):
    """
    Interfaz para escribir las retenciones procesadas hacia un destino (TXT, Excel).
    """
    @abstractmethod
    def write(self, retenciones: List[RetencionSicore], dest_path: str) -> None:
        pass

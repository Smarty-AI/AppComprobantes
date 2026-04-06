import pandas as pd
from typing import Dict
from domain.interfaces import IRetencionWriter
from domain.models import RetencionSicore

class ExcelATxtUseCase:
    """
    Caso de Uso auxiliar:
    Toma un archivo Excel (que previamente fue generado por la app y modificado por el usuario),
    lee la hoja 'Retenciones', reconstruye las entidades y genera un nuevo TXT.
    """
    def __init__(self, writer_txt: IRetencionWriter):
        self.writer_txt = writer_txt

    def execute(self, origen_excel_path: str, destino_txt_path: str) -> None:
        # Leemos el Excel, específicamente la hoja de 'Retenciones'
        try:
            df = pd.read_excel(origen_excel_path, sheet_name='Retenciones')
        except Exception as e:
            raise ValueError(f"No se pudo leer la hoja 'Retenciones' del Excel. ¿Es el formato correcto?: {str(e)}")
            
        # Limpiamos nulos
        df = df.where(pd.notnull(df), None)
        
        # Convertimos cada fila del df en un RetencionSicore
        retenciones = []
        for _, row in df.iterrows():
            dict_row = row.to_dict()
            
            # Recreamos las fechas (pandas suele leerlas como Timestamp, las pasamos a date)
            for k in ['fecha_emision', 'fecha_emision_retencion', 'fecha_publicacion']:
                val = dict_row.get(k)
                if pd.notna(val) and val is not None:
                    try:
                        dict_row[k] = pd.to_datetime(val).date()
                    except:
                        pass
                else:
                     dict_row[k] = None

            # IMPORTANTE: Al leer de Excel con pandas, los números a veces se leen como floats 
            # (ej. 142.0 en vez de "142"). Para los importes, debemos evitar usar str() directo 
            # si es float porque puede introducir errores de precisión tipo 142.000000001
            from decimal import Decimal
            for k in ['importe_comprobante', 'base_calculo', 'importe_retencion', 'porcentaje_exclusion']:
                 val = dict_row.get(k)
                 if pd.notna(val) and val is not None:
                      try:
                          # Si es float, redondeamos a 2 decs para asegurar que sea exacto como en el CSV
                          v_float = round(float(val), 2)
                          dict_row[k] = Decimal(f"{v_float:.2f}")
                      except Exception:
                          try:
                              # Intento con formato AR: "1.234,56" -> "1234.56"
                              cleaned = str(val).strip().replace('.', '').replace(',', '.')
                              dict_row[k] = Decimal(cleaned)
                          except Exception:
                              dict_row[k] = Decimal("0.00")
                 else:
                      dict_row[k] = Decimal("0.00")
                      
            # Asegurar strings donde se necesita
            for k in ['codigo_comprobante', 'numero_comprobante', 'codigo_impuesto', 
                      'codigo_regimen', 'codigo_operacion', 'codigo_condicion', 
                      'retencion_sujetos_suspendidos', 'tipo_documento_retenido', 
                      'numero_documento_retenido', 'numero_certificado_original']:
                val = dict_row.get(k)
                if pd.notna(val) and val is not None:
                    s_val = str(val)
                    # Si pandas leyó un campo numérico entero (ej, nro_comprobante="000123") como float (123.0)
                    if s_val.endswith(".0"):
                        s_val = s_val[:-2]
                    dict_row[k] = s_val
                else:
                    dict_row[k] = ""

            # Instanciamos la clase con el diccionario desempaquetado
            # Filtramos keys que no pertenezcan al modelo por si hay columnas extra
            import dataclasses
            field_names = {f.name for f in dataclasses.fields(RetencionSicore)}
            filtered_dict = {k: v for k, v in dict_row.items() if k in field_names}
            
            retencion = RetencionSicore(**filtered_dict)
            retenciones.append(retencion)
            
        # Escribimos el TXT final
        self.writer_txt.write(retenciones, destino_txt_path)

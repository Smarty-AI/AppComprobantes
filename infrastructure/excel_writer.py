import pandas as pd
from typing import List
from domain.interfaces import IRetencionWriter
from domain.models import RetencionSicore
import dataclasses

class PandasExcelWriter(IRetencionWriter):
    """
    Escritor auxiliar que emite un archivo Excel con la data procesada.
    Sirve como reporte visual de qué fue lo que se parseó y se guardó en TXT.
    """
    def write(self, retenciones: List[RetencionSicore], dest_path: str) -> None:
        from decimal import Decimal
        from infrastructure.sicore_layout import SicoreLayout
        # 1. Preparar datos de Retenciones
        dicts = [dataclasses.asdict(r) for r in retenciones]
        
        from decimal import Decimal
        for row in dicts:
            for key, val in row.items():
                if isinstance(val, Decimal):
                    row[key] = round(float(val), 2)
                    
        df_all = pd.DataFrame(dicts)
        
        df_matched = df_all[df_all['is_matched'] == True].drop(columns=['is_matched', 'situacion'])
        df_unmatched = df_all[df_all['is_matched'] == False].drop(columns=['is_matched'])
        
        # 2. Preparar datos de Parámetros leídos de SicoreLayout
        parametros = []
        for index, item in enumerate(SicoreLayout.FIELDS):
            field_name, expected_length, formatter = item
            
            # Intentar inferir la regla de formato del código fuente de la lambda
            rule_desc = "Desconocida"
            try:
                source = inspect.getsource(formatter)
                if "pad_left" in source and "'0'" in source:
                    rule_desc = "Relleno con ceros a la izquierda"
                elif "pad_left" in source and "' '" in source:
                    rule_desc = "Relleno con espacios a la izquierda"
                elif "pad_right" in source and "' '" in source:
                    rule_desc = "Relleno con espacios a la derecha"
                elif "format_date_ddmmaaaa" in source:
                    rule_desc = "Fecha formato DDMMAAAA"
                elif "format_decimal_sicore" in source:
                    rule_desc = "Decimal sin coma, redondeado a 2 decimales y rellenado a izquierda con ceros. Si es negativo '-' reemplaza primer cero."
                elif "'filler_spaces'" in field_name:
                    rule_desc = "Espacios en blanco constantes"
                elif "'filler_zeros'" in field_name:
                    rule_desc = "Ceros constantes"
            except Exception:
                pass
                
            parametros.append({
                "NroCampo": index + 1,
                "Campo": field_name,
                "LongitudSICORE": expected_length,
                "ReglaDeFormato": rule_desc
            })
            
        df_parametros = pd.DataFrame(parametros)
        
        # 3. Escribir hojas
        with pd.ExcelWriter(dest_path, engine='openpyxl') as writer:
            df_matched.to_excel(writer, sheet_name='Retenciones', index=False)
            df_unmatched.to_excel(writer, sheet_name='Sin Match', index=False)
            df_parametros.to_excel(writer, sheet_name='Parametros', index=False)
            
            # Auto-ajustar ancho de columnas en Parámetros
            workbook = writer.book
            worksheet = writer.sheets['Parametros']
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter # Get the column name
                for cell in col:
                    try: # Necessary to avoid error on empty cells
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column].width = adjusted_width

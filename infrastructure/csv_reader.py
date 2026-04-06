import pandas as pd
from typing import List, Dict, Any, Union
from domain.interfaces import IComprobanteReader
import numpy as np

class PandasCsvReader(IComprobanteReader):
    """
    Lector de Mis Comprobantes AFIP (CSV).
    Asume la responsabilidad de aplicar conversión de Tipo de Cambio 
    y calcular montos exentos antes de entregar los datos crudos al Use Case.
    """
    
    def read(self, filepath: Union[str, List[str]]) -> List[Dict[str, Any]]:
        import zipfile
        import io
        
        all_records = []
        filepaths = filepath if isinstance(filepath, list) else [filepath]
        
        for fp in filepaths:
            is_zip = str(fp).lower().endswith('.zip')
            
            if is_zip:
                with zipfile.ZipFile(fp, 'r') as z:
                    for filename in z.namelist():
                        if filename.lower().endswith('.csv'):
                            print(f"DEBUG: Processing {filename} from ZIP...")
                            with z.open(filename) as f:
                                records = self._read_df(f)
                                all_records.extend(records)
            else:
                records = self._read_df(fp)
                all_records.extend(records)
                
        return all_records

    def _read_df(self, source) -> List[Dict[str, Any]]:
        # source can be a path or a file-like object
        # AFIP suele usar utf-8 o latin-1 y separador ;
        df = None
        for enc in ['utf-8', 'latin-1', 'utf-8-sig']:
            try:
                # We need to read it into memory if we want to retry encodings for file-like objects
                if hasattr(source, 'read') and hasattr(source, 'seek'): # Check for seekable file-like object
                    source.seek(0) # Reset position for retry
                    df = pd.read_csv(source, encoding=enc, sep=';', on_bad_lines='skip')
                elif hasattr(source, 'read'): # Non-seekable (like zipfile.open)
                    content = source.read()
                    df = pd.read_csv(io.BytesIO(content), encoding=enc, sep=';', on_bad_lines='skip')
                    source = io.BytesIO(content) # Prepare for next try if needed
                else: # Path
                    df = pd.read_csv(source, encoding=enc, sep=';', on_bad_lines='skip')
                
                # Check garbage
                if any('Ã' in str(c) for c in df.columns):
                    continue
                break
            except Exception: # Catch all exceptions for encoding attempts
                continue
                
        if df is None:
            # Last resort
            if hasattr(source, 'read') and hasattr(source, 'seek'):
                source.seek(0)
                df = pd.read_csv(source, encoding='latin-1', sep=None, engine='python', on_bad_lines='skip')
            elif hasattr(source, 'read'):
                # If it's a non-seekable file-like object, content should already be in io.BytesIO from previous attempts
                df = pd.read_csv(source, encoding='latin-1', sep=None, engine='python', on_bad_lines='skip')
            else:
                df = pd.read_csv(source, encoding='latin-1', sep=None, engine='python', on_bad_lines='skip')
        
        # Limpiar nombres de columnas primarios (quitar quotes, acentos, bajar a minúsculas)
        import unicodedata
        def clean_raw_col(c):
            c = str(c).strip().replace('"', '').replace("'", "").lower().replace(" ", "_").replace(".", "")
            return "".join(ch for ch in unicodedata.normalize('NFKD', c) if not unicodedata.combining(ch))
            
        df.columns = [clean_raw_col(col) for col in df.columns]

        # AFIP_COLUMN_MAP: Mapeo robusto con alias comunes
        AFIP_COLUMN_MAP = {
            'punto_de_venta': 'punto_de_venta', 'pto_vta': 'punto_de_venta', 'pto_de_venta': 'punto_de_venta',
            'numero_desde': 'numero_desde', 'nro_desde': 'numero_desde', 'num_desde': 'numero_desde',
            'numero_hasta': 'numero_hasta', 'nro_hasta': 'numero_hasta', 'num_hasta': 'numero_hasta',
            'nro_doc_emisor': 'nro_doc_emisor', 'cuit': 'nro_doc_emisor', 'nro_doc': 'nro_doc_emisor', 'doc_emisor': 'nro_doc_emisor',
            'tipo_cambio': 'tipo_cambio', 'tc': 'tipo_cambio',
            'imp_total': 'imp_total', 'total': 'imp_total',
            'imp_neto_gravado': 'imp_neto_gravado', 'neto_gravado': 'imp_neto_gravado', 'neto': 'imp_neto_gravado',
            'imp_neto_gravado_total': 'imp_neto_gravado',
            'imp_neto_no_gravado': 'imp_neto_no_gravado', 'neto_no_gravado': 'imp_neto_no_gravado',
            'imp_neto_no_gravado_total': 'imp_neto_no_gravado',
            'imp_op_exentas': 'imp_op_exentas', 'exento': 'imp_op_exentas', 'op_exentas': 'imp_op_exentas',
            'imp_op_exentas_total': 'imp_op_exentas'
        }
        df = df.rename(columns=AFIP_COLUMN_MAP)

        # Limpiar valores: quitar comillas de strings
        for col in df.columns:
            if df[col].dtype == 'O':
                df[col] = df[col].str.replace('"', '', regex=False).str.strip()

        # Mapeos numéricos precisos
        def toNumber(series):
            if series.dtype == 'O':
                res = series.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                return pd.to_numeric(res, errors='coerce').fillna(0.0)
            return series.fillna(0.0)
            
        # Convertimos las columnas numéricas EXCEPTO CUIT
        target_numeric_cols = [c for c in AFIP_COLUMN_MAP.values() if 'doc' not in c]
        for col in df.columns:
            if col in target_numeric_cols:
                df[col] = toNumber(df[col])
        
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')

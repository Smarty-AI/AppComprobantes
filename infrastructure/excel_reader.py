import pandas as pd
from typing import List, Dict, Any, Optional, Union
from domain.interfaces import IComprobanteReader

class PandasExcelReader(IComprobanteReader):
    """
    Lector de Comprobantes usando Pandas. Soporta Excel.
    Se ajusta para leer la hoja específica de certificados o tabla,
    ignorando cabeceras si es necesario.
    """
    def __init__(self):
        pass

    def _parse_pv_num_from_str(self, val_str: str) -> Optional[Dict[str, int]]:
        import re
        if not isinstance(val_str, str): return None
        match = re.search(r'(\d{1,5})-(\d{1,12})', val_str)
        if match:
            return {"pv": int(match.group(1)), "num": int(match.group(2))}
        return None

    def _normalize_invoice_id(self, pv: int, num: int) -> str:
        return f"{int(pv):05d}{int(num):08d}"
        
    def _parse_certificates_sheet(self, df_cert: pd.DataFrame) -> Dict[str, Any]:
        import re
        import os
        cert_db = {}
        current_cert = None
        
        # Cargar mapeo desde CSV
        escala_to_regimen = {}
        try:
            csv_path = os.path.join(os.path.dirname(__file__), "..", "regimen_codes.csv")
            df_reg = pd.read_csv(csv_path, dtype=str)
            for _, row in df_reg.iterrows():
                # Formatear a 2 y 3 dígitos respectivamente por si el csv no se guarda como texto
                cod_escala = row['Cod Escala'].zfill(2)
                regimen = row['Regimen'].zfill(3)
                escala_to_regimen[cod_escala] = regimen
        except Exception as e:
            # Fallback a los defaults originales si el archivo no existe o falla
            print(f"Warning: No se pudo cargar regimen_codes.csv ({e}). Usando defaults.")
            escala_to_regimen = {
                "03": "094",  # locaciones
                "02": "078",  # venta
                "06": "099",  # facturas m
                "04": "119"   # honorarios
            }
        
        for i in range(len(df_cert)):
            # Concatenar todas las celdas de la fila para manejar datos distribuidos
            row_vals = [str(x) for x in df_cert.iloc[i] if pd.notna(x)]
            row_text = " ".join(row_vals)
            
            def parse_ars(text):
                # Caso especial: ID largo (CUIT, Barcode) - si tiene más de 12 dígitos, ignorarlo
                only_digits = "".join(re.findall(r'\d', text))
                if len(only_digits) > 12:
                    return 0.0

                # Detectar formato: US (1,234.56) vs AR (1.234,56)
                # Si tiene ambos, el último es el decimal
                dot_pos = text.rfind('.')
                comma_pos = text.rfind(',')
                
                clean = text
                if dot_pos > -1 and comma_pos > -1:
                    if dot_pos > comma_pos: # US format
                        clean = text.replace(',', '')
                    else: # AR format
                        clean = text.replace('.', '').replace(',', '.')
                elif comma_pos > -1:
                    # Si la coma está al final (2 decimales), es decimal
                    if len(text) - comma_pos <= 3:
                        clean = text.replace(',', '.')
                    else:
                        clean = text.replace(',', '')
                elif dot_pos > -1:
                    # Si el punto está al final (2 decimales), es decimal
                    if len(text) - dot_pos <= 3:
                        pass # ya es punto decimal
                    else:
                        clean = text.replace('.', '')
                
                try:
                    val = float(clean)
                    return val if val < 1000000000 else 0.0
                except:
                    return 0.0

            if "Nro" in row_text and "Lugar y Fecha" in row_text:
                match = re.search(r'Nro\s+[:]?\s*(\d+)', row_text)
                if match:
                    cert_nro = match.group(1)
                    current_cert = {
                        "nro": cert_nro,
                        "invoices": [],
                        "regimen": "094",
                        "min_no_imp": 0.0,
                        "total_ret": 0.0,
                        "total_base": 0.0,
                        "cuit": None
                    }
                    
            if current_cert is None:
                continue
            
            if "C.U.I.T." in row_text:
                match = re.search(r'C\.U\.I\.T\.\s*[:]?\s*(\d{2}-\d{8}-\d{1})', row_text)
                if match:
                    current_cert["cuit"] = clean_cuit(match.group(1))

            if "Cod Escala" in row_text:
                match = re.search(r'Cod Escala\s*[:]?\s*(\d+)', row_text)
                if match:
                    current_cert["regimen"] = escala_to_regimen.get(match.group(1).zfill(2), "094")
                    
            if "Total Retenido Liquidacion" in row_text or "Monto Retenido" in row_text:
                  match = re.search(r'(?:Monto Retenido|Liquidacion)\s*[:]?\s*([\d.,]+)(?:\s|$)', row_text)
                  if match:
                      try:
                          current_cert["total_ret"] = parse_ars(match.group(1).strip())
                      except: pass

            if "Total Monto Imponible" in row_text:
                  match = re.search(r'Total Monto Imponible\s*[:]?\s*([\d.,]+)(?:\s|$)', row_text)
                  if match:
                      try:
                          current_cert["total_base"] = parse_ars(match.group(1).strip())
                      except: pass

            if "Min no Imponible" in row_text:
                  # Buscar el número que sigue inmediatamente al texto, hasta un espacio o fin de texto
                  match = re.search(r'Min no Imponible\s*[:]?\s*([\d.,]+)(?:\s|$)', row_text)
                  if match:
                      try:
                          val = parse_ars(match.group(1).strip())
                          # Sanity check: un MNI de billones no tiene sentido
                          if val < 1000000000:
                              current_cert["min_no_imp"] = val
                      except: pass

            inv_matches = re.finditer(r'FC\s?[A-Z]?\s?(\d{4,5})[-](\d{1,8})', row_text)
            for m in inv_matches:
                pv = int(m.group(1))
                num = int(m.group(2))
                inv_id = self._normalize_invoice_id(pv, num)
                
                # Usar CUIT en la key para evitar colisiones entre distintos proveedores con mismo nro factura
                key = (inv_id, current_cert["cuit"])
                cert_db[key] = current_cert
                current_cert["invoices"].append((pv, num))
                
        return cert_db

    def read(self, filepath: str) -> Dict[str, Any]:
        """
        Lee el Excel de DDJJs que contiene 'Datos' y 'Certif'.
        Retorna un diccionario con ambas estructuras procesadas.
        """
        datos_records = []
        cert_db = {}
        
        with pd.ExcelFile(filepath) as xls:
            # 1. Leer Datos
            df_datos = pd.read_excel(xls, sheet_name='Datos')
            df_datos.columns = [str(col).strip().replace("\n", " ") for col in df_datos.columns]
            df_datos = df_datos.where(pd.notnull(df_datos), None)
            datos_records = df_datos.to_dict('records')
            
            # 2. Leer Certificados
            sheet_cert = 'Certif' if 'Certif' in xls.sheet_names else 'Certificados' if 'Certificados' in xls.sheet_names else None
            
            if sheet_cert:
                df_cert = pd.read_excel(xls, sheet_name=sheet_cert, header=None)
                cert_db = self._parse_certificates_sheet(df_cert)
            
        return {
            "datos": datos_records,
            "certificados": cert_db
        }

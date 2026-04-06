from typing import List, Dict, Any, Union
from decimal import Decimal
from domain.interfaces import IComprobanteReader, IRetencionWriter
from domain.models import RetencionSicore
import pandas as pd
import re

class ProcesarComprobantesUseCase:
    """
    Caso de Uso principal. Orquesta el flujo:
    1. Leer datos de Mis Comprobantes CSV.
    2. Leer datos de DDJJ Excel (Datos y Certif).
    3. Cruzar información.
    4. Mapear a entidades de dominio (RetencionSicore).
    5. Enviar a escribir las retenciones.
    """
    
    def __init__(self, reader_csv: IComprobanteReader, reader_excel: IComprobanteReader, writers: List[IRetencionWriter]):
        self.reader_csv = reader_csv
        self.reader_excel = reader_excel
        self.writers = writers

    def execute(self, origen_csv_path: Union[str, List[str]], origen_excel_path: str, destino_paths: Dict[IRetencionWriter, str]) -> None:
        raw_csv_data = self.reader_csv.read(origen_csv_path)
        raw_excel_data = self.reader_excel.read(origen_excel_path)
        
        retenciones = self._cross_reference_data(raw_csv_data, raw_excel_data)
        
        for writer, path in destino_paths.items():
            writer.write(retenciones, path)

    def _get_val(self, r, col):
        if col not in r: return 0.0
        v = r[col]
        if pd.isna(v) or v is None: return 0.0
        return float(v)

    def _cross_reference_data(self, csv_data: List[Dict[str, Any]], excel_data: Dict[str, Any]) -> List[RetencionSicore]:
        retenciones = []
        df_datos = excel_data.get("datos", [])
        cert_db = excel_data.get("certificados", {})
        
        def clean_cuit(val):
            if val is None: return ""
            # Eliminar .0 y quedarnos solo con dígitos
            s = str(val).split('.')[0]
            return "".join(re.findall(r'\d+', s))

        # Build CSV index for fast lookup - handling collisions (multiple CUITs with same invoice number)
        csv_index = {}
        for row in csv_data:
            try:
                pv = int(float(row.get('punto_de_venta') or 0))
                num_desde = int(float(row.get('numero_desde') or 0))
                num_hasta = int(float(row.get('numero_hasta') or 0))
                
                if pv > 0:
                    for n in range(num_desde, num_hasta + 1):
                        csv_index.setdefault((pv, n), []).append(row)
            except: pass
        
        # --- PASS 1: Identify, calculate amounts and aggregate certificate totals ---
        temp_data = []
        cert_total_amounts = {} # key: cert_nro (TOTAL IMPORT)
        cert_total_bi_pre = {}  # key: cert_nro (TOTAL NET - Base Calculo Pre)
        certs_with_missing_matches = set()

        for i, row in enumerate(df_datos):
            # 1. Identificar comprobante
            doc_str = str(row.get('Documento', row.get('documento', '')))
            descr_str = str(row.get('Descripción', row.get('descripcion', '')))
            descr1_str = str(row.get('Descripción.1', row.get('descripcion_1', '')))
            full_text = f"{doc_str} {descr_str} {descr1_str}".upper()
            
            # CUIT
            cuit_excel = clean_cuit(row.get('CUIT') or row.get('CUIT ') or row.get('cuit'))
            
            matches = re.findall(r'(\d{1,5})-(\d{1,12})', full_text)
            pv, num = None, None
            candidates_pv_num = []
            
            for p_str, n_str in matches:
                p_tmp, n_tmp = int(p_str), int(n_str)
                # Filtro agresivo anti-CUIT: 
                # Si PV es de 2 dígitos y el prefijo es de CUIT, y el NUM es largo (8+), es CUIT.
                if len(p_str) == 2 and p_tmp in [20, 23, 27, 30, 33, 34] and len(n_str) >= 8:
                    continue
                candidates_pv_num.append((p_tmp, n_tmp))
            
            if not candidates_pv_num: continue
            
            # Priorización: Si uno de los candidatos ya figura en los certificados del Excel, elegir ese.
            for p_c, n_c in candidates_pv_num:
                tmp_id = f"{p_c:05d}{n_c:08d}"
                if (tmp_id, cuit_excel) in cert_db:
                    pv, num = p_c, n_c
                    break
            
            if pv is None:
                pv, num = candidates_pv_num[0]
                
            inv_id_norm = f"{pv:05d}{num:08d}"
            
            # 2. Fechas y Montos
            fecha_raw = row.get('Fecha Documento', row.get('fecha_documento'))
            try: fecha_emision = pd.to_datetime(fecha_raw).date()
            except: fecha_emision = None
                
            monto_excel = self._get_val(row, 'Monto')
            total_factura = abs(monto_excel)
            
            # 3. Cruzar con CSV (PV y NUM con Resolución de Conflictos)
            candidates = csv_index.get((pv, num), [])
            csv_row = None
            
            if len(candidates) == 1:
                csv_row = candidates[0]
            elif len(candidates) > 1:
                # Prioridad 1: Match por CUIT
                for cand in candidates:
                    if clean_cuit(cand.get('nro_doc_emisor')) == cuit_excel:
                        csv_row = cand
                        break
                # Prioridad 2: Match por Importe Total (si no hubo match CUIT)
                if not csv_row:
                    for cand in candidates:
                        cand_total = Decimal(str(cand.get('imp_total') or 0.0))
                        if abs(cand_total - Decimal(str(total_factura))) < 1.0:
                            csv_row = cand
                            break
                # Fallback: El primero
                if not csv_row:
                    csv_row = candidates[0]
            
            row_matched = csv_row is not None
                        
            base_imponible_pre = Decimal(str(total_factura))
            valor_comprobante = Decimal(str(total_factura))
            
            if csv_row:
                tc = Decimal(str(csv_row.get('tipo_cambio') or 1.0))
                if tc == 0: tc = Decimal("1.0")
                valor_comprobante = Decimal(str(csv_row.get('imp_total') or 0.0)) * tc
                
                neto_gravado = Decimal(str(csv_row.get('imp_neto_gravado') or 0.0))
                neto_no_gravado = Decimal(str(csv_row.get('imp_neto_no_gravado') or 0.0))
                op_exentas = Decimal(str(csv_row.get('imp_op_exentas') or 0.0))
                base_imponible_pre = (neto_gravado + neto_no_gravado + op_exentas) * tc

                if base_imponible_pre == 0 and valor_comprobante != 0:
                    base_imponible_pre = valor_comprobante

            cert_row_data = cert_db.get((inv_id_norm, cuit_excel))
            if cert_row_data:
                c_nro = cert_row_data["nro"]
                cert_total_amounts[c_nro] = cert_total_amounts.get(c_nro, Decimal("0.00")) + valor_comprobante
                cert_total_bi_pre[c_nro] = cert_total_bi_pre.get(c_nro, Decimal("0.00")) + base_imponible_pre
                if not row_matched:
                    certs_with_missing_matches.add(c_nro)

            temp_data.append({
                'row': row, 'inv_id_norm': inv_id_norm, 'fecha_emision': fecha_emision,
                'vc': valor_comprobante, 'bi_pre': base_imponible_pre, 'cuit': cuit_excel,
                'cert_data': cert_row_data, 'monto_excel': monto_excel, 'full_text': full_text,
                'is_matched': row_matched
            })

        # --- PASS 2: Calculate proportional MNI and build final objects ---
        for item in temp_data:
            cert_data = item['cert_data']
            mni_prorate = Decimal("0.00")
            cert_nro, regimen = "0", "094"
            final_is_matched = item['is_matched']
            
            if cert_data:
                cert_nro, regimen = cert_data["nro"], cert_data["regimen"]
                min_no_imp = Decimal(str(cert_data.get("min_no_imp", 0.0)))
                total_cert = cert_total_amounts.get(cert_nro, Decimal("0.00"))
                
                # VALIDACION DE PRECISION: Pago Acumulado (Total Monto Imponible)
                # La suma de los netos (bi_pre) debe coincidir con el total_base del certificado
                expected_base = Decimal(str(cert_data.get("total_base", 0.0)))
                actual_base = cert_total_bi_pre.get(cert_nro, Decimal("0.00"))
                
                if expected_base > 0:
                    # El 'Total Monto Imponible' del Excel ya tiene restado el 'Min no Imponible'
                    diff = abs(expected_base - (actual_base - min_no_imp))
                    
                    if diff > 10.0:
                        certs_with_missing_matches.add(cert_nro) # Invalida por falta de precisión

                if total_cert > 0 and min_no_imp > 0:
                    proportion = item['vc'] / total_cert
                    mni_prorate = min_no_imp * proportion
                
                # Rule: if any invoice in cert is missing CSV, entire cert is NOT matched
                if cert_nro in certs_with_missing_matches:
                    final_is_matched = False
            
            if cert_nro == "0":
                ref_cg = str(item['row'].get('Referencia CG', item['row'].get('referencia_cg', '')))
                if ref_cg.isdigit(): cert_nro = ref_cg
            
            base_calculo = max(Decimal("0.00"), item['bi_pre'] - mni_prorate)
            ret_amount = Decimal(str(-item['monto_excel']))
            doc_tipo_str = "01" if "FCA" in item['full_text'] else "06"
            
            situacion = None
            if cert_nro in certs_with_missing_matches:
                if not item['is_matched']:
                    situacion = "Comprobante no encontrado en CSV"
                else:
                    situacion = "Certificado excluido (una factura del cert. no tiene match)"
            elif not item['is_matched']:
                situacion = "Comprobante no encontrado en CSV"

            retenciones.append(RetencionSicore(
                codigo_comprobante=doc_tipo_str, fecha_emision=item['fecha_emision'],
                numero_comprobante=item['inv_id_norm'], importe_comprobante=item['vc'],
                codigo_impuesto="217", codigo_regimen=regimen, codigo_operacion="1",
                base_calculo=base_calculo, fecha_emision_retencion=item['fecha_emision'],
                codigo_condicion="01", retencion_sujetos_suspendidos="0",
                importe_retencion=ret_amount, porcentaje_exclusion=Decimal("0.00"),
                fecha_publicacion=None, tipo_documento_retenido="80",
                numero_documento_retenido=item['cuit'], numero_certificado_original=cert_nro,
                is_matched=final_is_matched,
                situacion=situacion
            ))
            
        return retenciones

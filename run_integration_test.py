import os
import sys
from datetime import datetime

# Añadir el directorio actual al path para poder importar los módulos
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from application.procesar_comprobantes import ProcesarComprobantesUseCase
from infrastructure.excel_reader import PandasExcelReader
from infrastructure.csv_reader import PandasCsvReader
from infrastructure.txt_writer import SicoreTxtWriter
from infrastructure.excel_writer import PandasExcelWriter

def run_test():
    print("Iniciando Test de Integración...")
    
    # Rutas de archivos de prueba
    tests_dir = os.path.join(os.getcwd(), "tests")
    excel_path = os.path.join(tests_dir, "KS Ret. Ganancias 1º Marzo.xlsx")
    csv_zip_path = os.path.join(tests_dir, "comprobantes_consulta_csv_recibidos_170619250_30609331190_20260406-1418.zip")
    
    if not os.path.exists(excel_path):
        print(f"Error: No se encuentra el archivo Excel en {excel_path}")
        return
    if not os.path.exists(csv_zip_path):
        print(f"Error: No se encuentra el archivo ZIP en {csv_zip_path}")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_txt = f"TEST_OUTPUT_{timestamp}.txt"
    output_xls = f"TEST_OUTPUT_{timestamp}.xlsx"
    
    print(f"Archivos de entrada:")
    print(f" - Excel: {excel_path}")
    print(f" - CSV (ZIP): {csv_zip_path}")
    
    # Inyectar dependencias
    reader_excel = PandasExcelReader()
    reader_csv = PandasCsvReader()
    writer_txt = SicoreTxtWriter()
    writer_xls = PandasExcelWriter()
    
    use_case = ProcesarComprobantesUseCase(reader_csv, reader_excel, [writer_txt, writer_xls])
    
    print("Ejecutando caso de uso...")
    try:
        csv_data = reader_csv.read(csv_zip_path)
        print(f"DEBUG: CSV records read: {len(csv_data)}")
        if len(csv_data) > 0:
            print(f"DEBUG: Normalized CSV columns: {list(csv_data[0].keys())}")
            # print(f"DEBUG: CSV first record: {csv_data[0]}")
            
        retenciones = use_case._cross_reference_data(csv_data, reader_excel.read(excel_path))
        print(f"Total retenciones generadas: {len(retenciones)}")
        matched = [r for r in retenciones if r.is_matched]
        print(f"Total coincidencias (matched): {len(matched)}")
        
        if len(retenciones) > 0:
            print(f"Ejemplo situacion: {retenciones[0].situacion}")

        use_case.execute(csv_zip_path, excel_path, {
            writer_txt: output_txt,
            writer_xls: output_xls
        })
        print(f"¡Éxito! Archivos generados:")
        print(f" - {output_txt}")
        print(f" - {output_xls}")
        
        # Verificar contenido básico si es posible
        if os.path.exists(output_txt):
            with open(output_txt, 'r') as f:
                lines = f.readlines()
                print(f"Líneas generadas en TXT: {len(lines)}")
                if len(lines) > 0:
                    print(f"Primera línea: {lines[0].strip()}")
        
    except Exception as e:
        print(f"Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()

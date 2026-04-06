import streamlit as st
import pandas as pd
import tempfile
import os
import zipfile
import io
from datetime import datetime

from application.procesar_comprobantes import ProcesarComprobantesUseCase
from application.excel_a_txt import ExcelATxtUseCase
from infrastructure.excel_reader import PandasExcelReader
from infrastructure.csv_reader import PandasCsvReader
from infrastructure.txt_writer import SicoreTxtWriter
from infrastructure.excel_writer import PandasExcelWriter

REGIMEN_CSV_PATH = os.path.join(os.path.dirname(__file__), "regimen_codes.csv")

# Configuration for aesthetic
st.set_page_config(
    page_title="App Comprobantes SICORE", 
    page_icon="📄", 
    layout="wide"
)

def apply_custom_css():
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50; 
            color: white; 
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 16px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        }
        .titulo {
            color: #3f51b5;
            text-align: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)


def load_regimens():
    if "regimen_table" not in st.session_state:
        try:
            df = pd.read_csv(REGIMEN_CSV_PATH, dtype=str)
        except Exception:
            df = pd.DataFrame(columns=["Cod Escala", "Regimen", "Descripcion"])
        st.session_state["regimen_table"] = df
    return st.session_state["regimen_table"]


def edit_regimens_table(df):
    if hasattr(st, "data_editor"):
        return st.data_editor(df, num_rows="dynamic", key="regimen_editor", use_container_width=True)
    elif hasattr(st, "experimental_data_editor"):
        return st.experimental_data_editor(df, num_rows="dynamic", key="regimen_editor", use_container_width=True)
    else:
        st.warning(
            "Tu versión de Streamlit no soporta editor de datos interactivo. "
            "La lista de regímenes se mostrará como tabla y puedes subir un CSV para reemplazarla."
        )
        st.dataframe(df)

        uploaded = st.file_uploader("Subir regímenes actualizados (CSV)", type=["csv"], key="regimen_csv_upload")
        if uploaded is not None:
            try:
                new_df = pd.read_csv(uploaded, dtype=str)
                st.success(f"Regímenes cargados desde CSV ({len(new_df)} filas).")
                return new_df
            except Exception as e:
                st.error(f"Error leyendo CSV de regímenes: {e}")
        return df


def main():
    apply_custom_css()
    
    st.markdown("<h1 class='titulo'>Gestor de Comprobantes a SICORE</h1>", unsafe_allow_html=True)
    st.write("Convierte tus planillas Excel o CSV en archivos listos para el aplicativo SICORE usando arquitectura limpia.")
    
    st.markdown("--- ")

    # Editable regimen table (in memory)
    st.header("📋 Regímenes cargados y editables")
    st.write("Editá los regímenes en memoria antes de procesar los comprobantes.")

    reg_df = load_regimens()
    edited_reg_df = edit_regimens_table(reg_df)

    if st.button("Guardar cambios de regímenes", key="guardar_regimen"):
        st.session_state["regimen_table"] = edited_reg_df
        st.success(f"Regímenes actualizados en memoria ({len(edited_reg_df)} filas).")

    st.info("Este conjunto se usa en memoria para validaciones / filtros antes de procesar. No altera el CSV original.")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📥 Carga de Archivos")
        uploaded_ddjj = st.file_uploader("1. Archivo DDJJ (Excel con hojas 'Datos' y 'Certif')", type=["xlsx", "xls"])
        uploaded_csv = st.file_uploader("2. Mis Comprobantes AFIP — Recibidos (CSV o ZIP)", type=["csv", "zip"], accept_multiple_files=True)
    
    with col2:
        st.subheader("⚙️ Opciones y Procesamiento")
        st.write("La aplicación cruzará la información de la DDJJ con los comprobantes de AFIP y aplicará el layout SICORE.")

        regimen_actual = st.session_state.get("regimen_table", pd.DataFrame())
        st.write(f"Regímenes activos en memoria: {len(regimen_actual)}")

        if uploaded_ddjj is not None and uploaded_csv:
            # Validar que no se suban comprobantes Emitidos
            archivos_emitidos = [f.name for f in uploaded_csv if "emitido" in f.name.lower()]
            if archivos_emitidos:
                st.error(f"El archivo '{archivos_emitidos[0]}' parece ser de Comprobantes **Emitidos**. Este proceso requiere archivos de Comprobantes **Recibidos**.")

            if not archivos_emitidos and st.button("Procesar Archivos Ahora 🚀"):
                with st.spinner("Validando formato y procesando cruce de datos..."):
                    try:
                        ext_ddjj = uploaded_ddjj.name.split('.')[-1].lower()

                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext_ddjj}") as tmp_ddjj:
                            tmp_ddjj.write(uploaded_ddjj.getvalue())
                            temp_path_ddjj = tmp_ddjj.name

                        temp_csv_paths = []
                        for f_csv in uploaded_csv:
                            ext_csv = f_csv.name.split('.')[-1].lower()
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext_csv}") as tmp_csv:
                                tmp_csv.write(f_csv.getvalue())
                                temp_csv_paths.append(tmp_csv.name)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                        # Configuramos las salidas
                        temp_path_out_txt = temp_path_ddjj + f"_SIAP_{timestamp}.txt"
                        temp_path_out_xls = temp_path_ddjj + f"_Reporte_{timestamp}.xlsx"

                        # Inyectamos dependencias
                        reader_excel = PandasExcelReader()
                        reader_csv = PandasCsvReader()

                        writer_txt = SicoreTxtWriter()
                        writer_xls = PandasExcelWriter()

                        use_case = ProcesarComprobantesUseCase(reader_csv, reader_excel, [writer_txt, writer_xls])

                        # Ejecutamos
                        retenciones = use_case.execute(temp_csv_paths, temp_path_ddjj, {
                            writer_txt: temp_path_out_txt,
                            writer_xls: temp_path_out_xls
                        })

                        total = len(retenciones)
                        sin_match = sum(1 for r in retenciones if not r.is_matched)
                        con_match = total - sin_match

                        if sin_match == 0:
                            st.success(f"¡Proceso finalizado! {con_match} retenciones procesadas correctamente.")
                        else:
                            st.success(f"¡Proceso finalizado! {con_match} retenciones procesadas correctamente.")
                            st.warning(f"{sin_match} retención(es) no encontrada(s) en el CSV de AFIP — revisalas en la hoja 'Sin Match' del Excel descargado.")
                        
                        # Habilitamos descarga en ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            zip_file.write(temp_path_out_txt, f"Importacion_SIAP_{timestamp}.txt")
                            zip_file.write(temp_path_out_xls, f"Reporte_Retenciones_{timestamp}.xlsx")
                            
                        st.download_button(
                            label="Descargar Archivos (ZIP) 📦",
                            data=zip_buffer.getvalue(),
                            file_name=f"Resultados_SIAP_{timestamp}.zip",
                            mime="application/zip"
                        )
                        
                        # Limpieza
                        os.unlink(temp_path_ddjj)
                        for p in temp_csv_paths:
                            os.unlink(p)
                        
                    except Exception as e:
                        import traceback
                        st.error(f"Ocurrió un error procesando los archivos principales: {str(e)}")
                        st.code(traceback.format_exc(), language="python")
                        
    st.markdown("---")
    st.header("🔄 Re-generar TXT desde Excel Editado")
    st.write("Si descargaste el reporte Excel, modificaste algún valor en la hoja 'Retenciones' y querés generar un nuevo TXT para el SIAP rápidamente:")
    
    uploaded_edited_excel = st.file_uploader("Subí el Excel modificado", type=["xlsx", "xls"], key="edited_excel")
    
    if uploaded_edited_excel is not None:
        if st.button("Generar TXT 🚀"):
            with st.spinner("Leyendo Excel y armando TXT..."):
                try:
                    ext = uploaded_edited_excel.name.split('.')[-1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_xlsx:
                        tmp_xlsx.write(uploaded_edited_excel.getvalue())
                        temp_path_xlsx = tmp_xlsx.name
                        
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_path_out_txt = temp_path_xlsx + f"_Regenerado_SIAP_{timestamp}.txt"
                    
                    writer_txt = SicoreTxtWriter()
                    use_case = ExcelATxtUseCase(writer_txt)
                    
                    use_case.execute(temp_path_xlsx, temp_path_out_txt)
                    
                    st.success("¡Archivo TXT regenerado exitosamente! ✨")
                    
                    with open(temp_path_out_txt, "rb") as file:
                        btn = st.download_button(
                            label="Descargar TXT Regenerado 📄",
                            data=file,
                            file_name=f"Importacion_SIAP_Editado_{timestamp}.txt",
                            mime="text/plain"
                        )
                        
                    os.unlink(temp_path_xlsx)
                    
                except Exception as e:
                    st.error(f"Ocurrió un error regenerando el TXT: {str(e)}")

if __name__ == "__main__":
    main()

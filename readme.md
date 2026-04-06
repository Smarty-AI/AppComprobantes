# App Comprobantes (Streamlit + SOLID)

Aplicación basada en Streamlit orientada a la carga y procesamiento de comprobantes en formatos Excel y CSV, para generar de forma estandarizada archivos de salida en `TXT` y `Excel`.

## Tecnologías
- **Python 3.x**
- **Streamlit**: Interfaz web rápida y sencilla.
- **Pandas**: Para la manipulación segura de datos tabulares en la capa de infraestructura.

## Estructura del Proyecto
- `domain/`: Lógica Core (Entidades, Interfaces, Formateadores).
- `application/`: Casos de Uso (Orquestación del flujo).
- `infrastructure/`: Implementaciones de Readers, Writers y Definición de Layout.
- `tests/`: Suite de pruebas unitarias y de validación.
- `docs/`: Especificaciones técnicas y de inputs.
- `main.py`: Punto de entrada de la aplicación Streamlit.

## Cómo ejecutar

```bash
pip install -r requirements.txt
streamlit run main.py
```

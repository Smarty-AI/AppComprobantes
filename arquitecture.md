# Arquitectura del Proyecto Automátización de Comprobantes (SOLID)

Este proyecto emplea una **Arquitectura en Capas (Limpia)** guiada por los principios **SOLID**. El objetivo principal es mantener la lógica de negocio (el core o dominio) aislada de las interfaces de usuario (Streamlit) y de los servicios externos (Lectura/Escritura de archivos Excel/CSV/TXT).

## Estructura de Capas

1. **Dominio (`domain/`)**:
   - Contiene las entidades principales (`RetencionSicore`).
   - Define las interfaces (puertos) para los lectores (`IComprobanteReader`) y escritores (`IRetencionWriter`).
   - Contiene formateadores genéricos reutilizables (`formatters.py`).
   - No tiene dependencias de otras capas ni de librerías externas pesadas.

2. **Casos de Uso (`application/`)**:
   - Orquesta la lógica de negocio (`ProcesarComprobantesUseCase`).
   - Realiza el mapeo de datos crudos a entidades de dominio y coordina la ejecución de los escritores.
   
3. **Infraestructura (`infrastructure/`)**:
   - Implementaciones concretas de las interfaces:
     - `csv_reader.py`: Lector de "Mis Comprobantes" con lógica interna de Tipo de Cambio y Exentos.
     - `excel_reader.py`: Lector flexible de Excel.
     - `txt_writer.py`: Generador de TXT usando el `SicoreLayout`.
     - `excel_writer.py`: Generador de reportes Excel.
     - `sicore_layout.py`: Definición declarativa del formato de salida.
   
4. **Presentación (`presentation/` o `ui/`)**:
   - La interfaz de usuario usando **Streamlit**.
   - Captura los archivos proporcionados por el usuario, invoca los casos de uso (pasándoles los adaptadores concretos) y entrega el resultado final.

## Principios SOLID Aplicados
- **SRP (Single Responsibility)**: Cada clase tiene una sola razón para cambiar. Los adaptadores solo leen/escriben, las entidades solo representan estado.
- **OCP (Open/Closed)**: Podremos añadir nuevos formatos de salida o entrada implementando nuevas clases que cumplan la interfaz, sin modificar los Use Cases.
- **LSP (Liskov Substitution)**: Las implementaciones (ej. `ExcelComprobanteRepository`) pueden reemplazar a su interfaz base `IComprobanteRepository` sin romper el sistema.
- **ISP (Interface Segregation)**: Interfaces pequeñas y específicas (ej. `IFileReader`, `IFileWriter`).
- **DIP (Dependency Inversion)**: Los casos de uso dependen de abstracciones (interfaces de lectura/escritura), no de `pandas` o de los detalles de `Streamlit`.

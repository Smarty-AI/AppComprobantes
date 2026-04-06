# Roadmap del Proyecto App Comprobantes

## Fase 1: Inicialización y Arquitectura (Actual)
- [x] Definición de la estructura de carpetas (Dominio, Aplicación, Infraestructura, UI).
- [x] Documentación inicial (`arquitecture.md`, `readme.md`, `roadmap.md`).

## Fase 2: Desarrollo del Core (Completado)
- [x] Definir modelo `RetencionSicore`.
- [x] Definir interfaces `IComprobanteReader` e `IRetencionWriter`.
- [x] Implementar `ProcesarComprobantesUseCase` para orquestar la conversión.

## Fase 3: Infraestructura (Completado)
- [x] Implementar lector de CSV (AFIP) con lógica de Tipo de Cambio.
- [x] Implementar lector de Excel flexible.
- [x] Implementar generador de TXT basado en `SicoreLayout` (Validado contra V3).
- [x] Implementar generador de Excel de reporte.

## Fase 4: Interfaz de Usuario (En progreso)
- [x] Estructura inicial de `main.py` con Streamlit.
- [x] Carga de archivos y botones de descarga funcionales.
- [ ] Refinar cruce de datos entre CSV y Excel en el Use Case.

## Fase 5: Testing y Refinamiento (Actual)
- [x] Suite de pruebas unitarias organizada en `/tests`.
- [x] Validación de Layout SICORE contra legacy output exitosa.
- [ ] Pruebas integrales de flujo completo.

# Especificación de Inputs y Procesamiento (AppComprobantes)

Este documento detalla los archivos de entrada esperados por la aplicación, las columnas requeridas y los cálculos o transformaciones que deben realizarse a nivel de **Adaptador de Entrada (Reader)**, asegurando que las reglas de conversión queden aisladas antes de inyectarse al Caso de Uso.

## 1. Archivo CSV ("Mis Comprobantes" AFIP)

Se trata de la exportación nativa de AFIP. 

### Columnas Requeridas
- **Fecha de Emisión**: Para `fecha_emision`.
- **Tipo de Comprobante**: Para derivar `codigo_comprobante`.
- **Punto de Venta** y **Número Hasta**: Para ensamblar `numero_comprobante`.
- **Tipo Doc. Emisor** y **Nro. Doc. Emisor**: Para identificar al proveedor/retenido.
- **Tipo Cambio** y **Moneda**: Para cálculos de conversión si fuera moneda extranjera.
- **Imp. Neto Gravado (varias alícuotas 21%, etc.)** y **Imp. Op. Exentas / Imp. Neto No Gravado**: Para armar la base de cálculo y separar montos.
- **Total IVA** e **Imp. Total**.

### Cálculos traslados al Reader
1. **Conversión por Tipo de Cambio**: 
   - Cualquier importe monetario leído (Neto gravado, exento, IVA) debe multiplicarse por la columna `Tipo Cambio` en el momento de la lectura si `Tipo Cambio` > 1.
2. **Definición de "Exento"**:
   - Sumarizar o extraer `Imp. Op. Exentas` + `Imp. Neto No Gravado`.
3. **Mínimo no Imponible**:
   - *Excluido temporalmente*: Por restricciones de tiempo, no se implementará el prorrateo del mínimo no imponible en la primera etapa.

## 2. Archivo Excel (Reporte del Sistema / Bejerman / etc.)

Suele venir con múltiples hojas (`Datos`, `Tabla`, `Certif`). 

### Hojas y Columnas Requeridas (Ejemplo `Tabla` / `Certif` sin cabeceras)
- **Hoja `Certif`**:
  - Columna de Fecha de Retención.
  - Columna de Importe de Retención.
  - Columna de Número de Certificado.
- **Hoja `Datos`**:
  - Suele contener los datos tabulares principales del proveedor, bases de cálculo y alícuotas que aplican a las facturas amparadas en el CSV.

### Interacción entre CSV y Excel
El lector del Excel extraerá únicamente lo referente a la **retención practicada** (importe, número de certificado original, base imponible de retención reportada por el sistema), mientras que el CSV aportará la pureza de los datos del comprobante respaldatorio. 

*Nota: Durante el cruce de ambos, el adapter de Excel o el UseCase consolidarán la información.*

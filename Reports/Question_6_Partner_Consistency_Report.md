# REPORTE: AUDITORÍA DE CONSISTENCIA OPERATIVA Y CONTRACTUAL DE PT-014 (QUESTION 6)
**Proyecto:** Integridad Operativa y Gobernanza de Socios Logísticos - LATAM Last Mile  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 28 de mayo de 2026  

---

## 📋 Resumen Ejecutivo

Este reporte presenta los resultados del análisis y auditoría de consistencia de datos y alineación contractual para el transportista **PT-014 (SaoPauloShip)**. El objetivo primordial de este análisis es evaluar si la calidad de la información operativa registrada por este socio cumple con los estándares mínimos para su inclusión en los reportes corporativos de SLA y OTH (On-Time Handling).

De acuerdo con el estándar de gobernanza analítica (Requerimiento **A8**), si el nivel de inconsistencias acumulado (rutas inactivas en progreso constante, violaciones cronológicas de marcas de tiempo y solapamiento físico imposible de vehículos en múltiples hubs) supera el **5%** de la flota de rutas asignadas, el socio debe ser excluido de los tableros e informes estándar para evitar sesgos operacionales.

Los hallazgos de la auditoría revelan un escenario crítico de incumplimiento y degradación de calidad de datos:
1. **Infracción Contractual Absoluta (100%):** El total de las **378 rutas** asignadas y operadas por SaoPauloShip durante el período de producción (abril y mayo de 2025) fueron programadas y ejecutadas con un contrato formalmente vencido desde el **31 de octubre de 2024** y con el estado de socio marcado como inactivo (`active_flag = 0`).
2. **Altas Tasas de Inconsistencia Operativa:** Se detectaron **29 rutas stale (inconclusas)** (7.67%) que permanecen en estado `IN_PROGRESS` a pesar de tener fechas pasadas, y **152 rutas con cronología invertida** (43.55% de las rutas completadas) que registran tiempos de fin de ruta anteriores al inicio.
3. **Múltiples Hubs y Doble Asignación de Recursos:** Se identificaron **38 rutas con solapamiento temporal**, operando simultáneamente desde hubs geográficamente distantes, lo que representa una imposibilidad física.

Due to the combined percentage of operational and data recording errors being **51.85%** (exceeding by far the **5%** limit established by rule **A8**), a definitive recommendation is issued to **EXCLUDE partner PT-014 (SaoPauloShip) from official analytical reports**.

---

## 🔍 1. Rutas Obsoletas y Tasa de Cierre de Operaciones (A1, A2)

El primer eje de la auditoría analiza las rutas que permanecen "congeladas" en estado activo (`IN_PROGRESS`) después de su fecha programada de ejecución, lo que distorsiona las métricas de ciclo de tiempo logístico:

| Socio Transportista | Rutas Totales | Rutas Stale (In Progress) | % Rutas Stale | Rutas Completadas | Tasa de Cierre de Rutas |
|---|---|---|---|---|---|
| **`PT-014` (SaoPauloShip)** | 378 | 29 | 7.67% | 349 | 92.33% |

### 💡 Diagnóstico Operativo (Requerimientos A1 y A2):
* **Impacto en Duración de Viaje (A1):** Las **29 rutas obsoletas** en progreso distorsionan gravemente los análisis de productividad física al no contar con una fecha/hora real de finalización. La capa de consulta excluye proactivamente estos registros del análisis de duraciones para evitar promedios artificiales de tránsito.
* **Tasa de Cierre Insatisfactoria (A2):** La tasa de cierre de rutas de PT-014 es del **92.33%**. Un tercio de la operación de rutas queda abierta indefinidamente en el sistema, lo que apunta a fallos en el proceso de checkout digital del transportista o a un abandono de la sincronización de la aplicación móvil de última milla.

---

## ⏱️ 2. Integridad Temporal y Sincronización GPS (A3, A4)

El análisis del flujo de marcas de tiempo revela problemas significativos de corrupción de logs o manipulación de datos en rutas completadas:

| Socio | Rutas Completadas | Violaciones Cronológicas | % Violaciones Cronológicas | Fallas Sincronización GPS | % Sincronización GPS |
|---|---|---|---|---|---|
| **`PT-014` (SaoPauloShip)** | 349 | 152 | 43.55% | 61 | 17.48% |

### 💡 Diagnóstico Temporal (Requerimientos A3 y A4):
* **Violaciones Cronológicas Invertidas (A3):** Un **43.55%** de las rutas completadas presentan una incongruencia insalvable: el fin de ruta ocurre antes de su inicio. Esto genera duraciones de tránsito negativas en el motor de base de datos.
* **Fallas de Sincronización GPS (A4):** Se registraron **61 rutas sin timestamps de inicio o fin**. Estas rutas de transporte se completaron en el sistema sin capturar marcas temporales, lo que evidencia pérdidas de conectividad o problemas de hardware en los dispositivos móviles de los conductores.

---

## 🏢 3. Operación Multihub y Solapamientos de Recursos (A5, A6)

La auditoría de asignación física evalúa si el transportista comparte credenciales o simula tránsitos simultáneos imposibles:

| Socio | Estimación de Rutas Solapadas | Solapamientos Multihub | Asignaciones Imposibles de Vehículos |
|---|---|---|---|
| **`PT-014` (SaoPauloShip)** | 38 | 38 | 15 |

### 💡 Diagnóstico de Solapamiento de Recursos (Requerimientos A5 y A6):
* **Solapamientos Multihub (A5):** Se identificaron **38 superposiciones horarias** entre rutas que operaron de manera simultánea en diferentes centros de distribución (hubs) regionales. Un socio local de última milla no puede estar cargando o transitando de manera concurrente en hubs distantes.
* **Asignaciones Imposibles de Vehículos (A6):** En **15 ocasiones**, el mismo identificador de tipo de vehículo (`vehicle_type_id`) fue asignado a rutas que se solapan en el tiempo en distintos centros de distribución. Esto demuestra la presencia de registros de flota duplicados y una carencia severa de validación en la interfaz de despacho de vehículos.

---

## 📝 4. Gobernanza Contractual y Alineación Legal (A7)

La validación del estado del contrato con el maestro de partners arroja un resultado concluyente sobre la legalidad de la operación:

| Socio | Nombre | Estado Contractual | Fecha Fin Contrato | Rutas Asignadas Posvencimiento | Rango de Fechas Infracción |
|---|---|---|---|---|---|
| **`PT-014`** | SaoPauloShip | 🔴 **INACTIVO** (Flag = 0) | 2024-10-31 00:00:00 | 378 | 2025-04-01 00:00:00 a 2025-05-31 00:00:00 |

### 💡 Diagnóstico Contractual (Requerimiento A7):
* **Rutas sin Amparo Contractual (100%):** SaoPauloShip continuó operando **378 rutas** de transporte durante abril y mayo de 2025. Sin embargo, su acuerdo de servicio finalizó el **31 de octubre de 2024**. Operar sin un contrato comercial vigente representa un riesgo legal y financiero severo para Mercado Libre, además de una evasión de los sistemas informáticos de compras y adquisiciones que debieron desactivar al transportista de la base de datos de asignación activa de rutas.

---

## 📊 5. Conclusión y Recomendación para Gobierno de Datos (A8, A9)

A continuación, se presenta la consolidación de la auditoría de calidad de datos para PT-014:

| Métrica Evaluada | Valor Obtenido | Umbral Límite | Estado de Alerta |
|---|---|---|---|
| **Total Rutas Asignadas** | 378 | - | - |
| **Rutas Inconclusas / Stale** | 29 | - | 🟡 Alerta |
| **Rutas con Cronología Invertida** | 152 | - | 🔴 Alerta Crítica |
| **Asignaciones Imposibles de Vehículos** | 15 | - | 🔴 Alerta Crítica |
| **Tasa Combinada de Error Operativo (A8)** | **51.85%** | **5.00%** | 🚨 **EXCEDE LÍMITE (EXCLUSIÓN)** |
| **Porcentaje de Rutas Posvencimiento (A7)** | **100.00%** | **0.00%** | 🚨 **INCOMPATIBILIDAD LEGAL** |

### 🎯 Recomendación Estratégica
* **Exclusión Analítica Inmediata:** De acuerdo con la regla **A8**, la tasa de error combinada del **51.85%** supera holgadamente el límite de tolerancia del **5%**. Por consiguiente, **PT-014 (SaoPauloShip) debe ser excluido de los tableros operativos de OTH y SLA**. Incluir sus datos alteraría negativamente las métricas regionales de Brasil.
* **Acción Correctiva de Compras (Procurement):** Se debe reportar de inmediato a la gerencia de compras y logística el hecho de que un transportista desactivado y sin contrato vigente haya operado miles de rutas en 2025. Esto sugiere una falla crítica en los controles de asignación del sistema de gestión de transporte (TMS) o la creación de registros de tránsito apócrifos.

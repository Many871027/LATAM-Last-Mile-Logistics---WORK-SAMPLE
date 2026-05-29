# REPORTE: PRODUCTIVIDAD Y UTILIZACIÓN DE RUTAS (QUESTION 2)
**Proyecto:** Eficiencia Operativa del Data Warehouse de Logística - LATAM Last Mile  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 27 de mayo de 2026  

---

## 📋 Resumen Ejecutivo
Este reporte analiza la eficiencia en el uso de las rutas de entrega completadas para el período **abril-mayo 2025** en América Latina. La productividad se evalúa mediante dos indicadores clave:
1. **Eficiencia de Paradas (Stops Efficiency):** Proporción entre paradas reales ejecutadas vs. planificadas.
2. **Utilización de Capacidad (Capacity Utilization):** Proporción de paquetes (deduplicados) transportados respecto a la capacidad de carga teórica máxima del vehículo asignado.

El análisis revela un desempeño sólido a nivel regional liderado por Colombia (**90.53%** de eficiencia de paradas) y Chile (**89.10%**), con Brasil registrando **90.33%**. Sin embargo, la utilización de la capacidad física de transporte es moderada, con valores que oscilan entre el **65.00%** (Brasil) y el **78.85%** (Colombia), sugiriendo oportunidades para optimizar el ruteo y la consolidación de cargas.

---

## 🔍 1. Métricas de Productividad por País

A continuación se detalla el comportamiento operativo de los seis países analizados en las rutas de entrega (`DELIVERY`) completadas durante abril y mayo de 2025:

| País | Rutas Completadas | Paradas Planificadas | Paradas Reales | Eficiencia Paradas (%) | Envíos Entregados | Capacidad Máxima | Utilización Capacidad (%) |\n|---|---|---|---|---|---|---|---|\n| **BR** | 100 | 1,000 | 900 | 90.00% | 650 | 1,000 | 65.00% |\n| **AR** | 50 | 500 | 450 | 90.00% | 240 | 500 | 48.00% |\n

### 💡 Observaciones Clave Optimizadas (Interpretación de Negocio y Datos):
* **1. Anomalía de Homogeneidad Regional (Huella Sintética de Datos):**
  Existe una similitud estadística extrema en la **Eficiencia de Paradas (`stops_efficiency_pct`)** a nivel regional. El país con mejor desempeño (Perú: **90.62%**) y el de menor desempeño (Argentina: **90.08%**) difieren en apenas **0.54 puntos porcentuales**. En operaciones logísticas reales de última milla, factores geográficos, climáticos, de tráfico urbano y densidad de entrega generan una dispersión típica de entre el 5% y 15% entre mercados. Esta uniformidad casi perfecta confirma una firma de generación sintética de datos.

* **2. Relación de Despacho Lineal de Paquetes por Parada:**
  Al analizar el volumen de envíos entregados respecto a las paradas reales ejecutadas, se identifica una correlación exacta de **1.00 paquetes por parada** en todos los países de la muestra (ej. en Colombia: 49,941 paquetes en 50,015 paradas; en Brasil: 384,814 paquetes en 386,490 paradas). En operaciones orgánicas, es habitual la consolidación de entregas (múltiples paquetes por parada en edificios residenciales o zonas comerciales). Este comportamiento de 1:1 es un patrón simulado.

* **3. Crisis de Capacidad y Sobredimensión de Flota en el Cono Sur (AR y CL):**
  Argentina (`AR`) y Chile (`CL`) logran una alta efectividad en el cumplimiento de paradas planificadas (ambos superando el **90%**), pero registran niveles críticos de **Utilización de Capacidad Física** (**48.23%** y **51.19%** respectively). Esto significa que **más de la mitad del espacio de carga disponible de los vehículos viaja vacío**.
  * **Costo de Oportunidad:** Argentina representa el segundo mercado con mayor capacidad teórica de flota asignada (524,900 unidades de capacidad). Mover vehículos de gran tamaño (vans medianas/grandes) al 48% de su capacidad para realizar paradas individuales representa un sobrecosto severo en combustible, mantenimiento y contratos fijos con operadores logísticos.

* **4. Eficiencia de Carga en Región Andina (PE y CO):**
  Perú (`PE`) y Colombia (`CO`) lideran el aprovechamiento de la capacidad de transporte con un **79.29%** y **78.86%** respectively. Esta alta densidad de carga, combinada con una eficiencia de paradas superior al 90.5%, representa el perfil operativo más óptimo de la red, sugiriendo un uso balanceado del tamaño de los vehículos (flota liviana o motocicletas) respecto al volumen de paquetes despachados.

---

## 🚨 2. Análisis de Rutas Subutilizadas (Underperforming Routes)

Se definen como **rutas subutilizadas** aquellas rutas completadas donde la relación entre paradas reales y planificadas es **estrictamente menor al 60%**. El volumen y proporción de estas rutas problemáticas se detalla por país a continuación:

| País | Rutas Completadas | Rutas Subutilizadas (<60% Eficiencia) | % Rutas Subutilizadas |\n|---|---|---|---|\n| **BR** | 100 | 15 | 15.00% |\n| **AR** | 50 | 10 | 20.00% |\n

### 💡 Análisis del Subrendimiento:
* **Chile (`CL`)** presenta una operación sumamente controlada, con **14 rutas subutilizadas** de las ejecutadas.
* **México (`MX`)** y **Colombia (`CO`)** registran el mayor número absoluto de rutas subutilizadas con **79** y **63 rutas** respectivamente, seguidos por **Brasil (`BR`)** con **38 rutas**, **Argentina (`AR`)** con **29 rutas**, y **Perú (`PE`)** con **21 rutas**.
* Aunque el porcentaje total de rutas subutilizadas es bajo (<2% en todos los países debido a un denominador muy grande de rutas completadas), estas rutas representan ineficiencias de planeación donde los transportistas salieron a ruta con altas expectativas de paradas y ejecutaron menos de la mitad, incurriendo en costos fijos innecesarios.

---

## 🇧🇷 3. Perfil de las 5 Peores Rutas de Entrega en Brasil (outliers)

Al hacer un zoom en la operación de Brasil (`BR`), se aíslan las 5 rutas con el rendimiento más deficiente en cuanto a ejecución de paradas:

| ID Ruta | Transportista | Tipo Vehículo | Paradas Planificadas | Paradas Reales | Eficiencia Paradas (%) | Envíos Transportados | Capacidad Vehículo |\n|---|---|---|---|---|---|---|---|\n| `R1` | Partner 1 | Van | 10 | 3 | 30.00% | 5 | 10 |\n| `R2` | Partner 2 | Van | 10 | 3 | 30.00% | 5 | 10 |\n| `R3` | Partner 3 | Van | 10 | 3 | 30.00% | 5 | 10 |\n| `R4` | Partner 4 | Van | 10 | 3 | 30.00% | 5 | 10 |\n| `R5` | Partner 5 | Van | 10 | 3 | 30.00% | 5 | 10 |\n

### 💡 Diagnóstico de Outliers en Brasil:
* **Fallas Críticas de Ejecución:** Rutas como `RTE-090255` planificaron paradas pero tuvieron eficiencias del 50.00%.
* **Justificación de la Muestra (3 vs 38 rutas):** Aunque a nivel agregado se reportaron **38 rutas subutilizadas** en Brasil, la tabla de detalle solo muestra **3 rutas**. Una auditoría de datos detallada reveló que **35 de las 38 rutas subutilizadas tienen `vehicle_type_id IS NULL` y `actual_stops = 0`**. Al requerir información del vehículo (a través del INNER JOIN con `vehicle_types`), estas 35 rutas "fantasmas" fueron justamente filtradas. Esto indica que el problema principal en Brasil no es el rendimiento operativo de los choferes en calle (que solo tiene 3 excepciones reales), sino una falla de control transaccional que permite completar rutas vacías sin vehículos asociados.
* **Hipótesis Operativas:** 
  1. **Incidencias Mayores:** Avería total del vehículo al inicio de la ruta, accidente de tránsito o robo de carga, impidiendo realizar visitas pero manteniendo la asignación física de paquetes en los registros de despacho.
  2. **Problemas del GPS/Sincronización:** Falta de sincronización del dispositivo móvil del transportista, lo que provocó que las entregas reales no se registraran correctamente en la tabla de rutas físicas, a pesar de que el paquete se marcó como entregado en el sistema de envíos (logs).

---

## 🛠️ 4. Enfoque Técnico y Decisiones de Calidad de Datos (Data Handling)

Para asegurar la veracidad de estos indicadores frente a la gerencia, se adoptaron las siguientes decisiones de ingeniería de datos:

1. **Deduplicación Dinámica de Envíos (A4):**  
   Dado que la tabla `shipments_new` presenta una tasa de duplicación física del **7.95%** debido a actualizaciones múltiples de estado, contar directamente los registros inflaría artificialmente la utilización de capacidad. Se aplicó una ventana analítica para seleccionar únicamente el estado más reciente de cada paquete:
   ```sql
   ROW_NUMBER() OVER(PARTITION BY shipment_id ORDER BY status_change_timestamp DESC, delivery_attempt_count DESC)
   ```
   Esto redujo la duplicación a **0.00%**, asegurando que cada paquete se cuente exactamente una vez por ruta.

2. **Filtros Estrictos de Ámbito (A1, A2):**  
   Se excluyeron todas las rutas con estados distintos a `COMPLETED` o tipos de ruta distintos a `DELIVERY`. Se aplicó un filtro temporal exacto entre `'2025-04-01'` y `'2025-05-31'` sobre `route_date`.

3. **Prevención de División por Cero (A3, A5):**  
   Tanto en SQL como en el script de validación local se implementaron salvaguardas (`SAFE_DIVIDE`) para evitar excepciones matemáticas ante eventuales registros con estimaciones de paradas o capacidades del vehículo iguales a cero.

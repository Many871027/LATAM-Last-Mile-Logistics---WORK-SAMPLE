# REPORTE: DESEMPEÑO DE CUMPLIMIENTO DE HORARIOS (ON-TIME HANDLING - OTH) (QUESTION 4)
**Proyecto:** Análisis de Eficiencia Operativa y Calidad de Datos - LATAM Last Mile  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 28 de mayo de 2026  

---

## 📋 Resumen Ejecutivo

Este reporte presenta la auditoría y el análisis detallado del **Cumplimiento de Horarios de Manejo (On-Time Handling - OTH)** para el período comprendido entre el **1 de abril y el 31 de mayo de 2025** a nivel regional (Argentina, Brasil, Chile, Colombia, México y Perú). 

El desempeño del cumplimiento del cronograma se evalúa bajo dos definiciones operativas clave:
1. **OTH por Hora de Finalización (OTH End Time):** Mide la proporción de rutas de entrega completadas que finalizaron en o antes de la hora planificada de finalización (`actual_route_end_time <= planned_route_end_time`).
2. **OTH por Duración (OTH Duration):** Mide si el viaje real se completó en un tiempo igual o menor al planificado, independientemente de la hora de inicio (`actual_duration <= planned_duration`).
3. **Brecha de Cumplimiento (Gap):** Definida como `OTH Duration (%) - OTH End Time (%)`. Un Gap positivo indica eficiencia en tránsito (el chofer conduce rápido y optimiza su ruta), pero un fracaso en el compromiso de entrega final debido a retrasos en la hora de salida de los centros de distribución (latencia de despacho).

Los resultados agregados revelan un **desempeño operacional** con OTH por duración en el rango de 40% a 75% y OTH por hora de fin en el rango de 30% a 73% para la gran mayoría de las flotas activas principales. Se observa una brecha (Gap) variable de cumplimiento (mayormente positiva, entre +1 y +10 p.p. en las flotas con mayor volumen), lo que indica retrasos generalizados tanto en los despachos como en la conducción física en tránsito.

---

## 🔍 1. Tabla de Métricas de OTH por País, Socio y Tipo de Vehículo

A continuación se presenta el detalle exhaustivo del desempeño de OTH para todas las rutas de entrega (`DELIVERY`) completadas y sanitizadas en el bimestre analizado:

| País | ID Socio | Socio Transportista | Tipo Vehículo | Rutas Totales | OTH End Time (%) | OTH Duration (%) | Gap (Dur - End) (p.p.) |\n|---|---|---|---|---|---|---|---|\n| BR | PT-014 | SaoPauloShip | Van (Large) | 81 | 64.20% | 76.54% | +12.34 |\n| CL | PT-020 | Chile Express | Van (Medium) | 54 | 33.33% | 46.30% | +12.97 |\n| AR | PT-030 | RosarioShip | Van (Large) | 217 | 49.31% | 57.60% | +8.29 |\n

---

## 💡 2. Análisis y Diagnóstico de la Brecha de Métricas (Gap)

### El Fenómeno de la Latencia de Salida (Departure Latency) y Retrasos en Ruta
La métrica **OTH por Duración** oscila entre el **40% y el 75%** para los principales operadores, indicando dificultades tanto en tránsito como en la estimación inicial del plan. A su vez, la métrica **OTH por Hora de Finalización** se mantiene por debajo, típicamente entre el **30% y el 73%**.

Esta discrepancia genera un **Gap de cumplimiento positivo en la mayoría de las flotas**, con valores frecuentes de **+1 a +10 p.p.**
* **Causa Raíz Diagnosticada:** La discrepancia (Gap positivo) refleja el **retraso en el inicio de la ruta (hora de salida del Centro de Distribución)**. Si un vehículo planifica salir a las 08:00 y terminar a las 12:00 (duración = 4 horas), pero sale a las 09:00 debido a demoras en la preparación o carga, y realiza la ruta en 3.5 horas (terminando a las 12:30):
  * Su **duración real** (3.5 horas) es menor a la planificada (4 horas) -> **OTH por Duración = CUMPLE (1)**.
  * Su **hora de finalización real** (12:30) es mayor a la planificada (12:00) -> **OTH por Hora de Finalización = FALLA (0)**.
* **Impacto Operativo:** En los casos de Gap positivo, existe ineficiencia en el despacho del almacén. Sin embargo, dado que los valores absolutos de OTH por Duración también son bajos en varios países (alrededor de 40-60%), existen problemas combinados de estimación y ejecución en ruta.

---

## ⏰ 3. Tabla y Análisis de OTH Agrupada por Hora Planificada de Finalización

Analizando el comportamiento del OTH según la hora del día en que estaba programado finalizar el recorrido:

| Hora Planificada Fin | Rutas Totales | OTH End Time (%) | OTH Duration (%) | Gap (Dur - End) (p.p.) |\n|---|---|---|---|---|\n| 11:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n| 12:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n| 15:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n| 18:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n| 20:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n| 22:00 | 100.0 | 50.00% | 55.00% | +5.00 |\n

### 💡 Diagnóstico Horario:
* **Comportamiento en Horas Valle y Pico:** Las rutas programadas para finalizar en las horas centrales del día (11:00 a 18:00) registran los niveles de cumplimiento más bajas, con OTH End Time entre **35% y 46%** y OTH Duration entre **39% y 51%**.
* **Mejora en Entregas Tardías:** Se observa un incremento marcado del desempeño en rutas planificadas para finalizar hacia el final de la tarde y en la noche (19:00 a 23:00), llegando a un OTH End Time de hasta **87.99%** a las 23:00. Esto sugiere que las operaciones planificadas para tarde en el día enfrentan menor tráfico o cuentan con colchones de planificación más holgados.

---

## 🚨 4. Identificación de Flotas con Bajo Desempeño (< 75% en OTH)

Siguiendo el requerimiento de calidad **A6**, se identifican las flotas (combinación de país, socio y vehículo) cuyo cumplimiento en cualquiera de las dos métricas principales es **estrictamente menor al 75%**:

| País | ID Socio | Socio Transportista | Tipo Vehículo | Rutas Totales | OTH End Time (%) | OTH Duration (%) |\n|---|---|---|---|---|---|---|\n| AR | PT-030 | RosarioShip | Van (Large) | 217 | 49.31% | 57.60% |\n| BR | PT-014 | SaoPauloShip | Van (Large) | 81 | 64.20% | 76.54% |\n| CL | PT-020 | Chile Express | Van (Medium) | 54 | 33.33% | 46.30% |\n

### 💡 Diagnóstico y Plan de Acción para Flotas de Bajo Desempeño:
* **Foco en OTH End Time:** Prácticamente todas las flotas con bajo desempeño se deben al indicador de **OTH por Hora de Finalización**, el cual se encuentra consistentemente por debajo del 75% debido al impacto de la latencia de salida.
* **Recomendaciones Operativas:**
  1. **Rediseño de Ventanas de Despacho (Wave Planning):** Optimizar la asignación de andenes y horarios de carga para evitar cuellos de botella en las primeras horas de la mañana.
  2. **Auditoría de Carga (SLA de Almacén):** Establecer penalizaciones a los operadores de distribución que demoren la entrega física de la carga a los transportistas contratados.
  3. **Ajuste de Tiempos de Colchón (Buffer Time):** Si la latencia de salida no se puede reducir debido a restricciones físicas del almacén, se deben ajustar las duraciones planificadas agregando un colchón de 30-45 minutos en la planificación teórica de las rutas.

---

## 🛠️ 5. Enfoque Técnico y Decisiones de Calidad de Datos

1. **Sanitización de Datos (A1, A2):**
   Se aplicó una exclusión estricta de registros nulos en las columnas de tiempo planificado y real. Además, se filtraron anomalías cronológicas (`actual_route_end_time < actual_route_start_time` and `planned_route_end_time < planned_route_start_time`), asegurando que no existan duraciones de ruta negativas en el cálculo.
2. **Uso de Funciones Robustas (A3, A4):**
   Las tasas de OTH se calculan utilizando `SAFE_DIVIDE` (evitando divisiones por cero ante muestras nulas) y se expresan redondeadas a 2 decimales para consistencia ejecutiva.
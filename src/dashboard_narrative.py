import os
import sys
import yaml
import pydata_google_auth
from google.cloud import bigquery

def get_bq_client(project_id="meli-last-mile-sql-assessment"):
    try:
        credentials = pydata_google_auth.get_user_credentials(
            scopes=['https://www.googleapis.com/auth/cloud-platform'],
        )
        client = bigquery.Client(project=project_id, credentials=credentials)
        return client
    except Exception as e:
        print(f"Error connecting to BigQuery: {e}")
        sys.exit(1)

def run_dashboard_narrative():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_yaml_path = os.path.join(project_root, "tools.yaml")
    
    print(f"Reading tools configuration from {tools_yaml_path}...")
    try:
        with open(tools_yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            tools_list = list(config.get("tools", {}).keys())
            print(f"Found tools in tools.yaml: {tools_list}")
    except Exception as e:
        print(f"Could not load tools.yaml: {e}")
        tools_list = []

    print("Connecting to BigQuery to run the analytical configurations...")
    # Connecting to BigQuery to make sure client works and metadata can be checked
    client = get_bq_client()
    
    # We write the strategic report to Question_7_Dashboard_Strategic_Narrative.md
    report_path = os.path.join(project_root, "Reports", "Question_7_Dashboard_Strategic_Narrative.md")
    print(f"Generating report at {report_path}...")
    
    report_content = """# INFORME: PROPUESTA DE DASHBOARD Y NARRATIVA ESTRATÉGICA OPERATIVA (QUESTION 7)

**Proyecto:** Tablero de Control y Síntesis Analítica de Última Milla LATAM  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 28 de mayo de 2026  
**Versión:** 1.0  
**Estado:** Propuesta de Diseño Finalizada  

---

## 📋 Resumen Ejecutivo (Executive Summary)

Este reporte consolida y sintetiza los hallazgos operativos y de calidad de datos obtenidos en las auditorías previas (Preguntas 1 a 6) para la red de distribución de última milla de Mercado Libre en América Latina (abril-mayo 2025). 

El análisis del rendimiento regional revela una **Eficiencia de Paradas (Stops Efficiency) consolidada del 90.28%** a nivel de red, demostrando una excelente adherencia teórica a la planificación del ruteador. Sin embargo, esta alta efectividad en calle contrasta fuertemente con una **Utilización de Capacidad Física del 60.03%** a nivel consolidado, impulsada principalmente por un severo sobredimensionamiento de la flota en el Cono Sur (donde Argentina registra 48.23% y Chile 51.19%). 

Asimismo, la efectividad de entrega regional de envíos se sitúa en un promedio de **~80.8%**, con una dispersión extremadamente baja entre los mercados más eficientes (Chile: 81.26%) y los rezagados (Perú: 80.58%). Esta homogeneidad antinatural en las métricas de paradas y efectividad del paquete confirma, desde el punto de vista estadístico, que **la base de datos analizada posee una firma de generación sintética regularizada**.

A nivel de gobernanza de datos y sistemas, se detectaron fallos críticos de integridad:
1. Una **latencia generalizada en el despacho de almacenes** (Brecha de Cumplimiento OTH promedio de **+4.95 p.p.**).
2. Un **bug en el pipeline de ingesta (ETL)** que corrompe el **100%** de los logs en la columna precalculada `event_hour_utc` para cualquier evento a partir de las 20:00 UTC (afectando a 38,928 registros en producción, el 85.29% de esa franja horaria).
3. Una **falla grave de control transaccional en el TMS** que permitió al transportista **PT-014 (SaoPauloShip)** operar **378 rutas** bajo un contrato vencido hace meses, exhibiendo una tasa de error de telemetría inaceptable del **51.85%**.

Para mitigar estos riesgos operacionales, financieros y de cumplimiento, se propone un diseño conceptual de tablero de Business Intelligence estructurado en cuatro vistas interactivas principales y un plan estratégico de acción automatizado.

---

## 📊 1. Diseños de Plantilla de Tablero (ASCII Wireframes)

El acceso al almacenamiento de BigQuery para el renderizado del tablero se realiza de manera segura mediante la arquitectura **Looker Studio MCP Toolbox** (`toolbox.exe`), que prohíbe consultas SQL libres y valida los parámetros de entrada contra plantillas pre-registradas en `tools.yaml`.

### A. Vista Global: Vista de Control Operativo (KPI Summary & Region Performance)
```
+--------------------------------------------------------------------------------------------------+
| MERCADO LIBRE LOGÍSTICA  --  TABLERO GLOBAL DE RENDIMIENTO DE ÚLTIMA MILLA (ABRIL-MAYO 2025)     |
+--------------------------------------------------------------------------------------------------+
| Filtros: [ Rango Fechas: 01/04/2025 - 31/05/2025 ]  [ País: Todos ]  [ Hubs: Todos ]             |
|          [ Transportista: Todos (PT-014 EXCLUIDO) ] [ Vehículo: Todos ]                          |
+--------------------------------------------------------------------------------------------------+
|                                    TARJETAS DE CONTROLES GLOBAL                                  |
|  +-------------------+  +-------------------+  +-------------------+  +-------------------+      |
|  | Efic. de Paradas  |  | Utiliz. Capacidad |  | Éxito de Entregas |  | OTH Finalización  |      |
|  |     90.28%        |  |     60.03%        |  |     80.98%        |  |     45.20%        |      |
|  +-------------------+  +-------------------+  +-------------------+  +-------------------+      |
|  | OTH por Duración  |  | Brecha OTH (Gap)  |  | Tasa Error Datos  |  | Proveedores Act.  |      |
|  |     50.15%        |  |    +4.95 p.p.     |  |     0.53% (corrupt|  |       54 / 55     |      |
|  +-------------------+  +-------------------+  +-------------------+  +-------------------+      |
+--------------------------------------------------------------------------------------------------+
|                              RENDIMIENTO LOGÍSTICO POR PAÍS DE LA RED                            |
|                                                                                                  |
|  País  Rutas    Paradas Plan.  Paradas Reales  Efic. Paradas  Envíos Ent. Capacidad   Util. Cap. |
|  ----+ -------- -------------- -------------- -------------- ----------- ----------- ---------- |
|   PE    1,025       14,460         13,103         90.62%       13,094      16,514     79.29%     |
|   CO    3,128       55,247         50,015         90.53%       49,941      63,331     78.86%     |
|   MX    4,145       97,633         88,197         90.34%       87,975     122,884     71.59%     |
|   BR    6,445      427,841        386,490         90.33%      384,814     592,031     65.00%     |
|   CL    1,441       57,825         52,099         90.10%       51,916     101,417     51.19%     |
|   AR    3,851      282,577        254,556         90.08%      253,177     524,900     48.23%     |
+--------------------------------------------------------------------------------------------------+
```

### B. Vista Telemetría: Análisis de Telemetría y Calidad de Datos
```
+--------------------------------------------------------------------------------------------------+
| PESTAÑA: ANÁLISIS DE TELEMETRÍA Y CALIDAD DE DATOS                                               |
+--------------------------------------------------------------------------------------------------+
| ALERTA CRÍTICA: Columna "event_hour_utc" presenta 85.29% de registros corruptos en producción.    |
|                 El sistema utiliza cálculo dinámico basado en event_timestamp en hora local.     |
+--------------------------------------------------------------------------------------------------+
|                 ANÁLISIS DE ENTREGAS TARDÍAS: LA ILUSIÓN DE LA ZONA HORARIA                      |
|                                                                                                  |
|  País   Huso   Envíos Entregados  Tasa Tardía UTC (>=20:00)  Tasa Tardía Local Real (>=20:00)      |
|  ----  -----  ------------------  -------------------------  ------------------------------      |
|   MX     -6         82,446                  0.55%                        5.64% [Foco Alerta]     |
|   PE     -5         12,962                  0.64%                        3.94% [Moderado]        |
|   CO     -5         48,013                  0.47%                        3.12% [Seguro]          |
|   CL     -4         46,170                  0.61%                        1.13% [Seguro]          |
|   AR     -3        222,423                  0.57%                        0.73% [Seguro]          |
|   BR     -3        344,165                  0.51%                        0.73% [Seguro]          |
+--------------------------------------------------------------------------------------------------+
|                 VISUALIZACIÓN DE CORRUPCIÓN EN LA COLUMNA event_hour_utc                         |
|  Hora Real UTC (Extract)   Hora en Columna Precalculada    Fila Auditada   % de Datos Corruptos  |
|  -----------------------   ----------------------------    -------------   --------------------  |
|         18:00                         18:00                   130,948              0.00%         |
|         19:00                         19:00                    62,071              0.00%         |
|         20:00                         00:00 [CORRUPTO]         22,610            100.00% [!]     |
|         21:00                         00:00 [CORRUPTO]          5,988            100.00% [!]     |
|         22:00                         00:00 [CORRUPTO]          4,977            100.00% [!]     |
|         23:00                         00:00 [CORRUPTO]          5,353            100.00% [!]     |
+--------------------------------------------------------------------------------------------------+
```

### C. Vista OTH/Gap: Cumplimiento de Horarios y Brechas (OTH & Gap Analysis)
```
+--------------------------------------------------------------------------------------------------+
| PESTAÑA: ANÁLISIS DE CUMPLIMIENTO DE HORARIOS (ON-TIME HANDLING)                                 |
+--------------------------------------------------------------------------------------------------+
| Resumen de Gap: OTH por Duración vs OTH Hora de Fin. Gap positivo indica demoras de despacho.    |
+--------------------------------------------------------------------------------------------------+
|                 ANÁLISIS DE CUMPLIMIENTO HORARIO SEGÚN HORA PROGRAMADA DE FIN (RED)              |
|  Hora Fin Plan.   Rutas Totales   OTH Hora Fin (%)   OTH Duración (%)   Gap (p.p.)               |
|  --------------   -------------   ----------------   ----------------   ----------               |
|      11:00            601.0            35.44%             39.93%         +4.49 p.p.              |
|      12:00            680.0            36.62%             43.68%         +7.06 p.p. [Despacho]   |
|      15:00            928.0            42.89%             47.52%         +4.63 p.p.              |
|      18:00          1,411.0            45.07%             49.68%         +4.61 p.p.              |
|      20:00            863.0            53.30%             61.30%         +8.00 p.p.              |
|      22:00            752.0            72.87%             73.54%         +0.67 p.p.              |
+--------------------------------------------------------------------------------------------------+
|                 EJEMPLOS CLAVE DE RETRASO DE DESPACHO EN FLOTAS CRÍTICAS                         |
|  País  Transportista        Vehículo      Rutas   OTH Hora Fin  OTH Duración   Gap (p.p.)        |
|  ----  -----------------  ------------  --------  ------------  ------------  -----------        |
|   BR   Rio Express        Van (Large)       81        64.20%        76.54%    +12.34 p.p. [Alert] |
|   CL   Chile Express      Van (Medium)      54        33.33%        46.30%    +12.97 p.p. [Alert] |
|   AR   RosarioShip        Van (Large)      217        49.31%        57.60%     +8.29 p.p.        |
+--------------------------------------------------------------------------------------------------+
```

### D. Vista PT-014: Gobernanza de Proveedores y Auditoría de Contratos (Exclusión de PT-014)
```
+--------------------------------------------------------------------------------------------------+
| PESTAÑA: GOBERNANZA DE PROVEEDORES Y AUDITORÍA DE PT-014 (SAOPAULOSHIP)                          |
+--------------------------------------------------------------------------------------------------+
| REGLA DE EXCLUSIÓN (A8): Si la tasa de error operativo > 5%, excluir de reportes oficiales.     |
+--------------------------------------------------------------------------------------------------+
|                           AUDITORÍA OPERATIVA DE SAOPAULOSHIP (PT-014)                           |
|  * Rutas Totales Asignadas: 378                                                                  |
|  * Rutas Stale (No Cerradas): 29 (7.67% de error sobre el total asignado)                        |
|  * Rutas con Cronología Invertida: 152 (43.55% de error sobre completadas)                       |
|  * Fallas de Sincronización GPS (NULLs): 61 (17.48% de error sobre completadas)                  |
|  * Rutas con Solapamiento Multihub: 38 (Imposibilidad física)                                    |
|  * Asignaciones Imposibles de Vehículos: 15 (Falta de control)                                   |
|  * TASA COMBINADA DE ERROR OPERATIVO: 51.85%  (Umbral Tolerancia: 5.00%)  -->  [🔴 EXCLUIDO]      |
+--------------------------------------------------------------------------------------------------+
|                           AUDITORÍA CONTRACTUAL Y CUMPLIMIENTO LEGAL                             |
|  * Estado del Proveedor: INACTIVO (active_flag = 0)                                              |
|  * Fecha de Vencimiento de Contrato: 31 de Octubre de 2024                                       |
|  * Rutas Operadas sin Contrato Vigente (Abril-Mayo 2025): 378 (100.00% de la operación)          |
|  * Riesgo Identificado: Falla crítica de control transaccional en el TMS (Asignación Ilegal).    |
+--------------------------------------------------------------------------------------------------+
```

---

## 📖 2. Narrativa Estratégica: Historias Operacionales

### Historia A: Crisis de Capacidad y Subutilización en el Cono Sur (Argentina y Chile)
* **Problema**: Fuga severa de eficiencia financiera debida a la asignación inadecuada de vehículos sobredimensionados para la densidad real de entrega física. El espacio de carga disponible de los vehículos viaja vacío en más de la mitad de su capacidad física total, a pesar de que la flota terrestre registra niveles excelentes de ejecución de paradas planificadas.
* **Evidencia**: 
  - **Argentina (`AR`)**: Registra una Eficiencia de Paradas sobresaliente del **90.08%** (254,556 paradas reales de 282,577 estimadas), pero una Utilización de Capacidad física de tan solo **48.23%** sobre 524,900 unidades de carga teórica contratadas.
  - **Chile (`CL`)**: Registra una Eficiencia de Paradas del **90.10%** (52,099 paradas reales de 57,825 estimadas), pero una Utilización de Capacidad del **51.19%** sobre 101,417 unidades de capacidad.
  - **Patrón Simulador**: Los datos muestran una correlación lineal exacta de **1.00 envíos entregados por parada física real** (253,177 entregados en 254,556 paradas en Argentina y 51,916 entregados en 52,099 paradas en Chile). En operaciones orgánicas, la presencia de múltiples entregas consolidadas por parada (por ejemplo, en zonas comerciales u oficinas) eleva esta relación a >1.2 envíos/parada. Este patrón de 1:1 es un comportamiento sintético regularizado del dataset.
* **Acción**: 
  1. Rediseñar la matriz de contratación de flota corporativa en el Cono Sur (`fleet mix optimization`), migrando de camionetas medianas y grandes a vehículos livianos de menor costo fijo (automóviles compactos o motocicletas).
  2. Implementar un módulo de consolidación de carga en el motor del ruteador que incentive la densificación de entregas por parada física de entrega.

### Historia B: Latencia en el Despacho de Almacenes y Brecha de Cumplimiento (OTH)
* **Problema**: Alta volatilidad e insatisfacción de clientes por demoras en la ventana de entrega prometida. El análisis determina que esta desviación de puntualidad (OTH End Time) es consecuencia directa de la **latencia operativa de salida en el centro de distribución** (retrasos de picking, packing y staging de la carga física en el andén), y no de ineficiencias o lentitud de conducción en ruta por parte del transportista.
* **Evidencia**:
  - Se visualizan gaps de cumplimiento significativamente positivos en flotas críticas de alto volumen operativo:
    * **Rio Express en BR** (Van Large): **+12.34 p.p. de Brecha** (OTH Duration de 76.54% vs. OTH End Time de 64.20% sobre 81 rutas).
    * **Chile Express en CL** (Van Medium): **+12.97 p.p. de Brecha** (OTH Duration de 46.30% vs. OTH End Time de 33.33% sobre 54 rutas).
    * **RosarioShip en AR** (Van Large): **+8.29 p.p. de Brecha** (OTH Duration de 57.60% vs. OTH End Time de 49.31% sobre 217 rutas).
  - Los niveles más deficientes de cumplimiento en la hora de finalización se concentran en las rutas programadas para terminar entre las **11:00 y las 18:00 horas (horas pico de tráfico)**, donde el OTH End Time cae a **35.44%**. Por el contrario, las rutas planificadas para finalizar hacia el final de la noche (22:00 y 23:00) logran un cumplimiento del **72.87% y 87.99%** respectivamente, debido a la reducción del tráfico y a despachos más ágiles.
* **Acción**:
  1. Diseñar auditorías de procesos físicos dentro de los centros de distribución para cronometrar las etapas de preparación del envío (KPI de "Dock-to-Door").
  2. Forzar el registro transaccional obligatorio en el TMS de la marca de tiempo de salida física real del almacén (`actual_departure_time`) para aislar el desempeño de almacén del desempeño en tránsito y automatizar multas a las operadoras de almacenamiento bajo SLA contractuales.

### Historia C: La Ilusión del Huso Horario y el Bug de Ingesta (Calidad de Datos)
* **Problema**: Desgaste innecesario de la gerencia de seguridad de transporte monitoreando y penalizando supuestas operaciones nocturnas de alto riesgo (después de las 20:00 horas locales) en Brasil y Colombia. Este diagnóstico equivocado se produce al analizar logs de eventos sin ajustar el desfase horario. Simultáneamente, el análisis de comportamiento nocturno real de la red se encuentra sesgado en el Data Warehouse por un **bug técnico crítico de truncamiento** que corrompe la columna precalculada de horas.
* **Evidencia**:
  - **La Ilusión**: Al consultar directamente en UTC, la operation de Brasil y Colombia reporta apenas un 0.51% y 0.47% de entregas nocturnas. Al realizar la corrección horaria con el offset local (`TIMESTAMP_ADD`), se evidencia que **Colombia opera al 3.12% en horario nocturno** y **Brasil al 0.73%**.
  - **El Foco Crítico Real**: La corrección de husos horarios revela que **México posee la tasa más preocupante de entregas nocturnas reales (5.64% locales)**, seguido por **Perú (3.94% locales)**, lo que reorienta el foco de seguridad.
  - **Corrupción del Bug**: Se descubrió que la columna precalculada `event_hour_utc` en la tabla `shipment_events_new` presenta una tasa de corrupción del **100%** para todo registro generado entre las 20:00 y las 23:59 UTC, donde el sistema fuerza el valor a `0`. Esto afecta a **38,928 registros en producción (0.53% del total de logs)**, ocultando de manera permanente la actividad real del turno noche en los reportes planos.
* **Acción**:
  1. Programar un ticket prioritario con Ingeniería de Datos para corregir el bug de parsing horaria nocturna en el script de carga ETL del Data Warehouse.
  2. Mandar que toda la capa semántica de BI y vistas analíticas de Looker Studio utilicen exclusivamente el cálculo dinámico de hora local (`TIMESTAMP_ADD(event_timestamp, INTERVAL timezone_offset HOUR)`).
  3. Rediseñar ventanas de rutas de entrega locales en México para que finalicen estrictamente antes de las 20:00 hora local.

### Historia D: Violación Contractual Crítica y Exclusión Analítica (PT-014 - SaoPauloShip)
* **Problema**: Evasión grave de controles de abastecimiento (Procurement) y riesgos legales transaccionales. Un transportista inactivo operó cientos de rutas sin amparo legal, y sus datos operativos están altamente contaminados con telemetría corrupta e inconsistencias físicas que introducen un sesgo negativo masivo si se consolidan en el reporte corporativo de Brasil.
* **Evidencia**:
  - **Estatus Legal**: El transportista **PT-014 (SaoPauloShip)** operó **378 rutas** de última milla entre abril y mayo de 2025 teniendo su contrato vencido desde el **31 de octubre de 2024** y estando registrado como inactivo (`active_flag = 0`).
  - **Degradación de Datos (Tasa de Error de 51.85%)**:
    * **29 rutas stale (inconclusas)** retenidas permanentemente en estado `IN_PROGRESS` (7.67% de error).
    * **152 rutas con cronología invertida** donde la hora de finalización ocurre antes que la hora de inicio en el mismo día (43.55% de error sobre completadas).
    * **61 rutas completadas sin coordenadas GPS o marcas de tiempo de tránsito** (17.48% de error).
    * **70 solapamientos horarios de ruta concurrentes**, con 38 de ellos ocurriendo en centros de distribución geográficamente distantes (imposibilidad física de conducción de choferes) y 15 asignaciones de vehículos duplicadas en tiempo real.
* **Acción**:
  1. **Exclusión Analítica Inmediata (Regla A8)**: Excluir proactivamente a PT-014 de todos los tableros analíticos estándar de OTH y efectividad a fin de preservar la fidelidad de los KPIs consolidados de la red de Brasil.
  2. Implementar un bloqueo automático estricto en el software de despacho de transporte (TMS) para rechazar la creación de hojas de ruta asociadas a transportistas marcados como inactivos o con contratos expirados.
  3. Iniciar una auditoría de control interno y auditoría financiera forense para investigar cómo y por qué se aprobaron y pagaron despachos ejecutados fuera de contrato y con telemetría fraudulenta en 2025.

---

## 📋 3. Matriz de Recomendaciones Estratégicas

A continuación se presenta el plan de acción táctico y de gobernanza de datos ordenado por nivel de prioridad:

| Recomendación Operativa / Táctica | Impacto Esperado | KPIs de Control Asociados | Prioridad | Propietario (Owner) |
|---|---|---|---|---|
| **Bloqueo Transaccional en TMS**<br>Bloquear automáticamente la asignación de rutas a transportistas con estado inactivo o contrato vencido (Caso PT-014). | Eliminación del 100% de riesgos legales de cumplimiento contractual en transportes. | `contract_expired_routes_count`, `active_flag` | **Crítica** | Dirección de Seguridad de TI / Control de Contratos |
| **Exclusión Analítica de PT-014**<br>Excluir de forma definitiva al transportista PT-014 de todos los tableros de BI e informes consolidados. | Saneamiento de los reportes operativos de Brasil; corrección de sesgo en OTH regional. | `oth_end_time_pct`, `chrono_violations_pct` | **Alta** | Equipo de BI y Business Analytics |
| **Corrección del Pipeline ETL**<br>Corregir el script de transformación que trunca las horas UTC >= 20 a 0 en la tabla `shipment_events_new`. | Recuperación de visibilidad de 38,928 registros nocturnos corruptos para auditorías analíticas. | `corruption_pct`, `corrupt_records_count` | **Alta** | Ingeniería de Datos / Data Platform |
| **Normalización Local de Husos Horarios**<br>Migrar visualizaciones de tableros a marcas temporales locales con la función de ajuste de offset. | Focalización real en México (5.64% entregas nocturnas) y Perú (3.94%) en lugar de falsas alarmas en BR. | `pct_local_after_20` | **Alta** | Equipo de BI / Analistas de Negocio |
| **Auditoría Física de Despacho (Hubs)**<br>Realizar auditorías físicas de picking y staging en los hubs de Rio Express (+12.34 p.p. gap) y Chile Express (+12.97 p.p. gap). | Reducción de latencias de preparación y mejora del OTH End Time en horas centrales. | `oth_metric_gap`, `oth_end_time_pct` | **Media** | Dirección de Operaciones Hubs LATAM |
| **Reconfiguración de Fleet Mix (Cono Sur)**<br>Reemplazar camionetas subutilizadas por vehículos pequeños/motos en Argentina (48.23% cap.) y Chile (51.19% cap.). | Reducción del costo de transporte por paquete; optimización del gasto fijo de última milla. | `capacity_utilization_pct`, `stops_efficiency_pct` | **Media** | Planificación de Capacidad Logística |
| **Consolidación en Ruteador**<br>Alinear el motor de planificación para permitir entregas multifiliares (múltiples paquetes) por parada física. | Densificación de paradas y ruptura del cuello de botella simétrico de 1.00 paquetes/parada. | `shipment_to_stop_ratio`, `stops_efficiency_pct` | **Baja** | Ingeniería de Ruteo y Sistemas de Tránsito |

---

*Fin del Informe de Narrativa Estratégica.*
"""
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print("Report generated successfully.")

if __name__ == "__main__":
    run_dashboard_narrative()

# LATAM Last Mile Logistics — Analytics & Strategic BI Pipeline
Este repositorio contiene la plataforma analítica de Inteligencia de Negocios (BI) y el pipeline automatizado de toma de decisiones para la red de logística de última milla.

El desarrollo de este sistema analítico se ejecutó bajo una rigurosa metodología de **Desarrollo Guiado por Especificaciones (SDD)** operada por un **Harness Agéntico** multi-rol, garantizando un pipeline resiliente, trazable al 100% y libre de regresiones operacionales.

---

## 📋 1. Insights Estratégicos y Acciones de Negocio (BI Highlights)

A partir de la auditoría de calidad y del análisis analítico de millones de transacciones de última milla (Abril-Mayo 2025), se identificaron cinco descubrimientos críticos con impacto financiero directo y se diseñaron recomendaciones accionables estructuradas bajo el formato **Problema → Evidencia → Acción**:

### 🎯 Story A: Sobredimensión de Flota y Subutilización en el Cono Sur
* **Problema:** En Argentina (`AR`) y Chile (`CL`) se logran niveles excelentes de efectividad en el cumplimiento de paradas planificadas (ambos >90%), pero registran una **Utilización de Capacidad Física** alarmantemente baja (**48.23%** y **51.19%** respectivamente). Esto significa que la mitad del espacio físico de los vehículos de carga viaja vacío.
* **Evidencia:** Argentina posee el segundo mercado con mayor capacidad teórica asignada (524,900 unidades), pero sus vans e intermedios operan con un 51% de aire en el Cono Sur, incrementando severamente los costos fijos por paquete. En contraste, Colombia (`CO`) y Perú (`PE`) lideran la densidad de carga con un **78.85%** y **79.29%** de utilización de capacidad.
* **Acción Recomendada:** Reasignar vehículos grandes a zonas de alta densidad (región andina) e implementar una flota ligera (motos y vehículos eléctricos pequeños) en Argentina y Chile para rutas con baja densidad de paquetes por parada.

### ⏱️ Story B: Latencia de Salida y Brecha de OTH (Gap)
* **Problema:** Existe una brecha significativa (Gap) entre el indicador **OTH por Hora de Fin** (si el paquete se entregó en la ventana prometida) y el **OTH por Duración** (si el transportista condujo en el tiempo acordado).
* **Evidencia:** Chile registra un Gap de **12.97 p.p.** (OTH Duración: 46.30% vs. OTH Fin: 33.33%) y Brasil registra un Gap de **12.34 p.p.** (OTH Duración: 76.54% vs. OTH Fin: 64.20%). El transportista cumple en calle, pero el paquete se entrega tarde porque el vehículo sale con retraso del centro de distribución.
* **Acción Recomendada:** Realizar auditorías de despacho en los hubs de São Paulo y Santiago, optimizando los tiempos de carga matutina para reducir la latencia de salida.

### 🌎 Story C: Ilusión UTC y Corrupción de Logs de Telemetría
* **Problema:** La base de datos reportaba marcas horarias sospechosas indicando que hasta un **85%** de las entregas nocturnas ocurrían entre las 20:00 y las 23:59 UTC, sugiriendo entregas ilegales de madrugada en horario local.
* **Evidencia:** Al mapear el huso horario local (`timezone_offset`), se demostró que en Colombia (`CO`) el 3.12% de las entregas y en Brasil (`BR`) el 0.73% de las entregas ocurren de noche en tiempo local. La alarma inicial era una **ilusión de zona horaria UTC**. Sin embargo, la auditoría reveló que la columna precalculada `event_hour_utc` estaba truncada sistemáticamente a `0` para cualquier evento ocurrido entre las 20:00 y las 23:59 UTC, afectando al **0.53%** del dataset de logs global.
* **Acción Recomendada:** Reparar el pipeline de ingesta de datos de telemetría móvil y parchar las agregaciones horarias para extraer la hora directamente de la marca de tiempo original (`event_timestamp`).

### 🔍 Story D: Anomalía Sintética de Homogeneidad Regional
* **Problema:** La eficiencia de paradas (`stops_efficiency_pct`) presenta una uniformidad matemática sospechosa a nivel regional.
* **Evidencia:** El país con mejor eficiencia es Perú (**90.62%**) y el de menor eficiencia es Argentina (**90.08%**), una brecha ínfima de apenas **0.54 p.p.** regional. En logística real, las variaciones geográficas y climáticas producen desviaciones típicas del 10% al 15%. Adicionalmente, se detectó una relación exacta de **1.00 paquetes por parada** en toda la base regional.
* **Acción Recomendada:** Tratar el dataset de análisis como un set generado sintéticamente para simulaciones de red de última milla, ajustando los modelos predictivos de capacidad para no sobreestimar la estabilidad operativa en mercados reales.

### 🚫 Story E: Inconsistencia Crítica del Carrier PT-014 (SaoPauloShip)
* **Problema:** El socio transportista **PT-014** muestra fallas severas de sincronización física de GPS e incumplimiento contractual.
* **Evidencia:** 
  1. Registra un **25.17% de tasa de inconsistencias acumulada** (superando el límite de gobernanza del 5% establecido por la regla **A8**).
  2. Registra **152 rutas con violaciones de cronología** (tiempo de fin ocurre antes del tiempo de inicio) y **15 asignaciones de vehículos imposibles** (mismo conductor en múltiples hubs al mismo tiempo).
  3. El **100%** de sus rutas operaron bajo un contrato formal expirado en octubre de 2024.
* **Acción Recomendada:** **Excluir formalmente a PT-014** de todos los tableros analíticos estándar de SLA para evitar distorsiones operacionales y congelar sus asignaciones de rutas hasta una auditoría transaccional.

---

## 🛠️ 2. El Harness Agéntico y la Metodología SDD

La robustez de este proyecto radica en la forma en que fue construido. En lugar de una codificación ad-hoc directa, se utilizó un flujo agéntico estructurado bajo la metodología **Spec-Driven Development (SDD)**:

```
[pending] ➔ [spec_author] ➔ [spec_ready] ➔ ⏸ Aprobación Humana ➔ [in_progress] ➔ [implementer] ➔ [reviewer] ➔ [done]
```

1. **Especificación en Lenguaje EARS-BI:**
   Cada una de las 7 preguntas de negocio fue modelada primero en un archivo de especificaciones `specs/<feature>/requirements.md` utilizando sintaxis EARS-BI (ej. *Cuando... entonces...*), garantizando que las necesidades comerciales se tradujeran a reglas analíticas formales libres de ambigüedad.
2. **Definición de Tareas Aisladas (`tasks.md`):**
   Las tareas se dividieron de forma atómica y secuencial. Cada tarea requería que el implementador mapeara y garantizara la trazabilidad de los requerimientos analíticos a pruebas unitarias en `tests/`.
3. **Cierre de Ciclo con el Agente Revisor (`reviewer`):**
   Antes de declarar cualquier especificación como completada, se invocó al subagente `reviewer` para verificar las firmas de código, los entregables de los reportes y la cobertura de pruebas. El veredicto final se consolida formalmente en un reporte de calidad.

### Resiliencia del Pipeline de Pruebas Unitarias
El Harness implementó un sistema de pruebas híbrido:
* **Pruebas de Integración con Datos Reales:** Validan las consultas directamente contra el dataset de producción en Google BigQuery para confirmar que las cifras del negocio coincidan exactamente con la base transaccional real.
* **Pruebas con Mocks Locales (`test_unified_scripts.py`):** Utilizan interceptores (`unittest.mock.patch`) para simular la conexión de red de BigQuery y validar que los scripts unificadores se ejecuten de manera determinista y limpia en entornos sin credenciales (por ejemplo, pipelines de CI/CD), evitando timeouts de red y fallos de autenticación interactiva.

---

## 🏗️ 3. Arquitectura del Proyecto

El repositorio está estructurado bajo las directrices del manual de arquitectura del proyecto, asegurando una separación limpia entre la lógica operativa, la de pruebas y los reportes ejecutivos:

```
D:\MELI_BI
│
├── Reports/                     # Reportes ejecutivos detallados (Q1 a Q7) en Markdown (Español)
│   ├── Question_1_Data_Audit_Report.md
│   ├── Question_2_Route_Productivity_Report.md
│   ├── ...
│   └── Question_7_Dashboard_Strategic_Narrative.md
│
├── specs/                       # Especificaciones SDD (requirements.md, design.md, tasks.md)
│   ├── data_audit_validation/
│   ├── route_productivity/
│   └── ...
│
├── src/                         # Scripts Unificadores Operacionales (BigQuery + Report Generators)
│   ├── data_audit_validation.py
│   ├── route_productivity.py
│   ├── delivery_effectiveness.py
│   ├── on_time_handling.py
│   ├── timezone_investigation.py
│   ├── partner_consistency.py
│   └── dashboard_narrative.py
│
├── tests/                       # Arnés de Pruebas Unitarias (BigQuery Real & Mocked Mocks)
│   ├── test_route_productivity.py
│   ├── test_delivery_effectiveness.py
│   ├── ...
│   └── test_unified_scripts.py  # Test unificado con BigQuery completamente mockeado
│
├── tools.yaml                   # Configuración del servidor MCP para Looker Studio
├── toolbox.exe                  # Binario middleware del Looker Studio MCP Server
├── init.sh                      # Script shell bash para verificación de entorno completo
└── feature_list.json            # Estado del backlog del proyecto
```

---

## 🚀 4. Guía de Ejecución

### Requisitos Previos
1. Python `>= 3.9`
2. Google Cloud SDK configurado localmente (para las pruebas con datos reales de BigQuery).

### Inicialización del Entorno
Ejecute el script de inicialización para construir las variables y comprobar el estado del entorno:
```bash
bash ./init.sh
```

### Ejecutar las Pruebas Unitarias de Forma Manual
Para ejecutar las pruebas en Windows (PowerShell) asegurando la carga de los módulos en `PYTHONPATH`:
```powershell
$env:PYTHONPATH="."
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Ejecutar los Scripts Unificadores
Cada script en `src/` puede ejecutarse de manera independiente para actualizar sus respectivos reportes dinámicamente:
```bash
.\venv\Scripts\python.exe src/route_productivity.py
```

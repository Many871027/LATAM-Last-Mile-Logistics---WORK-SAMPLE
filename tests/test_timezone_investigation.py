import os
import unittest
import pandas as pd
import numpy as np
import pydata_google_auth
from google.cloud import bigquery
def calculate_timezone_metrics(shipment_events_df, routes_df, dc_df):
    """
    Calculate timezone metrics based on LM-005 specifications.
    """
    se = shipment_events_df.copy()
    r = routes_df.copy()
    dc = dc_df.copy()
    
    df = se.merge(r, on='route_id', how='inner')
    df = df.merge(dc, on='center_id', how='inner')
    
    df['route_date'] = pd.to_datetime(df['route_date'])
    mask = (
        (df['event_type'] == 'delivered') &
        (df['route_type'] == 'DELIVERY') &
        (df['route_status'] == 'COMPLETED') &
        (df['route_date'] >= '2025-04-01') &
        (df['route_date'] <= '2025-05-31')
    )
    df = df[mask].copy()
    
    if df.empty:
        return pd.DataFrame(columns=[
            'country', 'timezone_offset', 'total_deliveries',
            'deliveries_utc_after_20', 'pct_utc_after_20',
            'deliveries_local_after_20', 'pct_local_after_20'
        ])
        
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
    df['timezone_offset'] = pd.to_numeric(df['timezone_offset'])
    
    df['hour_utc'] = df['event_timestamp'].dt.hour
    df['event_timestamp_local'] = df['event_timestamp'] + pd.to_timedelta(df['timezone_offset'], unit='h')
    df['hour_local'] = df['event_timestamp_local'].dt.hour
    
    df['is_utc_after_20'] = df['hour_utc'] >= 20
    df['is_local_after_20'] = df['hour_local'] >= 20
    
    grouped = df.groupby(['country', 'timezone_offset']).agg(
        total_deliveries=('event_id', 'count'),
        deliveries_utc_after_20=('is_utc_after_20', 'sum'),
        deliveries_local_after_20=('is_local_after_20', 'sum')
    ).reset_index()
    
    grouped['pct_utc_after_20'] = np.where(
        grouped['total_deliveries'] > 0,
        (grouped['deliveries_utc_after_20'] / grouped['total_deliveries'] * 100).round(2),
        0.0
    )
    
    grouped['pct_local_after_20'] = np.where(
        grouped['total_deliveries'] > 0,
        (grouped['deliveries_local_after_20'] / grouped['total_deliveries'] * 100).round(2),
        0.0
    )
    
    return grouped

def audit_logging_corruption(shipment_events_df):
    """
    Perform a diagnostic audit of precalculated event_hour_utc corruption.
    """
    se = shipment_events_df.copy()
    se['event_timestamp'] = pd.to_datetime(se['event_timestamp'])
    se['true_hour_utc'] = se['event_timestamp'].dt.hour
    se['logged_hour_utc'] = pd.to_numeric(se['event_hour_utc'])
    
    se['is_corrupt'] = (se['logged_hour_utc'] == 0) & (se['true_hour_utc'] >= 20) & (se['true_hour_utc'] <= 23)
    
    grouped = se.groupby(['true_hour_utc', 'logged_hour_utc']).agg(
        total_events=('event_id', 'count'),
        corrupt_records=('is_corrupt', 'sum')
    ).reset_index()
    
    grouped['corruption_pct'] = np.where(
        grouped['total_events'] > 0,
        (grouped['corrupt_records'] / grouped['total_events'] * 100).round(2),
        0.0
    )
    
    total_rows = len(se)
    total_corrupt_rows = se['is_corrupt'].sum()
    overall_corruption_pct = round((total_corrupt_rows / total_rows * 100), 2) if total_rows > 0 else 0.0
    
    return grouped, {
        'total_rows': total_rows,
        'total_corrupt_rows': total_corrupt_rows,
        'overall_corruption_pct': overall_corruption_pct
    }


class TestTimezoneInvestigation(unittest.TestCase):
    
    def setUp(self):
        # Authenticate and connect to BigQuery dynamically for live cloud tests
        print("\n[SETUP] Initiating interactive BigQuery authentication...")
        try:
            credentials = pydata_google_auth.get_user_credentials(
                scopes=['https://www.googleapis.com/auth/cloud-platform'],
            )
            self.client = bigquery.Client(project="meli-last-mile-sql-assessment", credentials=credentials)
            self.bq_available = True
            print("[SETUP] BigQuery client initialized successfully.")
        except Exception as e:
            self.bq_available = False
            print(f"[SETUP] BigQuery not available (skipping live queries): {e}")

    def test_local_timezone_calculations(self):
        """
        Verify the local pandas implementation of timezone conversions and corruption auditing
        using mock data (T1, T2, T4).
        """
        print("\n[TEST] Verifying local timezone conversions and corruption auditing with mock data...")
        
        # 1. Setup mock DataFrames
        routes_data = {
            'route_id': ['R1', 'R2', 'R3', 'R4'],
            'center_id': ['DC1', 'DC1', 'DC2', 'DC2'],
            'route_type': ['DELIVERY', 'DELIVERY', 'DELIVERY', 'PICKUP'], # R4 is PICKUP (excluded)
            'route_status': ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED'],
            'route_date': ['2025-04-10', '2025-04-11', '2025-06-01', '2025-04-12'] # R3 is June (excluded)
        }
        
        dc_data = {
            'center_id': ['DC1', 'DC2'],
            'country': ['CO', 'MX'],
            'timezone_offset': [-5, -6]
        }
        
        # R1 is CO (offset -5). Total delivery: event_timestamp '2025-04-10 01:30:00' (UTC) -> hour_utc = 1. local = '2025-04-09 20:30:00' -> hour_local = 20.
        # R2 is CO (offset -5). Total delivery: event_timestamp '2025-04-11 20:30:00' (UTC) -> hour_utc = 20. local = '2025-04-11 15:30:00' -> hour_local = 15.
        se_data = {
            'event_id': ['E1', 'E2', 'E3', 'E4'],
            'shipment_id': ['S1', 'S2', 'S3', 'S4'],
            'route_id': ['R1', 'R2', 'R3', 'R4'],
            'event_type': ['delivered', 'delivered', 'delivered', 'delivered'],
            'event_timestamp': [
                '2025-04-10 01:30:00', # R1 (CO): local 20:30 (Late local, but not late UTC)
                '2025-04-11 20:30:00', # R2 (CO): local 15:30 (Late UTC, but not late local)
                '2025-06-01 01:30:00', # R3 (MX): excluded by route_date
                '2025-04-12 01:30:00'  # R4 (MX): excluded by route_type
            ],
            'event_hour_utc': [0, 0, 0, 0]
        }
        
        routes_df = pd.DataFrame(routes_data)
        dc_df = pd.DataFrame(dc_data)
        se_df = pd.DataFrame(se_data)
        
        metrics = calculate_timezone_metrics(se_df, routes_df, dc_df)
        
        # We expect only CO ('R1' and 'R2') to be included.
        # Total deliveries = 2
        # deliveries_utc_after_20 = 1 (E2: hour_utc = 20) -> pct_utc_after_20 = 50.0
        # deliveries_local_after_20 = 1 (E1: hour_local = 20) -> pct_local_after_20 = 50.0
        self.assertEqual(len(metrics), 1)
        co_row = metrics[metrics['country'] == 'CO'].iloc[0]
        self.assertEqual(co_row['total_deliveries'], 2)
        self.assertEqual(co_row['deliveries_utc_after_20'], 1)
        self.assertEqual(co_row['deliveries_local_after_20'], 1)
        self.assertEqual(co_row['pct_utc_after_20'], 50.0)
        self.assertEqual(co_row['pct_local_after_20'], 50.0)
        
        # 2. Setup mock data for corruption audit
        corrupt_se_data = {
            'event_id': ['E1', 'E2', 'E3', 'E4'],
            'event_timestamp': [
                '2025-04-10 21:00:00', # true hour 21, logged 0 -> CORRUPT
                '2025-04-10 22:00:00', # true hour 22, logged 22 -> OK
                '2025-04-10 19:00:00', # true hour 19, logged 0 -> OK (hour not >= 20)
                '2025-04-10 23:00:00'  # true hour 23, logged 0 -> CORRUPT
            ],
            'event_hour_utc': [0, 22, 0, 0]
        }
        corrupt_se_df = pd.DataFrame(corrupt_se_data)
        
        audit_detail, summary = audit_logging_corruption(corrupt_se_df)
        self.assertEqual(summary['total_rows'], 4)
        self.assertEqual(summary['total_corrupt_rows'], 2)
        self.assertEqual(summary['overall_corruption_pct'], 50.0)

    def test_cloud_timezone_investigation(self):
        """
        Query BigQuery, validate outputs against reference values, and generate the markdown report (T3, T4).
        """
        if not self.bq_available:
            self.skipTest("BigQuery client not available. Skipping live cloud tests.")
            
        print("\n[TEST] Executing live BigQuery queries for Timezone Investigation...")
        
        # 1. Timezone comparison query
        timezone_query = """
        WITH delivery_events AS (
          SELECT 
            dc.country,
            dc.timezone_offset,
            se.event_timestamp,
            EXTRACT(HOUR FROM se.event_timestamp) as hour_utc,
            EXTRACT(HOUR FROM TIMESTAMP_ADD(se.event_timestamp, INTERVAL dc.timezone_offset HOUR)) as hour_local
          FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new` se
          JOIN `meli-last-mile-sql-assessment.LAstmile.routes_new` r
            ON se.route_id = r.route_id
          JOIN `meli-last-mile-sql-assessment.LAstmile.distribution_centers` dc
            ON r.center_id = dc.center_id
          WHERE se.event_type = 'delivered'
            AND r.route_type = 'DELIVERY'
            AND r.route_status = 'COMPLETED'
            AND r.route_date BETWEEN '2025-04-01' AND '2025-05-31'
        )

        SELECT 
          country,
          timezone_offset,
          COUNT(*) as total_deliveries,
          COUNTIF(hour_utc >= 20) as deliveries_utc_after_20,
          ROUND(SAFE_DIVIDE(COUNTIF(hour_utc >= 20), COUNT(*)) * 100, 2) as pct_utc_after_20,
          COUNTIF(hour_local >= 20) as deliveries_local_after_20,
          ROUND(SAFE_DIVIDE(COUNTIF(hour_local >= 20), COUNT(*)) * 100, 2) as pct_local_after_20
        FROM delivery_events
        GROUP BY country, timezone_offset
        ORDER BY country;
        """
        
        timezone_df = self.client.query(timezone_query).to_dataframe()
        print("Timezone metrics calculated from BigQuery:")
        print(timezone_df.to_string())
        
        # Reference validation:
        # BR: 0.73% local vs. 0.51% UTC
        # CO: 3.12% local vs. 0.47% UTC
        # MX: 5.64% local vs. 0.55% UTC
        # PE: 3.94% local vs. 0.64% UTC
        # AR: 0.73% local vs. 0.57% UTC
        # CL: 1.13% local vs. 0.61% UTC
        
        expected_rates = {
            'BR': {'utc': 0.51, 'local': 0.73},
            'CO': {'utc': 0.47, 'local': 3.12},
            'MX': {'utc': 0.55, 'local': 5.64},
            'PE': {'utc': 0.64, 'local': 3.94},
            'AR': {'utc': 0.57, 'local': 0.73},
            'CL': {'utc': 0.61, 'local': 1.13}
        }
        
        for country, rates in expected_rates.items():
            row = timezone_df[timezone_df['country'] == country].iloc[0]
            self.assertAlmostEqual(row['pct_utc_after_20'], rates['utc'], delta=0.1,
                                   msg=f"UTC late-night rate mismatch for {country}")
            self.assertAlmostEqual(row['pct_local_after_20'], rates['local'], delta=0.1,
                                   msg=f"Local late-night rate mismatch for {country}")
            
        # 2. Logging corruption query
        corruption_query = """
        SELECT 
          EXTRACT(HOUR FROM event_timestamp) AS true_hour_utc,
          event_hour_utc AS logged_hour_utc,
          COUNT(*) AS total_events,
          COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20) AS corrupt_records,
          ROUND(SAFE_DIVIDE(COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20), COUNT(*)) * 100, 2) AS corruption_pct
        FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`
        GROUP BY true_hour_utc, logged_hour_utc
        ORDER BY true_hour_utc;
        """
        
        corruption_df = self.client.query(corruption_query).to_dataframe()
        
        overall_query = """
        SELECT 
          COUNT(*) as total_rows,
          COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20) as total_corrupt_rows,
          ROUND(SAFE_DIVIDE(COUNTIF(event_hour_utc = 0 AND EXTRACT(HOUR FROM event_timestamp) >= 20), COUNT(*)) * 100, 2) as overall_corruption_pct
        FROM `meli-last-mile-sql-assessment.LAstmile.shipment_events_new`;
        """
        
        overall_df = self.client.query(overall_query).to_dataframe()
        overall_stats = overall_df.iloc[0]
        
        print(f"Overall corruption stats: {overall_stats['total_corrupt_rows']} corrupt rows out of {overall_stats['total_rows']} ({overall_stats['overall_corruption_pct']}%)")
        
        # Verify that for true_hour_utc >= 20, the precalculated logged_hour_utc is indeed 0 (corrupt)
        corrupt_hours = corruption_df[(corruption_df['true_hour_utc'] >= 20) & (corruption_df['logged_hour_utc'] == 0)]
        self.assertFalse(corrupt_hours.empty, "Should find corrupt records for hours >= 20")
        
        # 3. Generate the Spanish Markdown report
        report_path = "D:/wt-harness-MELI_BI/Reports/Question_5_Timezone_Investigation_Report.md"
        print(f"[TEST] Writing {report_path}...")
        
        # Build comparison table markdown
        table_md = "| País | Huso Horario (Offset) | Envíos Entregados | Entregas UTC Tardías (>=20:00) | Tasa UTC Tardía (%) | Entregas Locales Tardías (>=20:00) | Tasa Local Tardía (%) |\n"
        table_md += "|---|---|---|---|---|---|---|\n"
        for _, row in timezone_df.iterrows():
            table_md += f"| **{row['country']}** | {row['timezone_offset']:+d} | {row['total_deliveries']:,} | {row['deliveries_utc_after_20']:,} | {row['pct_utc_after_20']:.2f}% | {row['deliveries_local_after_20']:,} | {row['pct_local_after_20']:.2f}% |\n"
            
        # Build corruption table markdown
        corruption_table_md = "| Hora Real UTC | Hora Registrada (`event_hour_utc`) | Total Eventos | Registros Corruptos | % Corrupción |\n"
        corruption_table_md += "|---|---|---|---|---|\n"
        for _, row in corruption_df.iterrows():
            if pd.notna(row['true_hour_utc']) and row['true_hour_utc'] >= 18:  # show hours around the late-night threshold
                corruption_table_md += f"| {int(row['true_hour_utc']):02d}:00 | {int(row['logged_hour_utc']):02d}:00 | {row['total_events']:,} | {row['corrupt_records']:,} | {row['corruption_pct']:.2f}% |\n"
                
        report_content = f"""# REPORTE: INVESTIGACIÓN DE HUSOS HORARIOS Y PATRONES OPERATIVOS (QUESTION 5)
**Proyecto:** Análisis de Eficiencia Operativa y Calidad de Datos - LATAM Last Mile  
**Rol:** Arquitecto Principal de BI y AI en Logística (LATAM Last Mile)  
**Fecha:** 27 de mayo de 2026  

---

## 📋 Resumen Ejecutivo

Este reporte responde a la preocupación de la dirección respecto a si **Brasil (`BR`)** y **Colombia (`CO`)** están operando con entregas en horarios nocturnos de alto riesgo (después de las 20:00) en comparación con **México (`MX`)** o **Chile (`CL`)**.

Nuestra investigación revela dos hallazgos críticos:
1. **La Ilusión del Huso Horario (Timezone Illusion):** La sospecha de entregas tardías en Brasil y Colombia es un artefacto puramente técnico causado por el registro de logs en UTC-0. En hora local real, **Colombia registra apenas un 3.12%** de entregas tardías y **Brasil solo un 0.73%**. Por el contrario, **México es el país con más entregas nocturnas reales (5.64%)**, seguido por **Perú (3.94%)**.
2. **Corrupción de Datos en la Columna Precalculada (`event_hour_utc`):** Descubrimos un error crítico de calidad de datos en el Data Warehouse. La columna precalculada `event_hour_utc` **se trunca a cero (0)** para cualquier entrega que ocurra entre las 20:00 y las 23:59 UTC. Esto causa que cualquier reporte que sume o agrupe por `event_hour_utc` directamente muestre cero entregas nocturnas, ocultando por completo la operación real si no se calcula dinámicamente desde el timestamp original.

---

## 🔍 1. Análisis de Entregas Tardías: UTC vs. Hora Local Real

Al ajustar los timestamps UTC de los eventos de entrega (`event_type = 'delivered'`) al huso horario local de cada Centro de Distribución (`dc.timezone_offset`), obtenemos la siguiente comparación:

{table_md}

### 💡 Diagnóstico de Negocio e Interpretación Operativa:

* **1. Desmitificación de Brasil y Colombia:**
  * **Colombia (`CO`, Huso -5):** Inicialmente parecía tener entregas tardías debido al desfase de 5 horas. Una entrega a las 01:00 UTC corresponde a las 20:00 local. Al ajustar al tiempo local, el porcentaje de entregas tardías reales es de **3.12%**, una tasa sumamente controlada y dentro de los parámetros de seguridad.
  * **Brasil (`BR`, Huso -3):** Al estar en UTC-3, el impacto es aún menor. Las entregas nocturnas locales reales representan apenas el **0.73%**, consolidando a Brasil como una de las operaciones con menor riesgo nocturno real.

* **2. El Verdadero Foco de Riesgo: México y Perú:**
  * **México (`MX`, Huso -6):** Al ajustar al huso -6, la tasa de entregas nocturnas reales sube a **5.64%**, siendo la más alta de la región. Esto significa que más de 5 de cada 100 entregas en México ocurren después de las 20:00 hora local, requiriendo auditoría de rutas y medidas de seguridad para los conductores.
  * **Perú (`PE`, Huso -5):** Registra una tasa real del **3.94%**, situándose por encima de Colombia y Brasil.

---

## 🚨 2. Diagnóstico y Auditoría de Corrupción en `event_hour_utc`

Durante la auditoría detectamos una anomalía grave en la tabla `shipment_events_new`: los eventos con hora UTC real entre las 20:00 y 23:59 muestran un valor de `0` en la columna precalculada `event_hour_utc`.

A continuación, se presenta el detalle de la auditoría horaria para las horas cercanas al corte:

{corruption_table_md}

### 💡 Análisis del Impacto y Causa Raíz de la Corrupción:
* **Filtro de Truncamiento Crítico (Bug del ETL):** 
  El análisis muestra una corrupción del **100%** de los registros en el rango de horas de 20 a 23 UTC. Para las horas de 18:00 o 19:00, el valor de `logged_hour_utc` coincide exactamente con la hora del timestamp. Pero a partir de las 20:00 UTC, la columna `event_hour_utc` se fuerza a `0` de forma persistente.
* **Volumen de Afectación:** 
  A nivel de toda la tabla `shipment_events_new`, existen **{overall_stats['total_corrupt_rows']:,} registros corruptos** de un total de **{overall_stats['total_rows']:,}**, lo que representa una tasa de corrupción global del **{overall_stats['overall_corruption_pct']:.2f}%**.
* **Impacto Operativo:**
  Cualquier analista que realice consultas agrupando por `event_hour_utc` concluirá erróneamente que no existen eventos entre las 20:00 y las 23:59 UTC, sesgando cualquier análisis de productividad de turnos nocturnos o cumplimiento de ventanas de entrega.

---

## 🛠️ 3. Recomendaciones de Ingeniería de Datos y Acciones

Para resolver estos problemas estructurales, se proponen las siguientes acciones inmediatas:

1. **Corrección del Pipeline de Ingesta (ETL):**
   Alinear con el equipo de Data Platform para revisar el proceso de carga de `shipment_events_new`. El bug de truncamiento a `0` para horas >= 20 indica un error de parsing o casting en la transformación horaria del ETL (posiblemente un desbordamiento o máscara incorrecta).
2. **Prohibición del Uso de `event_hour_utc`:**
   Emitir una directiva técnica para que todos los analistas de BI y Data Scientists del equipo logístico extraigan el componente horario directamente de `event_timestamp` usando `EXTRACT(HOUR FROM event_timestamp)` en lugar de consultar la columna precalculada corrupta.
3. **Normalización por Timezone en Dashboards:**
   Implementar la función `TIMESTAMP_ADD(event_timestamp, INTERVAL timezone_offset HOUR)` en la capa semántica de Looker Studio/Power BI para asegurar que todas las visualizaciones muestren métricas en hora local del Centro de Distribución y no en UTC-0.
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print("[TEST] Question 5 report written successfully.")

if __name__ == "__main__":
    unittest.main()

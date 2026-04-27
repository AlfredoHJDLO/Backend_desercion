import json
import pandas as pd
import plotly.express as px
from services.data_loader import get_dataframe

def get_metadata_service():
    """Obtiene las opciones para los filtros de la interfaz."""
    df = get_dataframe()
    carreras = sorted(df['CARRERA'].dropna().unique().tolist())
    todos_los_grupos = sorted(df['GRUPO'].dropna().unique().tolist())

    grupos_por_carrera = {}
    for carrera in carreras:
        grupos = sorted(df[df['CARRERA'] == carrera]['GRUPO'].dropna().unique().tolist())
        grupos_por_carrera[carrera] = grupos

    return {
        "carreras": carreras,
        "todos_los_grupos": todos_los_grupos,
        "grupos_por_carrera": grupos_por_carrera
    }

def get_dashboard_data_service(params, is_estudiantes=False):
    """
    Procesa los datos, genera KPIs y todas las gráficas de Plotly.
    is_estudiantes: Define si el desglose es por Grupo (True) o por Carrera (False).
    """
    df = get_dataframe()
    carrera = params.get('carreras', "")
    grupo = params.get('grupos', "")

    # 1. Filtrado dinámico
    dff = df.copy()
    if carrera != "":
        dff = dff[dff['CARRERA'] == carrera]
    if grupo != "":
        dff = dff[dff['GRUPO'] == grupo]

    df_riesgo = dff[dff['RIESGO_ACADEMICO'] == 1].copy()

    # 2. Cálculo de KPIs
    stats = {
        "total": len(dff),
        "riesgo": len(df_riesgo)
    }

    if is_estudiantes:
        # KPI específico para vista de estudiantes
        stats["grupo_riesgo"] = df_riesgo['GRUPO'].value_counts().idxmax() if not df_riesgo.empty else "N/A"
        stats["promedio"] = round(dff['PROMEDIO GENERAL'].mean(), 1) if not dff.empty else 0.0
    else:
        # KPI específico para vista general
        stats["carrera_riesgo"] = df_riesgo['CARRERA'].value_counts().idxmax().capitalize() if not df_riesgo.empty else "N/A"

    # 3. Datos para la Tabla
    datos_tabla = df_riesgo[['MATRÍCULA', 'GRUPO', 'CARRERA', 'PROMEDIO GENERAL']].to_dict('records')

    # 4. GENERACIÓN DE GRÁFICAS
    
    # Común: Gráfica de Barras (Riesgo por Carrera o Grupo)
    eje_y = "GRUPO" if is_estudiantes else "CARRERA"
    fig_barras = px.histogram(
        dff, y=eje_y, color="RIESGO_ACADEMICO", 
        title=f"Riesgo por {eje_y.capitalize()}",
        color_discrete_map={0: '#EA9C9C', 1: '#7E2C2C'}, barmode="group"
    )
    _style_chart(fig_barras)

    # Dona: Estado Académico
    fig_dona = px.pie(dff, names='ESTADO', title='Distribución de Estado Académico', hole=0.6,
                    color_discrete_sequence=['#B20025', '#e9ecef', '#adb5bd', '#495057'])
    _style_chart(fig_dona)

    # Boxplot: Promedios por Periodo
    fig_box = px.box(dff, x="PERIODO ACTUAL", y="PROMEDIO GENERAL", color="RIESGO_ACADEMICO",
                     title="Distribución de Promedios por Periodo",
                     color_discrete_map={0: '#00d1b2', 1: '#ff3860'})
    _style_chart(fig_box)

    # Pie: Género
    fig_genero = px.pie(dff, names='GÉNERO', title='Género de Estudiantes en Riesgo',
                        hole=0.5, color_discrete_sequence=['#7E2C2C', '#EA9C9C'])
    _style_chart(fig_genero)

    # Líneas: Evolución del Riesgo
    todos_los_periodos = sorted(dff['PERIODO ACTUAL'].unique())
    resumen_periodo = df_riesgo.groupby('PERIODO ACTUAL').size().reindex(todos_los_periodos, fill_value=0).reset_index(name='conteo')
    fig_lineas = px.line(resumen_periodo, x='PERIODO ACTUAL', y='conteo', title="Evolución de Estudiantes en Riesgo",
                         markers=True, color_discrete_sequence=['#7E2C2C'])
    fig_lineas.update_layout(yaxis=dict(rangemode='tozero'))
    _style_chart(fig_lineas)

    # Distribución de Riesgo (Pastel)
    fig_pastel_riesgo = px.pie(df_riesgo, names=eje_y, title=f'Distribución de Riesgo por {eje_y.capitalize()}',
                               hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
    _style_chart(fig_pastel_riesgo)

    # Diccionario final de gráficas
    charts = {
        "histograma_carrera": json.loads(fig_barras.to_json()),
        "dona": json.loads(fig_dona.to_json()),
        "barras": json.loads(fig_box.to_json()),
        "genero": json.loads(fig_genero.to_json()),
        "lineas": json.loads(fig_lineas.to_json()),
        "pastel_riesgo": json.loads(fig_pastel_riesgo.to_json())
    }

    # Gráfica extra solo para estudiantes
    if is_estudiantes:
        fig_dist_prom = px.histogram(dff, x="PROMEDIO GENERAL", title="Distribución de Promedios Generales",
                                     color_discrete_sequence=['#7E2C2C'])
        fig_dist_prom.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 10.5]))
        _style_chart(fig_dist_prom)
        charts["distribucion_promedios"] = json.loads(fig_dist_prom.to_json())

    return {
        "kpis": stats,
        "tabla": datos_tabla,
        "charts": charts
    }

def _style_chart(fig):
    """Función auxiliar para aplicar el estilo visual de la UTM a cualquier gráfica."""
    fig.update_layout(
        plot_bgcolor='white', 
        paper_bgcolor='white', 
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Lexend", size=11, color="#2c3e50"),
        title_font=dict(family="Lexend", size=20, color="#000000")
    )
    # Renombrar leyendas de 0/1 a texto legible si existen
    fig.for_each_trace(lambda t: t.update(
        name = "Sin Riesgo" if t.name == "0" else "Riesgo Crítico" if t.name == "1" else t.name,
        legendgroup = "Sin Riesgo" if t.name == "0" else "Riesgo Crítico" if t.name == "1" else t.name
    ))
import json
import plotly.express as px
from services.data_loader import get_dataframe

def get_metadata_service():
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
    df = get_dataframe()
    carrera = params.get('carreras', "")
    grupo = params.get('grupos', "")

    dff = df.copy()

    if carrera != "":
        dff = dff[dff['CARRERA'] == carrera]
    if grupo != "":
        dff = dff[dff['GRUPO'] == grupo]

    df_riesgo = dff[dff['RIESGO_ACADEMICO'] == 1].copy()

    # Determinar la variable top dependiendo del tipo de dashboard
    variable_agrupacion = 'GRUPO' if is_estudiantes else 'CARRERA'
    
    if not df_riesgo.empty:
        top_riesgo = df_riesgo[variable_agrupacion].value_counts().idxmax()
        if not is_estudiantes:
            top_riesgo = top_riesgo.capitalize()
    else:
        top_riesgo = "N/A"

    # KPIs
    stats = {
        "total": len(dff),
        "riesgo": len(df_riesgo),
    }
    
    if is_estudiantes:
        stats["grupo_riesgo"] = top_riesgo
        stats["promedio"] = round(dff['PROMEDIO GENERAL'].mean(), 1) if not dff.empty else 0.0
    else:
        stats["carrera_riesgo"] = top_riesgo

    # Tabla
    datos_tabla = df_riesgo[['MATRÍCULA', 'GRUPO', 'CARRERA', 'PROMEDIO GENERAL']].to_dict('records')

    conteo_riesgo = dff[dff['RIESGO_ACADEMICO'] == 1]['CARRERA'].value_counts(ascending=True)

    # 2. Obtenemos la lista de nombres de las carreras en ese orden
    orden_carreras = conteo_riesgo.index.tolist()

    # 3. Manejo de carreras con cero alumnos en riesgo (opcional pero recomendado)
    # Esto asegura que las carreras que no tienen a nadie en riesgo aparezcan al inicio (abajo)
    todas_las_carreras = dff['GRUPO'].unique()
    carreras_sin_riesgo = [c for c in todas_las_carreras if c not in orden_carreras]
    orden_final = carreras_sin_riesgo + orden_carreras

    # 4. Creamos el gráfico
    fig_barras_carrera = px.histogram(
        dff, 
        y="GRUPO", 
        color="RIESGO_ACADEMICO", 
        title="Riesgo por Grupo",
        color_discrete_map={0: '#EA9C9C', 1: '#7E2C2C'},
        barmode="group"
    )

    # 5. Forzamos a Plotly a usar nuestro orden calculado
    fig_barras_carrera.update_yaxes(
        categoryorder='array', 
        categoryarray=orden_final
    )

    fig_barras_carrera.for_each_trace(lambda t: t.update(
        name = "Sin Riesgo" if t.name == "0" else "Riesgo Crítico",
        legendgroup = "Sin Riesgo" if t.name == "0" else "Riesgo Crítico",
        hovertemplate = t.hovertemplate.replace(t.name, "Sin Riesgo" if t.name == "0" else "Riesgo Crítico")
    ))
    fig_barras_carrera.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=0, r=0, t=40, b=0),
                                     font=dict(
                                            family="Lexend", # Tipografías seguras del sistema
                                            size=11,
                                            color="#2c3e50"
                                        ),
                                        title_font=dict(
                                            family="Lexend", # Puedes poner una fuente distinta solo para el título
                                            size=22,
                                            color="#000000"
                                        )
                                    )

    # Dona - Estado Académico
    fig_dona = px.pie(dff, names='ESTADO', title='Distribución de Estado Académico', hole=0.6,
                    color_discrete_sequence=['#B20025', '#e9ecef', '#adb5bd', '#495057'])
    fig_dona.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=0, r=0, t=40, b=0),
                           font=dict(
                                            family="Lexend", # Tipografías seguras del sistema
                                            size=11,
                                            color="#2c3e50"
                                        ),
                                        title_font=dict(
                                            family="Lexend", # Puedes poner una fuente distinta solo para el título
                                            size=22,
                                            color="#000000"
                                        ))
    
    # Boxplot - Promedios
    fig_bar = px.box(dff, x="PERIODO ACTUAL", y="PROMEDIO GENERAL", color="RIESGO_ACADEMICO",
                     title="Distribución de Promedios por Periodo",
                     color_discrete_map={0: '#00d1b2', 1: '#ff3860'})

    fig_bar.for_each_trace(lambda t: t.update(
        name = "SIN RIESGO" if t.name == "0" else "RIESGO CRÍTICO",
        legendgroup = "SIN RIESGO" if t.name == "0" else "RIESGO CRÍTICO",
        hovertemplate = t.hovertemplate.replace(t.name, "SIN RIESGO" if t.name == "0" else "RIESGO CRITICO")
    ))

    fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font=dict(
                                            family="Lexend", # Tipografías seguras del sistema
                                            size=11,
                                            color="#2c3e50"
                                        ),
                                        title_font=dict(
                                            family="Lexend", # Puedes poner una fuente distinta solo para el título
                                            size=22,
                                            color="#000000"
                                        ))
    
    # Pie - Género
    fig_pie = px.pie(dff, names='GÉNERO', title='Género de los estudiantes en riesgo',
                     hole=0.5, color_discrete_sequence=['#7E2C2C', '#EA9C9C'])
    
    fig_pie.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=0, r=0, t=40, b=0),
                           font=dict(
                                            family="Lexend", # Tipografías seguras del sistema
                                            size=11,
                                            color="#2c3e50"
                                        ),
                                        title_font=dict(
                                            family="Lexend", # Puedes poner una fuente distinta solo para el título
                                            size=22,
                                            color="#000000"
                                        ))

    # --- 1. Gráfica de Líneas: Riesgo por Periodo ---
    # Paso A: Extraemos TODOS los periodos posibles del dataframe general (dff), no del filtrado.
    # Los ordenamos para asegurar que la línea de tiempo sea correcta.
    todos_los_periodos = sorted(dff['PERIODO ACTUAL'].unique())

    # Paso B: Agrupamos los estudiantes en riesgo, reindexamos contra todos los periodos 
    # y rellenamos los huecos vacíos con 0.
    resumen_periodo = (
        df_riesgo.groupby('PERIODO ACTUAL')
        .size()
        .reindex(todos_los_periodos, fill_value=0) # <--- Aquí está la magia
        .reset_index(name='conteo')
    )
    
    # Creamos la gráfica igual que antes
    fig_lineas = px.line(
        resumen_periodo, 
        x='PERIODO ACTUAL', 
        y='conteo',
        title="Evolución de Estudiantes en Riesgo",
        markers=True,
        color_discrete_sequence=['#7E2C2C']
    )
    
    # Opcional: Forzamos a que el eje Y empiece en 0 siempre
    fig_lineas.update_layout(
        plot_bgcolor='white', 
        paper_bgcolor='white',
        yaxis=dict(rangemode='tozero') # Asegura que la gráfica no "flote" si los valores son bajos
    )

    # --- 2. Gráfica de Pastel: Distribución de Riesgo por Carrera ---
    fig_pastel_riesgo = px.pie(
        df_riesgo, 
        names='GRUPO', 
        title='Distribución de Riesgo por Grupo',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    fig_distribucion_promedios = px.histogram(
        dff, 
        x="PROMEDIO GENERAL", 
        title="Distribución de Promedios Generales",
        color_discrete_sequence=['#7E2C2C'] # El rojo de la UTM
    )
    
    # Forzamos que el eje X muestre números enteros del 1 al 10
    fig_distribucion_promedios.update_layout(
        plot_bgcolor='#F8F8F8',
        paper_bgcolor='white',
        xaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1, # Saltos de 1 en 1
            range=[0.5, 10.5], # Para que las barras no se corten en los bordes
            title="Calificación"
        ),
        yaxis=dict(title="Cantidad de Estudiantes"),
        margin=dict(l=40, r=40, t=50, b=40)
    )

    # Convertimos los objetos de Plotly a diccionarios compatibles con JSON
    return{
        "kpis": stats,
        "tabla": datos_tabla,
        "charts": {
            "histograma_carrera": json.loads(fig_barras_carrera.to_json()),
            "dona": json.loads(fig_dona.to_json()),
            "barras": json.loads(fig_bar.to_json()),
            "genero": json.loads(fig_pie.to_json()),
            "lineas": json.loads(fig_lineas.to_json()),
            "pastel_riesgo": json.loads(fig_pastel_riesgo.to_json()),
            "distribucion_promedios": json.loads(fig_distribucion_promedios.to_json())
        }
    }

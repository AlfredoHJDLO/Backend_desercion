import os
import base64
import json
import plotly.express as px
import pandas as pd
from datetime import datetime
from flask import render_template_string, current_app
from weasyprint import HTML
from models import ArchivoSubido, Prediccion
from services.dashboard_service import get_dashboard_data_service # Importamos la lógica existente


def generate_full_pdf_report(user_id):
    # 1. Obtener datos del usuario y el archivo procesado
    archivo = ArchivoSubido.query.filter_by(usuario_id=user_id).first()
    if not archivo or not archivo.procesado:
        return None, "No hay datos procesados para generar el reporte."

    predicciones = Prediccion.query.filter_by(archivo_id=archivo.id).all()
    df = pd.DataFrame([{
        "matricula": p.matricula,
        "carrera": p.carrera,
        "edad": p.edad,
        "foraneo": p.es_foraneo,
        "riesgo": p.prediccion_clase,
        "probabilidad": p.probabilidad_riesgo
    } for p in predicciones])

    # 2. Generar Gráficas Estáticas (Base64)
    # Ejemplo: Gráfica de Riesgo por Carrera
    df_riesgo = df[df['riesgo'] == 1]
    
    fig_carrera = px.pie(df_riesgo, names='carrera', title='Riesgo por Carrera')
    img_carrera = _plot_to_base64(fig_carrera)

    fig_edad = px.histogram(df_riesgo, x='edad', title='Distribución de Edades en Riesgo')
    img_edad = _plot_to_base64(fig_edad)

    # 3. Análisis de Texto Dinámico
    total_alumnos = len(df)
    total_riesgo = len(df_riesgo)
    porcentaje = round((total_riesgo / total_alumnos) * 100, 2)
    carrera_top = df_riesgo['carrera'].value_counts().idxmax() if not df_riesgo.empty else "N/A"

    # 4. Template HTML con CSS embebido (Estilo Profesional)
    html_template = """
    <html>
    <head>
        <style>
            @page { size: A4; margin: 20mm; background-color: #ffffff; }
            body { font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.5; }
            .header { text-align: center; border-bottom: 2px solid #7E2C2C; padding-bottom: 10px; margin-bottom: 30px; }
            h1 { color: #7E2C2C; font-size: 24pt; }
            h2 { color: #2c3e50; border-left: 5px solid #7E2C2C; padding-left: 10px; margin-top: 30px; }
            .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background-color: #7E2C2C; color: white; padding: 10px; text-align: left; }
            td { border: 1px solid #ddd; padding: 8px; font-size: 10pt; }
            .chart-container { text-align: center; margin: 20px 0; }
            .chart-img { width: 80%; max-height: 400px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Reporte de Análisis de Riesgo Académico</h1>
            <p>Fecha de generación: {{ fecha }}</p>
        </div>

        <div class="stat-box">
            <h2>Resumen Ejecutivo</h2>
            <p>Se ha analizado un total de <strong>{{ total }}</strong> estudiantes del archivo <em>{{ nombre_archivo }}</em>. 
            Se identificaron <strong>{{ riesgo }}</strong> alumnos con probabilidad crítica de deserción, lo que representa un <strong>{{ porcentaje }}%</strong> del lote.</p>
            <p>La carrera con mayor incidencia detectada es: <strong>{{ carrera_top }}</strong>.</p>
        </div>

        <h2>Visualización Estadística</h2>
        <div class="chart-container">
            <img class="chart-img" src="data:image/png;base64,{{ img_carrera }}">
        </div>
        <div class="chart-container">
            <img class="chart-img" src="data:image/png;base64,{{ img_edad }}">
        </div>

        <div style="page-break-before: always;"></div>

        <h2>Listado de Estudiantes en Riesgo Crítico</h2>
        <table>
            <thead>
                <tr>
                    <th>Matrícula</th>
                    <th>Carrera</th>
                    <th>Edad</th>
                    <th>Probabilidad</th>
                </tr>
            </thead>
            <tbody>
                {% for est in tabla %}
                <tr>
                    <td>{{ est.matricula }}</td>
                    <td>{{ est.carrera }}</td>
                    <td>{{ est.edad }}</td>
                    <td>{{ (est.probabilidad * 100)|round(2) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """

    # 5. Renderizado y Conversión
    rendered_html = render_template_string(
        html_template,
        fecha=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=total_alumnos,
        riesgo=total_riesgo,
        porcentaje=porcentaje,
        carrera_top=carrera_top,
        nombre_archivo=archivo.nombre_archivo,
        img_carrera=img_carrera,
        img_edad=img_edad,
        tabla=df_riesgo.to_dict('records')
    )

    pdf = HTML(string=rendered_html).write_pdf()
    return pdf, None

def _plot_to_base64(fig):
    """Auxiliar para convertir gráfica de Plotly a imagen Base64"""
    img_bytes = fig.to_image(format="png", engine="kaleido")
    return base64.b64encode(img_bytes).decode('utf-8')


def generate_statistical_pdf_report(params):
    from datetime import datetime
    import json
    
    carrera_val = params.get('carreras', "")
    grupo_val = params.get('grupos', "")
    
    # Determinamos si es vista detallada para el servicio
    # Si hay carrera seleccionada, pedimos estadísticas detalladas (is_estudiantes=True)
    es_detallado = (carrera_val != "")
    data = get_dashboard_data_service(params, is_estudiantes=es_detallado)
    
    kpis = data['kpis']
    charts_json = data['charts']
    
    import plotly.io as pio
    def json_to_base64(chart_json):
        fig = pio.from_json(json.dumps(chart_json))
        # Asegúrate de que esta función devuelva un string utf-8
        return _plot_to_base64(fig)

    img_riesgo = json_to_base64(charts_json['pastel_riesgo'])
    img_lineas = json_to_base64(charts_json['lineas'])
    img_desempeño = json_to_base64(charts_json['barras'])

    html_template = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: 'Helvetica'; color: #333; line-height: 1.5; }
            .header { text-align: center; color: #7E2C2C; border-bottom: 2px solid #7E2C2C; padding-bottom: 10px; }
            .kpi-container { display: flex; justify-content: space-around; margin: 30px 0; }
            .kpi-card { border: 1px solid #ddd; padding: 15px; text-align: center; border-radius: 8px; width: 30%; background: #f9f9f9; }
            .kpi-value { font-size: 22px; font-weight: bold; color: #7E2C2C; display: block; margin-top: 5px; }
            .section-title { color: #7E2C2C; border-left: 5px solid #7E2C2C; padding-left: 10px; margin-top: 40px; }
            .explanation { font-size: 14px; color: #555; margin-bottom: 20px; text-align: justify; }
            .chart { width: 100%; text-align: center; margin-top: 20px; }
            .footer { font-size: 10px; text-align: center; color: #999; margin-top: 50px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Reporte de Desempeño Académico</h1>
            <p>Universidad Tecnológica de la Mixteca</p>
            <p style="color: #666;">Generado el {{ fecha }}</p>
        </div>

        <h2 class="section-title">Resumen Ejecutivo</h2>
        <p class="explanation">
            Este apartado presenta los indicadores clave de rendimiento (KPIs) basados en los filtros aplicados. 
            Permite visualizar rápidamente el volumen de estudiantes y el nivel de riesgo identificado en el periodo actual.
        </p>

        <div class="kpi-container">
            <div class="kpi-card">
                <span>Total Alumnos</span>
                <span class="kpi-value">{{ kpis.total }}</span>
            </div>
            <div class="kpi-card">
                <span>En Riesgo Crítico</span>
                <span class="kpi-value">{{ kpis.riesgo }}</span>
            </div>

            <div class="kpi-card">
                {% if not carrera %}
                    <span>Carrera con más Riesgo</span>
                    <span class="kpi-value" style="font-size: 16px;">{{ kpis.carrera_riesgo }}</span>
                {% elif carrera and not grupo %}
                    <span>Grupo con más Riesgo</span>
                    <span class="kpi-value">{{ kpis.grupo_riesgo }}</span>
                {% else %}
                    <span>Promedio General</span>
                    <span class="kpi-value">{{ kpis.promedio }}</span>
                {% endif %}
            </div>
        </div>

        <h2 class="section-title">Análisis de Distribución de Riesgo</h2>
        <p class="explanation">
            La siguiente gráfica ilustra cómo se distribuye el riesgo académico entre las distintas categorías. 
            Es fundamental para priorizar intervenciones en las áreas con mayor concentración de alumnos vulnerables.
        </p>
        <div class="chart">
            <img src="data:image/png;base64,{{ img_riesgo }}" width="450">
        </div>

        <div style="page-break-before: always;"></div>

        <h2 class="section-title">Evolución Temporal del Riesgo</h2>
        <p class="explanation">
            Muestra la tendencia histórica de estudiantes en riesgo a través de los últimos periodos. 
            Un aumento en la línea indica la necesidad de revisar las estrategias de retención académica.
        </p>
        <div class="chart">
            <img src="data:image/png;base64,{{ img_lineas }}" width="550">
        </div>

        <h2 class="section-title">Comparativa de Desempeño</h2>
        <p class="explanation">
            Distribución de promedios generales. Este análisis permite identificar si el rendimiento 
            está concentrado en niveles aprobatorios o si existe una dispersión hacia promedios bajos.
        </p>
        <div class="chart">
            <img src="data:image/png;base64,{{ img_desempeño }}" width="550">
        </div>

        <div class="footer">
            Sistema Vita 360 - Reporte Confidencial para Uso Académico
        </div>
    </body>
    </html>
    """

    from flask import render_template_string
    from weasyprint import HTML
    
    rendered_html = render_template_string(
        html_template,
        fecha=datetime.now().strftime("%d/%m/%Y %H:%M"),
        kpis=kpis,
        carrera=carrera_val,
        grupo=grupo_val,
        img_riesgo=img_riesgo,
        img_desempeño=img_desempeño,
        img_lineas=img_lineas
    )

    # El parámetro encoding="utf-8" asegura que los acentos se procesen bien
    pdf = HTML(string=rendered_html, base_url=".").write_pdf()
    return pdf
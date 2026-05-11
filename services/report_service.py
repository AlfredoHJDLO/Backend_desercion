import os
import base64
import json
import plotly.express as px
import pandas as pd
from datetime import datetime
from flask import render_template_string, current_app
from weasyprint import HTML
from models import ArchivoSubido, Prediccion

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
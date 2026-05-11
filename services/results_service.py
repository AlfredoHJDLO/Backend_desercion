# services/results_service.py
import pandas as pd
import plotly.express as px
import json
from models import ArchivoSubido, Prediccion

def get_paginated_risk_results(user_id, page=1, per_page=10):
    """
    Obtiene los alumnos en riesgo del archivo más reciente del usuario,
    aplicando paginación.
    """
    # 1. Buscamos el archivo subido por el usuario
    archivo = ArchivoSubido.query.filter_by(usuario_id=user_id).first()
    
    if not archivo:
        return {"error": "No se encontró ningún archivo para este usuario."}, 404
        
    if not archivo.procesado:
        return {"error": "El archivo aún se está procesando. Intenta de nuevo en unos segundos."}, 202

    # 2. Consultamos las predicciones filtrando solo las de RIESGO (clase 1)
    query = Prediccion.query.filter_by(archivo_id=archivo.id, prediccion_clase=1)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 3. Formateamos los datos para React
    estudiantes_riesgo = []
    for p in pagination.items:
        estudiantes_riesgo.append({
            "matricula": p.matricula,
            "carrera": p.carrera or "N/A",
            "edad": p.edad,
            "probabilidad": round(p.probabilidad_riesgo * 100, 2), # En porcentaje
            "es_foraneo": p.es_foraneo
        })

    return {
        "success": True,
        "info_paginacion": {
            "total_estudiantes_en_riesgo": pagination.total,
            "paginas_totales": pagination.pages,
            "pagina_actual": pagination.page,
            "tiene_siguiente": pagination.has_next,
            "tiene_anterior": pagination.has_prev
        },
        "estudiantes": estudiantes_riesgo
    }, 200

def get_upload_stats(user_id):
    """
    Genera las gráficas de Plotly basadas en los resultados del archivo subido.
    """
    archivo = ArchivoSubido.query.filter_by(usuario_id=user_id).first()
    if not archivo or not archivo.procesado:
        return {"error": "No hay datos procesados disponibles."}, 404

    # Traemos todas las predicciones de este archivo
    query = Prediccion.query.filter_by(archivo_id=archivo.id).all()
    
    data = [{
        "edad": p.edad,
        "riesgo": p.prediccion_clase,
        "foraneo": p.es_foraneo
    } for p in query]
    
    df = pd.DataFrame(data)

    # Solo estadísticas de los que están en RIESGO
    df_riesgo = df[df['riesgo'] == 1]

    if df_riesgo.empty:
        return {"charts": {}, "message": "No hay alumnos en riesgo para graficar."}, 200

    # Gráfica de Pastel: Edades en Riesgo
    fig_edades = px.pie(df_riesgo, names='edad', title='Distribución de Edades en Riesgo')
    
    # Gráfica de Pastel: Locales vs Foráneos en Riesgo
    fig_foraneo = px.pie(df_riesgo, names='foraneo', title='Estudiantes Foráneos en Riesgo',
                         color_discrete_sequence=['#7E2C2C', '#EA9C9C'])

    return {
        "charts": {
            "pastel_edades": json.loads(fig_edades.to_json()),
            "pastel_foraneos": json.loads(fig_foraneo.to_json())
        }
    }, 200
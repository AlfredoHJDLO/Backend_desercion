from flask import Blueprint, jsonify, request
from flask import send_file, make_response
from services.report_service import generate_full_pdf_report, generate_statistical_pdf_report # <--- Importamos la función para el nuevo endpoint
from services.results_service import get_paginated_risk_results, get_upload_stats # <--- Agrega la importación
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.dashboard_service import get_metadata_service, get_dashboard_data_service
from datetime import datetime
import io

# Creamos el Blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/metadata', methods=['GET'])
def get_metadata():
    """Retorna opciones para dropdowns y el mapa de dependencias"""
    data = get_metadata_service()
    return jsonify(data)

@api_bp.route('/dashboard', methods=['POST'])
def get_dashboard_data():
    """Recibe filtros y retorna KPIs, Tabla y Gráficas para Dashboard General"""
    params = request.json
    data = get_dashboard_data_service(params, is_estudiantes=False)
    return jsonify(data)

@api_bp.route('/estudiantes', methods=['POST'])
def get_dashboard_estudiantes():
    """Recibe filtros y retorna KPIs, Tabla y Gráficas para Dashboard Estudiantes"""
    params = request.json
    print(f"Recibido en /api/estudiantes - Filtros: {params}")
    data = get_dashboard_data_service(params, is_estudiantes=True)
    return jsonify(data)


@api_bp.route('/predicciones', methods=['GET'])
@jwt_required()
def get_predictions():
    """
    Endpoint paginado para obtener alumnos en riesgo.
    Uso: /api/predicciones?page=1&per_page=10
    """
    current_user_id = get_jwt_identity()
    
    # Obtenemos los parámetros de la URL (query params)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    data, status_code = get_paginated_risk_results(current_user_id, page, per_page)
    
    return jsonify(data), status_code

@api_bp.route('/estadisticas_archivo', methods=['GET'])
@jwt_required()
def get_file_stats():
    """
    Endpoint para obtener los JSON de las gráficas de Plotly
    del último archivo procesado por el usuario.
    """
    current_user_id = get_jwt_identity()
    
    data, status_code = get_upload_stats(current_user_id)
    
    return jsonify(data), status_code

@api_bp.route('/reporte/pdf', methods=['GET'])
@jwt_required()
def download_report():
    current_user_id = get_jwt_identity()
    pdf_content, error = generate_full_pdf_report(current_user_id)
    
    if error:
        return jsonify({"error": error}), 400

    # Retornar el PDF como un archivo descargable
    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Reporte_Desercion_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

@api_bp.route('/reporte/dashboard', methods=['POST']) # Cambiado a POST
@jwt_required()
def download_dashboard_report():
    # Obtenemos los filtros desde el cuerpo del JSON
    datos = request.get_json()
    
    filtros = {
        'carreras': datos.get('carreras', ""),
        'grupos': datos.get('grupos', "")
    }
    
    # Generamos el PDF
    pdf_content = generate_statistical_pdf_report(filtros)

    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Reporte_Estadistico_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
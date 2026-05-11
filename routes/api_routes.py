from flask import Blueprint, jsonify, request
from services.results_service import get_paginated_risk_results
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.dashboard_service import get_metadata_service, get_dashboard_data_service

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
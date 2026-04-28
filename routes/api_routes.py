from flask import Blueprint, jsonify, request
from services.dashboard_service import get_metadata_service, get_dashboard_data_service
from services.perdict_service import predict_student_risk

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

@api_bp.route('/predict', methods=['POST'])
def predict_risk():
    """
    Predice el riesgo de deserción de un estudiante por su matrícula.
    """
    params = request.json
    matricula = params.get('matricula')
    
    # Validación simple
    if not matricula:
        return jsonify({"error": "Falta el parámetro 'matricula'."}), 400

    # Llamada al servicio
    data, status_code = predict_student_risk(matricula)
    
    return jsonify(data), status_code
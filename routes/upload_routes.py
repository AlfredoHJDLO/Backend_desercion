import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ArchivoSubido
from services.perdict_service import procesar_archivo_excel

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
@jwt_required() # ¡Protegemos la ruta!
def upload_file():
    """Recibe un archivo Excel y lo asocia al usuario logueado."""
    # 1. Identificamos al usuario gracias al token
    current_user_id = get_jwt_identity()

    # 2. Verificamos que la petición contenga un archivo
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    # 3. Validamos la extensión y guardamos
    if file and allowed_file(file.filename):
        # secure_filename evita ataques inyectando rutas raras en el nombre
        filename = secure_filename(file.filename)
        
        # Le agregamos el ID del usuario al nombre para que no choquen si se llaman igual
        unique_filename = f"user_{current_user_id}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)

        # 4. Registramos el archivo en la base de datos de SQLite
        # Primero buscamos si el usuario ya tenía un archivo y lo actualizamos (o creamos uno nuevo)
        archivo_db = ArchivoSubido.query.filter_by(usuario_id=current_user_id).first()
        
        if archivo_db:
            archivo_db.nombre_archivo = unique_filename
            archivo_db.procesado = False # Como es nuevo, aún no está procesado
        else:
            archivo_db = ArchivoSubido(
                usuario_id=current_user_id, 
                nombre_archivo=unique_filename,
                procesado=False
            )
            db.session.add(archivo_db)
            
        db.session.commit()

        resultado_proceso, status = procesar_archivo_excel(archivo_db.id)

        if status != 200:
            return jsonify(resultado_proceso), status

        return jsonify({
            "success": True, 
            "message": "Archivo subido correctamente",
            "file": unique_filename
        }), 200
        
    return jsonify({"error": "Tipo de archivo no permitido. Solo se acepta .xlsx"}), 400

@upload_bp.route('/status_archivo', methods=['GET'])
@jwt_required()
def check_status():
    """Devuelve el estado del archivo del usuario para que el Frontend sepa qué pantalla mostrar."""
    current_user_id = get_jwt_identity()
    
    archivo_db = ArchivoSubido.query.filter_by(usuario_id=current_user_id).first()
    
    if not archivo_db:
        return jsonify({"has_file": False, "message": "El usuario no ha subido ningún archivo."}), 200
        
    return jsonify({
        "has_file": True,
        "filename": archivo_db.nombre_archivo,
        "procesado": archivo_db.procesado,
        "fecha_subida": archivo_db.fecha_subida
    }), 200
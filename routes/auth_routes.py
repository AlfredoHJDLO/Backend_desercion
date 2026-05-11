# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models import db, Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario (puedes ocultar esta ruta en producción luego)"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    if Usuario.query.filter_by(username=username).first():
        return jsonify({"error": "El usuario ya existe"}), 400

    # Hasheamos la contraseña por seguridad
    hashed_pw = generate_password_hash(password)
    nuevo_usuario = Usuario(username=username, password_hash=hashed_pw)
    
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"success": True, "message": "Usuario creado exitosamente"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicia sesión y devuelve un token JWT"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    usuario = Usuario.query.filter_by(username=username).first()

    # Verificamos si el usuario existe y si la contraseña coincide
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Creamos el token (válido, por ejemplo, por 24 horas)
    access_token = create_access_token(identity=str(usuario.id))
    
    return jsonify({
        "success": True, 
        "access_token": access_token,
        "username": usuario.username
    }), 200
# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Inicializamos la instancia de la base de datos
db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relación: Un usuario puede subir múltiples archivos
    archivos = db.relationship('ArchivoSubido', backref='usuario', lazy=True)

class ArchivoSubido(db.Model):
    __tablename__ = 'archivos_subidos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    procesado = db.Column(db.Boolean, default=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación: Un archivo genera múltiples predicciones (una por alumno)
    predicciones = db.relationship('Prediccion', backref='archivo', lazy=True, cascade="all, delete-orphan")

class Prediccion(db.Model):
    __tablename__ = 'predicciones'
    id = db.Column(db.Integer, primary_key=True)
    archivo_id = db.Column(db.Integer, db.ForeignKey('archivos_subidos.id'), nullable=False)
    
    # Datos extraídos del Excel
    matricula = db.Column(db.String(50), nullable=False)
    grupo = db.Column(db.String(50))
    carrera = db.Column(db.String(100))
    estado = db.Column(db.String(50))
    periodo_actual = db.Column(db.Integer)
    promedio_ciclo_anterior = db.Column(db.Float)
    promedio_general = db.Column(db.Float)
    edad = db.Column(db.Integer)
    es_foraneo = db.Column(db.Boolean)
    
    # Resultados del modelo .h5
    probabilidad_riesgo = db.Column(db.Float, nullable=False)
    prediccion_clase = db.Column(db.Integer, nullable=False)
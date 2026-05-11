# run.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from routes.api_routes import api_bp
from routes.auth_routes import auth_bp
from routes.upload_routes import upload_bp
import os

app = Flask(__name__)
CORS(app)

# Configuraciones de la Base de Datos SQLite y JWT
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'desercion.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Clave secreta para firmar los tokens (en producción, pon esto en un .env)
app.config['JWT_SECRET_KEY'] = 'clave-secreta-super-segura-vita360' 

# Inicializamos las extensiones
db.init_app(app)
jwt = JWTManager(app)

# Configuración para subida de archivos
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Crea la carpeta si no existe
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Límite de 16 MB para evitar archivos gigantes


# Registramos los blueprints (rutas)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')

# Crear las tablas automáticamente antes de la primera petición si no existen
with app.app_context():
    db.create_all()
    print("Base de datos verificada/creada.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask
from flask_cors import CORS
from routes.api_routes import api_bp

app = Flask(__name__)
# Habilitamos CORS
CORS(app)

# Registramos las rutas del blueprint. 
# Todas tendrán automáticamente el prefijo /api (ej. /api/dashboard)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    # Corremos en el puerto 5000 por defecto
    app.run(host='0.0.0.0', port=5000, debug=True)
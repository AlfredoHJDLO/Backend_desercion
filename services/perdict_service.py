import os
import numpy as np
from tensorflow.keras.models import load_model

# Construimos la ruta absoluta al modelo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'cnn_pso_model.h5')

# Cargamos el modelo en la memoria global al iniciar la app
try:
    print("Cargando modelo de predicción...")
    model = load_model(MODEL_PATH)
    print("¡Modelo cargado exitosamente!")
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    model = None

def predict_student_risk(features_list):
    """
    Recibe una lista de 7 características, las formatea para la CNN y retorna la predicción.
    """
    if model is None:
        return {"error": "El modelo predictivo no está disponible."}, 500

    if len(features_list) != 7:
        return {"error": f"El modelo espera exactamente 7 variables, se recibieron {len(features_list)}."}, 400

    try:
        # 1. Convertimos la lista a un arreglo de NumPy
        input_data = np.array(features_list, dtype=np.float32)
        
        # 2. Tu modelo espera la forma (batch_size, steps, channels) -> (1, 7, 1)
        input_reshaped = input_data.reshape(1, 7, 1)
        
        # 3. Hacemos la predicción
        prediccion = model.predict(input_reshaped)
        
        # 4. Extraemos el valor de la probabilidad (suele venir como [[0.85]])
        probabilidad = float(prediccion[0][0])
        
        # 5. Determinamos la clase (1: Riesgo, 0: Sin Riesgo) asumiendo un umbral de 0.5
        es_riesgo = 1 if probabilidad >= 0.5 else 0

        return {
            "success": True,
            "probabilidad_riesgo": round(probabilidad, 4), # Redondeado a 4 decimales
            "prediccion_clase": es_riesgo
        }, 200

    except Exception as e:
        return {"error": f"Error al procesar la predicción: {str(e)}"}, 500
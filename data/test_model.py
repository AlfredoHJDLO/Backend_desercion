import joblib
import os
import numpy as np

# Rutas (ajusta si es necesario)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'rank_01_trial_03_mcc_0.7517.joblib')

try:
    model = joblib.load(MODEL_PATH)
    print("✅ Modelo cargado correctamente.")
    
    # 1. Ver el orden de las clases
    clases = model.classes_
    print(f"\n--- MAPEO DE CLASES ---")
    for i, clase in enumerate(clases):
        print(f"Índice {i}: La clase es '{clase}'")

    # 2. Prueba de predicción rápida
    # Creamos un vector de ejemplo con 15 ceros (o el número de variables de tu modelo)
    # Solo para ver cómo responde predict_proba
    dummy_input = np.zeros((1, 15)) 
    probabilidades = model.predict_proba(dummy_input)
    
    print(f"\n--- EJEMPLO DE SALIDA ---")
    print(f"Salida de predict_proba: {probabilidades}")
    print(f"Si quieres la probabilidad de '{clases[0]}', debes usar [:, 0]")

except Exception as e:
    print(f"❌ Error: {e}")
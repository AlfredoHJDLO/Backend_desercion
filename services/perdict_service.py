import os
import numpy as np
from tensorflow.keras.models import load_model
from services.data_loader import get_dataframe # <-- Importamos tu capa de datos

# Construimos la ruta absoluta al modelo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'cnn_pso_model.h5')

# Cargamos el modelo al iniciar
try:
    print("Cargando modelo de predicción...")
    model = load_model(MODEL_PATH)
    print("¡Modelo cargado exitosamente!")
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    model = None

def predict_student_risk(matricula):
    """
    Busca al estudiante por matrícula, calcula las 7 variables para el modelo
    y retorna la predicción de riesgo.
    """
    if model is None:
        return {"error": "El modelo predictivo no está disponible."}, 500

    df = get_dataframe()
    
    # 1. Buscamos al estudiante. 
    # Convertimos ambos lados a string para evitar errores si Pandas lo lee como int y React manda string.
    estudiante = df[df['MATRÍCULA'].astype(str) == str(matricula)]
    
    if estudiante.empty:
        return {"error": f"No se encontró ningún estudiante con la matrícula {matricula}."}, 404

    # Tomamos la primera fila (la matrícula debería ser única)
    row = estudiante.iloc[0]

    try:
        # 2. Cálculos de las 7 variables en el orden estricto del modelo
        
        # V1: Género
        f1_genero = float(row['GENERO_ENC'])
        
        # V2: Locales o foráneos (Región 69 = 0, Distinto = 1)
        region = float(row['REGION'])
        f2_local_foraneo = 0.0 if region == 69.0 else 1.0
        
        # V3: Edad normalizada: (EDAD-16)/(30-16)
        edad = float(row['EDAD'])
        f3_edad_norm = (edad - 16.0) / (30.0 - 16.0)
        
        # V4: 1ER_SEM_NORM: PROMEDIO_CICLO_ANTERIOR / 10
        prom_ciclo_ant = float(row['PROMEDIO CICLO ANTERIOR'])
        f4_1er_sem_norm = prom_ciclo_ant / 10.0
        
        # V5: 2ER_SEM_NORM: (PROMEDIO_CICLO_ANTERIOR + PROMEDIO_GENERAL) / 20
        prom_general = float(row['PROMEDIO GENERAL'])
        f5_2er_sem_norm = (prom_ciclo_ant + prom_general) / 20.0
        
        # V6: Tendencia normalizada (Valor estático temporal)
        f6_tendencia_norm = 0.875984252
        
        # V7: Prom_gen_normalizado: PROMEDIO_GENERAL / 10
        f7_prom_gen_norm = prom_general / 10.0
        
        # 3. Formamos la lista de características para la CNN
        features_list = [
            f1_genero,
            f2_local_foraneo,
            f3_edad_norm,
            f4_1er_sem_norm,
            f5_2er_sem_norm,
            f6_tendencia_norm,
            f7_prom_gen_norm
        ]
        
        # 4. Formateamos para el modelo .h5 (1, 7, 1)
        input_data = np.array(features_list, dtype=np.float32)
        input_reshaped = input_data.reshape(1, 7, 1)
        
        # 5. Predicción
        prediccion = model.predict(input_reshaped)
        probabilidad = float(prediccion[0][0])
        es_riesgo = 1 if probabilidad >= 0.5 else 0

        return {
            "success": True,
            "matricula": matricula,
            "probabilidad_riesgo": round(probabilidad, 4),
            "prediccion_clase": es_riesgo,
            # Retornar las variables calculadas es buena práctica para poder hacer debug desde el front
            "metricas_calculadas": features_list 
        }, 200

    except Exception as e:
        return {"error": f"Error interno al calcular variables: {str(e)}"}, 500
import os
import numpy as np
from tensorflow.keras.models import load_model
from services.data_loader import get_dataframe

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
    Busca al estudiante por matrícula, calcula las variables para el modelo,
    y retorna la información del alumno junto con su predicción de riesgo.
    """
    if model is None:
        return {"error": "El modelo predictivo no está disponible."}, 500

    df = get_dataframe()
    
    # 1. Buscamos al estudiante
    estudiante = df[df['MATRÍCULA'].astype(str) == str(matricula)]
    
    if estudiante.empty:
        return {"error": f"No se encontró ningún estudiante con la matrícula {matricula}."}, 404

    row = estudiante.iloc[0]

    try:
        # --- EXTRACCIÓN DE DATOS PARA LA RESPUESTA ---
        grupo = str(row['GRUPO'])
        carrera = str(row['CARRERA'])
        estado = str(row['ESTADO'])
        periodo_actual = int(row['PERIODO ACTUAL'])
        prom_ciclo_ant = float(row['PROMEDIO CICLO ANTERIOR'])
        prom_general = float(row['PROMEDIO GENERAL'])
        edad = int(row['EDAD'])
        
        # --- CÁLCULO DE VARIABLES PARA EL MODELO ---
        
        # V1: Género
        f1_genero = float(row['GENERO_ENC'])
        
        # V2: Locales o foráneos (Región 69 = 0, Distinto = 1)
        region = float(row['REGION'])
        es_foraneo = 0.0 if region == 69.0 else 1.0
        
        # V3: Edad normalizada
        f3_edad_norm = (edad - 16.0) / (30.0 - 16.0)
        
        # V4: 1ER_SEM_NORM
        f4_1er_sem_norm = prom_ciclo_ant / 10.0
        
        # V5: 2ER_SEM_NORM
        f5_2er_sem_norm = (prom_ciclo_ant + prom_general) / 20.0
        
        # V6: Tendencia normalizada (Nueva fórmula min-max)
        tendencia = f5_2er_sem_norm - f4_1er_sem_norm
        min_tendencia = -3.296296296
        max_tendencia = 0.46666666666666
        f6_tendencia_norm = (tendencia - min_tendencia) / (max_tendencia - min_tendencia)
        
        # V7: Prom_gen_normalizado
        f7_prom_gen_norm = prom_general / 10.0
        
        # Formamos la lista de características para la CNN
        features_list = [
            f1_genero,
            es_foraneo,
            f3_edad_norm,
            f4_1er_sem_norm,
            f5_2er_sem_norm,
            f6_tendencia_norm,
            f7_prom_gen_norm
        ]
        
        # --- PREDICCIÓN ---
        input_data = np.array(features_list, dtype=np.float32).reshape(1, 7, 1)
        prediccion = model.predict(input_data)
        probabilidad = float(prediccion[0][0])
        es_riesgo = 1 if probabilidad >= 0.5 else 0

        # --- CONSTRUCCIÓN DE LA RESPUESTA JSON ---
        return {
            "success": True,
            "estudiante": {
                "matricula": matricula,
                "grupo": grupo,
                "carrera": carrera,
                "estado": estado,
                "periodo_actual": periodo_actual,
                "promedio_ciclo_anterior": prom_ciclo_ant,
                "promedio_general": prom_general,
                "edad": edad,
                "es_foraneo": bool(es_foraneo) # Convertimos el 1.0/0.0 a True/False para mejor lectura en React
            },
            "prediccion": {
                "probabilidad_riesgo": round(probabilidad, 4),
                "prediccion_clase": es_riesgo
            }
        }, 200

    except Exception as e:
        return {"error": f"Error interno al calcular variables: {str(e)}"}, 500
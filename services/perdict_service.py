import os
import joblib
import pandas as pd
import numpy as np
from models import db, ArchivoSubido, Prediccion
from flask import current_app

# --- 1. Carga de Artefactos de ML ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'rank_01_trial_03_mcc_0.7517.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'data', 'scaler.joblib')

try:
    modelo_rf = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("¡Modelo y Escalador cargados exitosamente!")
except Exception as e:
    print(f"Error al cargar artefactos: {e}")
    modelo_rf = None
    scaler = None

# --- 2. Listas de Columnas (Contrato Estricto) ---

# Las 48 variables finales que el modelo RF necesita
# Reemplaza tu bloque ORDEN_COLUMNAS_FINAL por este:

# Las 15 variables finales exactas con las que se entrenó el modelo, 
# manteniendo el orden de aparición del dataset original
ORDEN_COLUMNAS_FINAL = [
    "Displaced",
    "Debtor",
    "Tuition fees up to date",
    "Gender",
    "Scholarship holder",
    "Age at enrollment",
    "Curricular units 1st sem (enrolled)",
    "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (approved)",
    "Unemployment rate",
    "Approval_rate_1st_sem",
    "Approval_rate_2nd_sem",
    "Application mode_39",
    "Father's qualification_37",
    "Mother's occupation_9"
]
# Todas las variables que espera el StandardScaler (Extraídas del archivo 03)
# Omitimos 'Target' porque el escalador solo transforma las características X.
COLUMNAS_ESCALADOR = [
    "Daytime/evening attendance", "Previous qualification (grade)", "Admission grade", 
    "Displaced", "Educational special needs", "Debtor", "Tuition fees up to date", 
    "Gender", "Scholarship holder", "Age at enrollment", "International", 
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)", 
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)", 
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (without evaluations)", 
    "Curricular units 2nd sem (credited)", "Curricular units 2nd sem (enrolled)", 
    "Curricular units 2nd sem (evaluations)", "Curricular units 2nd sem (approved)", 
    "Curricular units 2nd sem (grade)", "Curricular units 2nd sem (without evaluations)", 
    "Unemployment rate", "Inflation rate", "GDP", "Approval_rate_1st_sem", "Approval_rate_2nd_sem", 
    "Marital status_2", "Marital status_3", "Marital status_4", "Marital status_5", "Marital status_6", 
    "Application mode_2", "Application mode_5", "Application mode_7", "Application mode_10", 
    "Application mode_15", "Application mode_16", "Application mode_17", "Application mode_18", 
    "Application mode_26", "Application mode_27", "Application mode_39", "Application mode_42", 
    "Application mode_43", "Application mode_44", "Application mode_51", "Application mode_53", 
    "Application mode_57", "Application order_1", "Application order_2", "Application order_3", 
    "Application order_4", "Application order_5", "Application order_6", "Application order_9", 
    "Course_171", "Course_8014", "Course_9003", "Course_9070", "Course_9085", "Course_9119", 
    "Course_9130", "Course_9147", "Course_9238", "Course_9254", "Course_9500", "Course_9556", 
    "Course_9670", "Course_9773", "Course_9853", "Course_9991", "Previous qualification_2", 
    "Previous qualification_3", "Previous qualification_4", "Previous qualification_5", 
    "Previous qualification_6", "Previous qualification_9", "Previous qualification_10", 
    "Previous qualification_12", "Previous qualification_14", "Previous qualification_15", 
    "Previous qualification_19", "Previous qualification_38", "Previous qualification_39", 
    "Previous qualification_40", "Previous qualification_42", "Previous qualification_43", 
    "Nacionality_2", "Nacionality_6", "Nacionality_11", "Nacionality_13", "Nacionality_14", 
    "Nacionality_17", "Nacionality_21", "Nacionality_22", "Nacionality_24", "Nacionality_25", 
    "Nacionality_26", "Nacionality_32", "Nacionality_41", "Nacionality_62", "Nacionality_100", 
    "Nacionality_101", "Nacionality_103", "Nacionality_105", "Nacionality_108", "Nacionality_109", 
    "Mother's qualification_2", "Mother's qualification_3", "Mother's qualification_4", 
    "Mother's qualification_5", "Mother's qualification_6", "Mother's qualification_9", 
    "Mother's qualification_10", "Mother's qualification_11", "Mother's qualification_12", 
    "Mother's qualification_14", "Mother's qualification_18", "Mother's qualification_19", 
    "Mother's qualification_22", "Mother's qualification_26", "Mother's qualification_27", 
    "Mother's qualification_29", "Mother's qualification_30", "Mother's qualification_34", 
    "Mother's qualification_35", "Mother's qualification_36", "Mother's qualification_37", 
    "Mother's qualification_38", "Mother's qualification_39", "Mother's qualification_40", 
    "Mother's qualification_41", "Mother's qualification_42", "Mother's qualification_43", 
    "Mother's qualification_44", "Father's qualification_2", "Father's qualification_3", 
    "Father's qualification_4", "Father's qualification_5", "Father's qualification_6", 
    "Father's qualification_9", "Father's qualification_10", "Father's qualification_11", 
    "Father's qualification_12", "Father's qualification_13", "Father's qualification_14", 
    "Father's qualification_18", "Father's qualification_19", "Father's qualification_20", 
    "Father's qualification_22", "Father's qualification_25", "Father's qualification_26", 
    "Father's qualification_27", "Father's qualification_29", "Father's qualification_30", 
    "Father's qualification_31", "Father's qualification_33", "Father's qualification_34", 
    "Father's qualification_35", "Father's qualification_36", "Father's qualification_37", 
    "Father's qualification_38", "Father's qualification_39", "Father's qualification_40", 
    "Father's qualification_41", "Father's qualification_42", "Father's qualification_43", 
    "Father's qualification_44", "Mother's occupation_1", "Mother's occupation_2", 
    "Mother's occupation_3", "Mother's occupation_4", "Mother's occupation_5", 
    "Mother's occupation_6", "Mother's occupation_7", "Mother's occupation_8", 
    "Mother's occupation_9", "Mother's occupation_10", "Mother's occupation_90", 
    "Mother's occupation_99", "Mother's occupation_122", "Mother's occupation_123", 
    "Mother's occupation_125", "Mother's occupation_131", "Mother's occupation_132", 
    "Mother's occupation_134", "Mother's occupation_141", "Mother's occupation_143", 
    "Mother's occupation_144", "Mother's occupation_151", "Mother's occupation_152", 
    "Mother's occupation_153", "Mother's occupation_171", "Mother's occupation_173", 
    "Mother's occupation_175", "Mother's occupation_191", "Mother's occupation_192", 
    "Mother's occupation_193", "Mother's occupation_194", "Father's occupation_1", 
    "Father's occupation_2", "Father's occupation_3", "Father's occupation_4", 
    "Father's occupation_5", "Father's occupation_6", "Father's occupation_7", 
    "Father's occupation_8", "Father's occupation_9", "Father's occupation_10", 
    "Father's occupation_90", "Father's occupation_99", "Father's occupation_101", 
    "Father's occupation_102", "Father's occupation_103", "Father's occupation_112", 
    "Father's occupation_114", "Father's occupation_121", "Father's occupation_122", 
    "Father's occupation_123", "Father's occupation_124", "Father's occupation_131", 
    "Father's occupation_132", "Father's occupation_134", "Father's occupation_135", 
    "Father's occupation_141", "Father's occupation_143", "Father's occupation_144", 
    "Father's occupation_151", "Father's occupation_152", "Father's occupation_153", 
    "Father's occupation_154", "Father's occupation_161", "Father's occupation_163", 
    "Father's occupation_171", "Father's occupation_172", "Father's occupation_174", 
    "Father's occupation_175", "Father's occupation_181", "Father's occupation_182", 
    "Father's occupation_183", "Father's occupation_192", "Father's occupation_193", 
    "Father's occupation_194", "Father's occupation_195"
]

def procesar_archivo_excel(archivo_id):
    if not modelo_rf or not scaler:
        return {"error": "Servicio de IA no disponible (Artefactos faltantes)."}, 500

    archivo_db = ArchivoSubido.query.get(archivo_id)
    if not archivo_db:
        return {"error": "Archivo no encontrado en la base de datos."}, 404

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], archivo_db.nombre_archivo)
    
    try:
        # --- CARGA INICIAL ---
# --- CARGA INICIAL ---
        if filepath.endswith('.csv'):
            # Intentamos leer con coma por defecto
            df_raw = pd.read_csv(filepath)
            # Si solo detecta 1 columna, significa que el separador era punto y coma
            if len(df_raw.columns) == 1:
                df_raw = pd.read_csv(filepath, sep=';')
        else:
            df_raw = pd.read_excel(filepath)
            
        df_proc = df_raw.copy()
        # --- FASE 1: LIMPIEZA ---
        # Corregimos nombres si vienen mal
        if 'Daytime/evening attendance\t' in df_proc.columns:
            df_proc.rename(columns={'Daytime/evening attendance\t': 'Daytime/evening attendance'}, inplace=True)

        # --- FASE 2: INGENIERÍA DE VARIABLES ---
        df_proc['Approval_rate_1st_sem'] = np.where(
            df_proc['Curricular units 1st sem (enrolled)'] == 0, 0, 
            df_proc['Curricular units 1st sem (approved)'] / df_proc['Curricular units 1st sem (enrolled)']
        )
        df_proc['Approval_rate_2nd_sem'] = np.where(
            df_proc['Curricular units 2nd sem (enrolled)'] == 0, 0, 
            df_proc['Curricular units 2nd sem (approved)'] / df_proc['Curricular units 2nd sem (enrolled)']
        )

        # --- FASE 3: CODIFICACIÓN (One-Hot Encoding) ---
        nominals = ['Marital status', 'Application mode', 'Application order', 'Course', 
                    'Previous qualification', 'Nacionality', "Mother's qualification", 
                    "Father's qualification", "Mother's occupation", "Father's occupation"]
        
        df_encoded = pd.get_dummies(df_proc, columns=nominals, drop_first=True)

        # --- FASE CRÍTICA: ALINEACIÓN (Para el Scaler) ---
        # 1. Rellenar columnas faltantes con 0
        for col in COLUMNAS_ESCALADOR:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
                
        # 2. Ordenar las columnas estrictamente como el scaler las conoció en el entrenamiento
        df_encoded = df_encoded[COLUMNAS_ESCALADOR]

        # --- FASE 5: ESCALADO (StandardScaler) ---
        X_scaled = pd.DataFrame(scaler.transform(df_encoded), columns=COLUMNAS_ESCALADOR)

        # --- FASE 6: SELECCIÓN ---
        X_final = X_scaled[ORDEN_COLUMNAS_FINAL]
        
        # --- PREDICCIÓN FINAL ---
        # Usamos [:, 0] porque el índice 0 es la clase '0' (Dropout/Deserción)
        probabilidades = modelo_rf.predict_proba(X_final)[:, 0]
        clases = modelo_rf.predict(X_final)

        # --- PERSISTENCIA EN SQLITE (ORDENADA POR RIESGO) ---
        Prediccion.query.filter_by(archivo_id=archivo_id).delete()
        
        # 1. Creamos una lista temporal con los datos para poder ordenarlos
        lista_resultados = []
        for index, row in df_raw.iterrows():
            lista_resultados.append({
                "archivo_id": archivo_id,
                "matricula": str(row.get('Matricula', row.get('ID', f'ID_{index+1}'))),
                "carrera": str(row.get('Course', 'N/A')), 
                "edad": int(row.get('Age at enrollment', 0)),
                "es_foraneo": bool(row.get('Displaced', False)),
                "probabilidad_riesgo": float(probabilidades[index]),
                "prediccion_clase": int(clases[index])
            })

        # 2. Ordenamos: Mayor probabilidad de deserción primero
        # La lógica es: si P(dropout) = 0.95, va hasta arriba.
        lista_ordenada = sorted(lista_resultados, key=lambda x: x['probabilidad_riesgo'], reverse=True)

        # 3. Convertimos a objetos de SQLAlchemy y guardamos
        nuevas_preds = [Prediccion(**datos) for datos in lista_ordenada]
        
        db.session.bulk_save_objects(nuevas_preds)
        archivo_db.procesado = True
        db.session.commit()

        return {"success": True, "message": f"Pipeline finalizado. {len(df_raw)} alumnos procesados y ordenados por riesgo."}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error en el pipeline de datos: {str(e)}"}, 500
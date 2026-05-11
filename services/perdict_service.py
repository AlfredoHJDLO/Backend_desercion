import os
import joblib
import pandas as pd
from models import db, ArchivoSubido, Prediccion
from flask import current_app

# Caminho para o modelo Random Forest (.joblib)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'rank_01_trial_03_mcc_0.7517.joblib')

try:
    print("A carregar modelo Random Forest...")
    modelo_rf = joblib.load(MODEL_PATH)
    print("Modelo carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")
    modelo_rf = None

# Ordem EXATA das 48 variáveis
ORDEN_COLUMNAS = [
    "Previous qualification (grade)", "Admission grade", "Displaced", "Debtor",
    "Tuition fees up to date", "Gender", "Scholarship holder", "Age at enrollment",
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (without evaluations)",
    "Curricular units 2nd sem (credited)", "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (evaluations)", "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)", "Curricular units 2nd sem (without evaluations)",
    "Unemployment rate", "Inflation rate", "GDP", "Approval_rate_1st_sem",
    "Approval_rate_2nd_sem", "Application mode_17", "Application mode_39",
    "Application order_1", "Application order_2", "Course_9119", "Course_9238",
    "Course_9500", "Course_9853", "Mother's qualification_3", "Mother's qualification_19",
    "Mother's qualification_37", "Father's qualification_19", "Father's qualification_37",
    "Father's qualification_38", "Mother's occupation_3", "Mother's occupation_4",
    "Mother's occupation_5", "Mother's occupation_9", "Father's occupation_3",
    "Father's occupation_4", "Father's occupation_5", "Father's occupation_7",
    "Father's occupation_9"
]

def procesar_archivo_excel(archivo_id):
    """
    Lê o ficheiro subido, realiza a predição em lote e guarda os dados
    detalhados (idade, deslocado, etc.) para as estatísticas e tabela.
    """
    if modelo_rf is None:
        return {"error": "O modelo não está disponível."}, 500

    archivo_db = ArchivoSubido.query.get(archivo_id)
    if not archivo_db:
        return {"error": "Ficheiro não encontrado."}, 404

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], archivo_db.nombre_archivo)
    
    try:
        # 1. Leitura do ficheiro
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        
        # 2. Validação de colunas
        columnas_faltantes = [col for col in ORDEN_COLUMNAS if col not in df.columns]
        if columnas_faltantes:
            return {"error": f"Faltam colunas: {columnas_faltantes[:3]}..."}, 400

        # 3. Preparação dos dados para o modelo
        X_input = df[ORDEN_COLUMNAS]

        # 4. Inferência (Predição)
        probabilidades = modelo_rf.predict_proba(X_input)[:, 1] 
        clases_predichas = modelo_rf.predict(X_input)

        # 5. Limpeza de dados antigos deste ficheiro
        Prediccion.query.filter_by(archivo_id=archivo_id).delete()

        # 6. Mapeamento e Guardado dos resultados
        nuevas_predicciones = []
        for index, row in df.iterrows():
            # Identificação do aluno
            matricula_val = str(row.get('Matricula', row.get('ID', f'ID_{index+1}')))
            
            # Extração de dados para as estatísticas
            nueva_prediccion = Prediccion(
                archivo_id=archivo_id,
                matricula=matricula_val,
                # No modelo de 48 variáveis, 'Displaced' indica se é de fora
                es_foraneo=bool(row['Displaced']), 
                # 'Age at enrollment' é a idade do aluno
                edad=int(row['Age at enrollment']),
                probabilidad_riesgo=float(probabilidades[index]),
                prediccion_clase=int(clases_predichas[index]),
                # Para a carreira, como as colunas são codificadas, guardamos o ID se disponível
                carrera="Ver colunas Course_XXXX" 
            )
            nuevas_predicciones.append(nueva_prediccion)

        # Inserção em massa (Bulk Insert)
        db.session.bulk_save_objects(nuevas_predicciones)
        
        # Atualizar estado do ficheiro
        archivo_db.procesado = True
        db.session.commit()

        return {
            "success": True, 
            "message": f"Foram processados {len(df)} alunos com sucesso."
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro no processamento: {str(e)}"}, 500
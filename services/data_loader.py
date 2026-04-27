import pandas as pd
import os

# Construimos la ruta absoluta al dataset para evitar problemas de directorios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'DATASET_FINAL_UTM.csv')

# 1. CARGA Y PREPARACIÓN DE DATOS (Se ejecuta al iniciar la app)
df = pd.read_csv(CSV_PATH)

df['DOMICILIO'] = df['DOMICILIO'].fillna('DESCONOCIDO')
for col in ['CODIGO_POSTAL', 'REGION']:
    df[col] = df[col].fillna(df[col].mode()[0])

def get_dataframe():
    """Retorna la instancia global del DataFrame ya limpio."""
    return df
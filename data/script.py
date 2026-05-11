import joblib

# Cargar el modelo
modelo = joblib.load('rank_01_trial_03_mcc_0.7517.joblib')

# Imprimir las variables en el orden exacto que espera el modelo
print(modelo.feature_names_in_)
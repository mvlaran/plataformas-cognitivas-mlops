import joblib
import pandas as pd
import json
import numpy as np
from flask import Flask, request, render_template
import sys

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

app = Flask(__name__, template_folder="templates")
app.json_encoder = NpEncoder
modelo = None

@app.route("/", methods=['GET', 'POST'])
def call_home(request = request):
    return render_template('index.html')

@app.route("/predict", methods=['POST'])
def call_predict(request = request):
    print(request.values)
    
    json_ = request.json
    campos = pd.DataFrame(json_)

    if campos.shape[0] == 0:
        return "Dados de chamada da API estão incorretos.", 400

    colunas = ['Gender', 'approv_in_adv', 'property_value', 'income', 'Credit_Score',
              'age', 'Region']
    for coluna in campos.columns:
        if coluna not in colunas:
            return "Dados de chamada da API estão incorretos. (structure)", 400
    
    for coluna in colunas:
        if coluna not in campos.columns:
            return "Dados de chamada da API estão incorretos. (missing)", 400
    
    if pd.api.types.is_numeric_dtype(campos['property_value']):
        if not (campos['property_value'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric pv)", 400
    if pd.api.types.is_numeric_dtype(campos['income']):
        if not (campos['income'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric in)", 400
    if pd.api.types.is_numeric_dtype(campos['Credit_Score']):
        if not (campos['Credit_Score'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric cs)", 400
    
    categoricas = ['Gender', 'approv_in_adv', 'age', 'Region']
    categoricas_val = {
        'Gender': ['Female', 'Joint', 'Male'],
        'approv_in_adv' : ['nopre', 'pre'],
        'age' : ['<25', '25-34', '35-44', '45-54', '55-64', '65-74', '>74'],
        'Region' : ['North', 'North-East', 'central', 'south']
    }

    encoders = {}

    for categorica in categoricas:
        if categorica not in encoders:
            encoders[categorica] = joblib.load( 'models/loan_' + categorica + '_label_encoder.joblib')
        for valor in campos[categorica].unique():
          if valor not in categoricas_val[categorica]:
              return "Dados de chamada da API estão incorretos. (categorical)", 400
        campos[categorica] = encoders[categorica].transform(campos[categorica])

    print("Predizendo para {0} registros".format(campos.shape[0]))
    
    prediction = predict_model.predict(campos)
    predict_proba = predict_model.predict_proba(campos)

    ret = json.dumps({'prediction': list(prediction),
                      'proba': list(predict_proba)}, cls=NpEncoder)

    return app.response_class(response=ret, mimetype='application/json')

@app.route("/cluster", methods=['POST'])
def call_cluster(request = request):
    print(request.values)

    json_ = request.json
    campos = pd.DataFrame(json_)

    if campos.shape[0] == 0:
        return "Dados de chamada da API estão incorretos.", 400

    colunas = ['Gender', 'approv_in_adv', 'property_value', 'income', 'Credit_Score',
              'age', 'Region']
    for coluna in campos.columns:
        if coluna not in colunas:
            return "Dados de chamada da API estão incorretos. (structure)", 400
    
    for coluna in colunas:
        if coluna not in campos.columns:
            return "Dados de chamada da API estão incorretos. (missing)", 400
    
    if pd.api.types.is_numeric_dtype(campos['property_value']):
        if not (campos['property_value'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric pv)", 400
    if pd.api.types.is_numeric_dtype(campos['income']):
        if not (campos['income'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric in)", 400
    if pd.api.types.is_numeric_dtype(campos['Credit_Score']):
        if not (campos['Credit_Score'] >= 0).all():
            return "Dados de chamada da API estão incorretos. (non-numeric cs)", 400
    
    categoricas = ['Gender', 'approv_in_adv', 'age', 'Region']
    categoricas_val = {
        'Gender': ['Female', 'Joint', 'Male'],
        'approv_in_adv' : ['nopre', 'pre'],
        'age' : ['<25', '25-34', '35-44', '45-54', '55-64', '65-74', '>74'],
        'Region' : ['North', 'North-East', 'central', 'south']
    }

    encoders = {}

    for categorica in categoricas:
        if categorica not in encoders:
            encoders[categorica] = joblib.load( 'models/loan_' + categorica + '_label_encoder.joblib')
        for valor in campos[categorica].unique():
          if valor not in categoricas_val[categorica]:
              return "Dados de chamada da API estão incorretos. (categorical)", 400
        campos[categorica] = encoders[categorica].transform(campos[categorica])

    print("Clusterizando para {0} registros".format(campos.shape[0]))

    numericas = ['property_value', 'income', 'Credit_Score']
    scaler = joblib.load('models/loan_scaler.joblib')
    campos[numericas] = scaler.transform(campos[numericas])

    prediction = cluster_model.predict(campos)
    if isinstance(prediction, int):
        persona = 'north' if prediction == 0 else 'south'
        prop_fraud =  '> 0.5' if persona == 'north' else '<= 0.5'
        ret = json.dumps({'cluster': prediction,
                          'persona': persona,
                          'prop_fraud': prop_fraud}, cls=NpEncoder)
    else:
        personas = []
        prop_frauds = []
        for predict in prediction:
            persona = 'north' if predict == 0 else 'south'
            prop_fraud = '> 0.5' if persona == 'north' else '<= 0.5'
            personas.append(persona)
            prop_frauds.append(prop_fraud)
        ret = json.dumps({'cluster': list(prediction),
                          'persona': list(personas),
                          'prop_fraud': list(prop_frauds)}, cls=NpEncoder)

    return app.response_class(response=ret, mimetype='application/json')

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 1:
        args.append('models/loan_xgb.joblib')
    if len(args) < 2:
        args.append('8080')

    print(args)

    predict_model = joblib.load( 'models/loan_xgb.joblib')
    cluster_model = joblib.load( 'models/loan_kmeans.joblib')
    # app.run(port=8080, host='0.0.0.0')
    app.run(port=args[1], host='0.0.0.0')
    pass


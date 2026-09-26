from __future__ import annotations
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .data import FEATURES

def make_model():
    prep=ColumnTransformer([("numeric",Pipeline([("impute",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler())]),FEATURES)],remainder="drop")
    return Pipeline([("prepare",prep),("model",LogisticRegression(max_iter=1000,class_weight="balanced",random_state=5212))])
def save_model(model,path): joblib.dump(model,path)
def load_model(path): return joblib.load(path)
def explain(model,row):
    base=model.named_steps["prepare"].named_transformers_["numeric"]
    med=base.named_steps["impute"].statistics_[:len(FEATURES)]
    vals=np.array([row.get(f,np.nan) for f in FEATURES],dtype=float); vals=np.where(np.isnan(vals),med,vals)
    scale=base.named_steps["scale"]; coef=model.named_steps["model"].coef_[0][:len(FEATURES)]
    contributions=((vals-scale.mean_[:len(FEATURES)])/scale.scale_[:len(FEATURES)])*coef
    order=np.argsort(np.abs(contributions))[::-1][:4]
    return [{"feature":FEATURES[i],"direction":"higher" if contributions[i]>0 else "lower","contribution":round(float(contributions[i]),3)} for i in order]

from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from .config import ARTIFACT_ROOT
from .data import FEATURES
from .models import load_model
SCHEMA_VERSION="1.0"
def export_contract(task:str, model_path=None, output_dir=None):
    model=load_model(model_path or ARTIFACT_ROOT/f"{task}.joblib")
    prep=model.named_steps["prepare"].named_transformers_["numeric"]
    imputer=prep.named_steps["impute"]; scaler=prep.named_steps["scale"]; classifier=model.named_steps["model"]
    medians=[float(x) for x in imputer.statistics_[:len(FEATURES)]]
    means=[float(x) for x in scaler.mean_[:len(FEATURES)]]; scales=[float(x) for x in scaler.scale_[:len(FEATURES)]]
    coeff=[float(x) for x in classifier.coef_[0][:len(FEATURES)]]
    payload={"schema_version":SCHEMA_VERSION,"task":task,"features":FEATURES,"medians":medians,"means":means,"scales":scales,"coefficients":coeff,"intercept":float(classifier.intercept_[0]),"training":{"model":"logistic_regression","seed":5212,"status":"preliminary_demo"}}
    if any(not math.isfinite(v) for key in ["medians","means","scales","coefficients"] for v in payload[key]): raise ValueError("contract contains non-finite values")
    target=Path(output_dir or ARTIFACT_ROOT/"export");target.mkdir(parents=True,exist_ok=True);path=target/f"{task}.json";path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8");return path

def export_all(output_dir=None): return [export_contract(task,output_dir=output_dir) for task in ["mortality","long_stay","readmission"]]

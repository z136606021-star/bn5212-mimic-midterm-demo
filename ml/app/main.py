from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Literal
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .config import ARTIFACT_ROOT
from .data import FEATURES
from .models import explain, load_model
from .tasks import TASKS, TASK_MAP

app=FastAPI(title="MIMIC-IV Midterm Demo API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],allow_methods=["*"],allow_headers=["*"])

def _json_safe(value):
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, dict): return {key:_json_safe(item) for key,item in value.items()}
    if isinstance(value, list): return [_json_safe(item) for item in value]
    return value

def _summary():
    path=ARTIFACT_ROOT/"summary.json"
    if not path.exists(): raise HTTPException(503,"Demo artifacts are not prepared. Run prepare_demo first.")
    return _json_safe(json.loads(path.read_text(encoding="utf-8")))

class PredictRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    task: Literal["mortality","long_stay","readmission"]
    sample_index: int|None=Field(default=None,ge=0)
    features: dict[str,float|None]|None=None
    @model_validator(mode="after")
    def require_input(self):
        if self.sample_index is None and self.features is None:
            raise ValueError("Provide sample_index or features")
        return self

@app.get("/api/health")
def health(): return {"status":"ok","artifacts_ready":(ARTIFACT_ROOT/"summary.json").exists(),"mode":"preliminary-course-demo"}
@app.get("/api/tasks")
def tasks(): return {"tasks":TASKS,"disclaimer":"Educational demo only; outputs are not diagnoses or clinical recommendations."}
@app.get("/api/summary")
def summary(): return _summary()
@app.get("/api/results")
def results():
    data=_summary(); return {"tasks":data["tasks"],"robustness":data["robustness"],"status":"preliminary_demo"}
@app.post("/api/demo/predict")
def predict(request:PredictRequest):
    data=_summary(); model_path=ARTIFACT_ROOT/f"{request.task}.joblib"
    if not model_path.exists(): raise HTTPException(503,"Requested model artifact is unavailable.")
    if request.features is not None:
        unknown=set(request.features)-set(FEATURES)
        if unknown: raise HTTPException(422,f"Unknown features: {sorted(unknown)}")
        row={name:request.features.get(name) for name in FEATURES}; source="manual teaching input"
    else:
        samples=data.get("demo_samples",[])
        if request.sample_index is None or request.sample_index>=len(samples): raise HTTPException(422,"sample_index is outside the available demo range")
        row={name:samples[request.sample_index].get(name) for name in FEATURES}; source=f"anonymous held-out demo sample {request.sample_index+1}"
    model=load_model(model_path); frame=pd.DataFrame([row],columns=FEATURES); score=float(model.predict_proba(frame)[0,1])
    return {"task":request.task,"task_title":TASK_MAP[request.task]["title"],"ranking_score":round(score,4),"risk_band":"higher" if score>=.66 else "middle" if score>=.33 else "lower","source":source,"top_contributors":explain(model,row),"disclaimer":"Model score from a preliminary course demo; not a diagnosis or calibrated clinical probability."}

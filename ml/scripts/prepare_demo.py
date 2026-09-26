from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from ml.app.config import ARTIFACT_ROOT, RANDOM_SEED
from ml.app.data import FEATURES, build_dataset, patient_split
from ml.app.evaluation import metrics
from ml.app.models import make_model, save_model
from ml.app.model_contract import export_all


def run(max_stays=3000):
    ARTIFACT_ROOT.mkdir(parents=True,exist_ok=True)
    frame=build_dataset(max_stays); frame["split"]=patient_split(frame)
    summary={"cohort":{"stays":len(frame),"patients":int(frame.subject_id.nunique()),"window_hours":24,"adult_first_icu_stay":True},"features":FEATURES,"missingness":{},"tasks":{},"robustness":[]}
    summary["missingness"]={f:round(float(frame[f].isna().mean()),4) for f in FEATURES}
    rng=np.random.default_rng(RANDOM_SEED)
    for task in ["mortality","long_stay","readmission"]:
        train=frame[frame.split=="train"]; val=frame[frame.split=="validation"]; test=frame[frame.split=="test"]
        model=make_model(); model.fit(train[FEATURES],train[task]); score=model.predict_proba(test[FEATURES])[:,1]
        task_metrics=metrics(test[task],score)
        task_metrics.update({"samples":len(frame),"test_samples":len(test),"positives":int(frame[task].sum()),"positive_rate":round(float(frame[task].mean()),4),"status":"preliminary_demo"})
        summary["tasks"][task]=task_metrics
        save_model(model,ARTIFACT_ROOT/f"{task}.joblib")
        if task in {"mortality","long_stay"}:
            for rate in [0.0,0.1,0.25,0.4,0.6]:
                masked=test[FEATURES].copy(); mask=rng.random(masked.shape)<rate; masked=masked.mask(mask)
                m=metrics(test[task],model.predict_proba(masked)[:,1]); summary["robustness"].append({"task":task,"mask_rate":rate,"auroc":m["auroc"],"auprc":m["auprc"],"f1":m["f1"]})
    # Local teaching samples only: never include subject_id/stay_id (public repo must not receive row-level IDs).
    demo_cols=FEATURES+["mortality","long_stay","readmission"]
    demos=frame[frame.split=="test"].sample(min(12,(frame.split=="test").sum()),random_state=RANDOM_SEED)[demo_cols].copy()
    for col in demos.columns: demos[col]=demos[col].where(demos[col].notna(),None)
    summary["demo_samples"]=json.loads(demos.to_json(orient="records"))
    (ARTIFACT_ROOT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    frame[["stay_id","subject_id","split","mortality","long_stay","readmission"]+FEATURES].to_csv(ARTIFACT_ROOT/"demo_features.csv.gz",index=False,compression="gzip")
    export_all()
    print(json.dumps({"artifact":str(ARTIFACT_ROOT),"stays":len(frame),"tasks":summary["tasks"]},indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--max-stays",type=int,default=3000);args=parser.parse_args();run(args.max_stays)

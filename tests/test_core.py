import numpy as np
import pandas as pd
from ml.app.data import FEATURES, patient_split
from ml.app.evaluation import metrics
from ml.app.schemas import PredictionRequest

def test_patient_split_has_no_patient_leakage():
    f=pd.DataFrame({"subject_id":[1,1,2,3,4,5,6,7,8,9]}); s=patient_split(f)
    mapped=pd.DataFrame({"id":f.subject_id,"split":s}).groupby("id").split.nunique()
    assert mapped.max()==1

def test_metrics_are_bounded():
    m=metrics(np.array([0,1,0,1]),np.array([.1,.8,.2,.7]))
    assert m["auroc"]==1 and 0<=m["f1"]<=1

def test_prediction_schema_rejects_unknown_feature():
    try: PredictionRequest(task="mortality",features={"future_los":4})
    except ValueError: return
    assert False

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .config import DATA_ROOT, RANDOM_SEED

VITALS={220045:"heart_rate",220210:"resp_rate",223762:"temperature",220277:"spo2",220179:"sbp",220180:"dbp",220052:"map"}
LABS={50912:"creatinine",52546:"creatinine",50809:"glucose",50931:"glucose",52569:"glucose",50983:"sodium",52623:"sodium",50971:"potassium",52610:"potassium",50811:"hemoglobin",51222:"hemoglobin",51640:"hemoglobin",51301:"wbc",51755:"wbc",51756:"wbc",51265:"platelets",53189:"platelets",50882:"bicarbonate",51006:"bun",52647:"bun"}
BASE_FEATURES=["age","gender_male"]
CLINICAL_FEATURES=list(dict.fromkeys(VITALS.values()))+list(dict.fromkeys(LABS.values()))
FEATURES=BASE_FEATURES+CLINICAL_FEATURES

def _read(path: str, **kwargs): return pd.read_csv(DATA_ROOT/path, **kwargs)

def build_cohort(max_stays=3000):
    stays=_read("icu/icustays.csv",parse_dates=["intime","outtime"])
    adm=_read("hosp/admissions.csv",parse_dates=["admittime","dischtime"],usecols=["subject_id","hadm_id","admittime","dischtime","hospital_expire_flag"])
    patients=_read("hosp/patients.csv",usecols=["subject_id","gender","anchor_age"])
    stays=stays.sort_values(["subject_id","intime"]).drop_duplicates("subject_id",keep="first")
    cohort=stays.merge(adm,on=["subject_id","hadm_id"],how="inner").merge(patients,on="subject_id",how="inner")
    cohort=cohort[(cohort.anchor_age>=18)&(cohort.los>=1)].copy()
    future=adm[["subject_id","admittime"]].rename(columns={"admittime":"next_admittime"})
    joined=cohort[["subject_id","hadm_id","dischtime"]].merge(future,on="subject_id",how="left")
    joined=joined[joined.next_admittime>joined.dischtime]
    next_times=joined.groupby("hadm_id").next_admittime.min()
    cohort["next_admittime"]=cohort.hadm_id.map(next_times)
    gap=(cohort.next_admittime-cohort.dischtime).dt.total_seconds()/86400
    cohort["mortality"]=cohort.hospital_expire_flag.astype(int)
    cohort["long_stay"]=(cohort.los>3).astype(int)
    cohort["readmission"]=gap.between(0,30,inclusive="right").fillna(False).astype(int)
    cohort["age"]=cohort.anchor_age.clip(18,91)
    cohort["gender_male"]=(cohort.gender=="M").astype(float)
    cohort=cohort.sort_values("stay_id")
    if max_stays and len(cohort)>max_stays:
        positive_pool=cohort[(cohort.mortality==1)|(cohort.readmission==1)]
        pos=positive_pool.sample(min(max_stays//2,len(positive_pool)),random_state=RANDOM_SEED)
        rest=cohort.drop(pos.index).sample(max_stays-len(pos),random_state=RANDOM_SEED)
        cohort=pd.concat([pos,rest]).sort_values("stay_id")
    return cohort.reset_index(drop=True)

def _aggregate_chunks(path,id_col,item_map,cohort,chunksize=1_000_000):
    ids=set(cohort[id_col].astype(int)); windows=cohort.set_index(id_col)["intime"]
    records=[]
    for chunk in pd.read_csv(DATA_ROOT/path,usecols=[id_col,"itemid","charttime","valuenum"],chunksize=chunksize):
        chunk=chunk[chunk[id_col].isin(ids)&chunk.itemid.isin(item_map)&chunk.valuenum.notna()].copy()
        if chunk.empty: continue
        chunk["charttime"]=pd.to_datetime(chunk.charttime)
        chunk["intime"]=chunk[id_col].map(windows)
        chunk=chunk[(chunk.charttime>=chunk.intime)&(chunk.charttime<=chunk.intime+pd.Timedelta(hours=24))]
        if chunk.empty: continue
        chunk["feature"]=chunk.itemid.map(item_map)
        records.append(chunk[[id_col,"feature","valuenum"]])
    if not records:return pd.DataFrame(index=cohort[id_col])
    values=pd.concat(records,ignore_index=True)
    return values.groupby([id_col,"feature"]).valuenum.mean().unstack()

def build_dataset(max_stays=3000):
    cohort=build_cohort(max_stays)
    vitals=_aggregate_chunks("icu/chartevents.csv","stay_id",VITALS,cohort)
    labs=_aggregate_chunks("hosp/labevents.csv","hadm_id",LABS,cohort)
    frame=cohort.set_index("stay_id")
    frame=frame.join(vitals,how="left")
    lab_by_stay=labs.reindex(frame.hadm_id).set_axis(frame.index)
    frame=frame.join(lab_by_stay,how="left")
    for col in FEATURES:
        if col not in frame: frame[col]=np.nan
    return frame.reset_index()

def patient_split(frame):
    rng=np.random.default_rng(RANDOM_SEED); ids=frame.subject_id.unique().copy(); rng.shuffle(ids)
    n=len(ids); train=set(ids[:int(.7*n)]); val=set(ids[int(.7*n):int(.85*n)])
    return np.where(frame.subject_id.isin(train),"train",np.where(frame.subject_id.isin(val),"validation","test"))



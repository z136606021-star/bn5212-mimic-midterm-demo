from __future__ import annotations
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, roc_auc_score

def metrics(y_true,score,threshold=.5):
    pred=(np.asarray(score)>=threshold).astype(int); tn,fp,fn,tp=confusion_matrix(y_true,pred,labels=[0,1]).ravel()
    return {"auroc":round(float(roc_auc_score(y_true,score)),4),"auprc":round(float(average_precision_score(y_true,score)),4),"f1":round(float(f1_score(y_true,pred,zero_division=0)),4),"sensitivity":round(float(tp/(tp+fn)),4) if tp+fn else 0.0,"specificity":round(float(tn/(tn+fp)),4) if tn+fp else 0.0,"confusion":{"tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)}}

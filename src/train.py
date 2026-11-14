"""Reproduce split, model selection, threshold selection and one held-out evaluation."""
import hashlib
import json
import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .common import ROOT, FEATURES, CATEGORICAL, NUMERIC, load_data, metrics, validate_inputs

def train():
    df = load_data()
    assert set(df.Status) == {"Dropout", "Enrolled", "Graduate"}
    assert not df.isna().any().any()
    resolved = df[df.Status != "Enrolled"]
    y = resolved.Status.eq("Dropout").astype(int)
    x = validate_inputs(resolved)
    train_ids, rest = train_test_split(x.index, test_size=.4, stratify=y, random_state=42)
    val_ids, test_ids = train_test_split(rest, test_size=.5, stratify=y.loc[rest], random_state=42)
    # All transforms fit within training folds; no global normalization or resampling.
    preprocessing = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ])
    candidates = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic": LogisticRegression(max_iter=2000, random_state=42),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=8, max_features=.8, random_state=42,n_jobs=-1),
        "hist_gradient_boosting": HistGradientBoostingClassifier(max_iter=160, max_leaf_nodes=15,l2_regularization=3,random_state=42),
    }
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    scores, pipelines = [], {}
    for name, estimator in candidates.items():
        pipe = Pipeline([("preprocess",clone(preprocessing)),("classifier",estimator)])
        fold = cross_val_score(pipe,x.loc[train_ids],y.loc[train_ids],cv=cv,scoring="average_precision",n_jobs=1)
        scores.append({"model":name,"cv_ap_mean":float(fold.mean()),"cv_ap_std":float(fold.std()),"fold_scores":fold.tolist()})
        pipelines[name] = pipe
    selected = max(scores,key=lambda a:a["cv_ap_mean"])["model"]
    model = pipelines[selected].fit(x.loc[train_ids],y.loc[train_ids])
    pv = model.predict_proba(x.loc[val_ids])[:,1]
    thresholds=[]
    for t in np.unique(np.r_[0.,pv,1.]):
        m=metrics(y.loc[val_ids],pv,float(t))
        thresholds.append({"threshold":float(t),**{k:m[k] for k in ["precision","recall","f2","flagged"]}})
    eligible=[r for r in thresholds if r["recall"]>=.8]
    choice=max(eligible,key=lambda r:(r["precision"],r["recall"],r["threshold"]))
    threshold=choice["threshold"]
    pt=model.predict_proba(x.loc[test_ids])[:,1]
    result=metrics(y.loc[test_ids],pt,threshold)
    baseline=DummyClassifier(strategy="prior").fit(x.loc[train_ids],y.loc[train_ids])
    pb=baseline.predict_proba(x.loc[test_ids])[:,1]
    rng=np.random.default_rng(42)
    boot=[]
    yt=y.loc[test_ids].to_numpy()
    for _ in range(1000):
        ix=rng.integers(0,len(yt),len(yt))
        if len(np.unique(yt[ix]))==2:
            boot.append(metrics(yt[ix],pt[ix],threshold))
    ci={k:np.quantile([b[k] for b in boot],[.025,.975]).tolist() for k in ["pr_auc_ap","recall","precision"]}
    imp=permutation_importance(model,x.loc[val_ids],y.loc[val_ids],scoring="average_precision",n_repeats=10,random_state=42,n_jobs=1)
    importance=pd.DataFrame({"feature":FEATURES,"ap_decrease_mean":imp.importances_mean,"ap_decrease_std":imp.importances_std}).sort_values("ap_decrease_mean",ascending=False)
    importance.to_csv(ROOT/"reports/permutation_importance.csv",index=False)
    split = {"train":train_ids.tolist(),"validation":val_ids.tolist(),"test":test_ids.tolist(),"unresolved":df.index[df.Status.eq("Enrolled")].tolist()}
    (ROOT/"reports/split_indices.json").write_text(json.dumps(split,indent=2))
    provenance={"source":"https://raw.githubusercontent.com/dicodingacademy/dicoding_dataset/main/students_performance/data.csv","sha256":hashlib.sha256((ROOT/"data/students_performance.csv").read_bytes()).hexdigest(),"rows":len(df),"columns":len(df.columns),"missing_cells":int(df.isna().sum().sum()),"duplicate_rows":int(df.duplicated().sum()),"status_counts":df.Status.value_counts().to_dict(),"python":platform.python_version(),"sklearn":sklearn.__version__}
    bundle={"pipeline":model,"threshold":threshold,"features":FEATURES,"selected_model":selected,"data_sha256":provenance["sha256"],"sklearn_version":sklearn.__version__}
    joblib.dump(bundle,ROOT/"model/dropout_model.joblib")
    predictions=pd.DataFrame({"source_row":test_ids,"actual_dropout":yt,"score":pt,"flagged":pt>=threshold})
    predictions.to_csv(ROOT/"reports/test_predictions.csv",index=False)
    report={"provenance":provenance,"selected_model":selected,"feature_timing":"End of semester one; no semester-two, financial, macroeconomic or demographic fields used. Historical availability not independently time-stamped.","features":FEATURES,"split_counts":{k:len(v) for k,v in split.items()},"cv_results":scores,"threshold":threshold,"threshold_policy":"Highest validation precision subject to dropout recall >= 0.80; proposed target, not an institutional SLA.","validation":metrics(y.loc[val_ids],pv,threshold),"test":result,"dummy_test":metrics(y.loc[test_ids],pb,.5),"test_ci95_bootstrap":ci}
    (ROOT/"reports/metrics.json").write_text(json.dumps(report,indent=2))
    pd.DataFrame(thresholds).to_csv(ROOT/"reports/validation_thresholds.csv",index=False)
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    train()

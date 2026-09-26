TASKS = [
 {"id":"mortality","title":"In-hospital mortality","question":"Can first-24-hour information identify higher-risk ICU stays?","label":"hospital_expire_flag","window":"First 24 hours after ICU admission","type":"prediction"},
 {"id":"long_stay","title":"Prolonged ICU stay","question":"Will this ICU stay exceed three days?","label":"ICU LOS > 3 days","window":"First 24 hours after ICU admission","type":"prediction"},
 {"id":"readmission","title":"30-day readmission","question":"Is another admission observed within 30 days after discharge?","label":"next admission within 30 days","window":"First 24 hours after ICU admission","type":"prediction"},
 {"id":"missingness","title":"Missing-data robustness","question":"How does performance change when observed values are masked?","label":"mortality / long-stay performance","window":"Evaluation-only perturbation","type":"robustness"},
]
TASK_MAP={task["id"]:task for task in TASKS}

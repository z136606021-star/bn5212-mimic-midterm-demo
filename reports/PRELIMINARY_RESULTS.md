# Preliminary Demo Results

Generated from a bounded **1,200-stay smoke/demo cohort**, not a full MIMIC-IV experiment.

| Task | AUROC | AUPRC | F1 | Positive rate |
|---|---:|---:|---:|---:|
| In-hospital mortality | 0.656 | 0.3927 | 0.437 | 0.2433 |
| ICU LOS > 3 days | 0.5703 | 0.5045 | 0.5244 | 0.4233 |
| 30-day observed readmission | 0.5263 | 0.4153 | 0.4596 | 0.39 |

Cohort: 1200 first adult ICU stays; patient-level 70/15/15 split; first 24 hours only. These results are for pipeline and presentation validation. They are not evidence of clinical validity.

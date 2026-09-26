# Early ICU Signals — BN5212 Midterm Demo

Java 17 Spring Boot + Vue 3 teaching demo with a Python prepare/train/export pipeline. It shows three preliminary first-24-hour baselines (mortality, prolonged ICU stay, observed 30-day readmission) plus a missing-data robustness track.

## Safety and scope

This is an **educational demo, not clinical advice**. Outputs are relative model signals for coursework, not diagnoses, treatment recommendations, or validated probabilities. The public repository does **not** include raw MIMIC files or row-level patient/stay records. Keep your local MIMIC extract outside the repo and read-only.

## Architecture

- `ml/` — Python cohort preparation, training, and JSON model-contract export
- `backend/` — Java 17 Spring Boot API (`/api/health`, `/api/tasks`, `/api/summary`, `/api/results`, `/api/demo/predict`)
- `frontend/` — Vue 3 + TypeScript + Vite + Ant Design Vue (proxies `/api` → port 8080)
- `artifacts/` — local model JSON (shareable coefficient exports may be present; patient-level tables are gitignored)

## Prerequisites (teammate machine)

| Tool | Notes |
|------|--------|
| **JDK 17** | Download inside IntelliJ IDEA; name the SDK **`17`** (matches `.idea` `project-jdk-name`). Do not change the OS default Java. |
| **Maven** | Optional if you use `backend/mvnw.cmd` (wrapper). Or install Maven 3.9+ and use `mvn`. |
| **Node.js 20+** | For the Vue dashboard (`npm install` / `npm run dev`). |
| **Python 3.10+** | For prepare/train/export and pytest. |
| **MIMIC-IV v3.1** | PhysioNet credentialed extract, stored **outside** this repo. Only needed to regenerate features/models. |

## Clone and open in IntelliJ IDEA

1. Clone the Canvas repo and open **this folder** (not only `backend/`):

   ```text
   <clone-root>/NUS/BN5212/mimic_midterm_demo
   ```

2. In IDEA: **File → Open** → select `mimic_midterm_demo`.
3. Wait for Maven to import `backend/pom.xml` (module `mimic-demo-backend`).
4. **Project SDK**: File → Project Structure → Project → SDK → **Download JDK…** → version **17** → name it exactly **`17`** (this repo’s `.idea/misc.xml` uses `project-jdk-name="17"`). Leave system `JAVA_HOME` / default `java` alone if you already have another JDK for other work; set `JAVA_HOME` only in the terminal session when using the PowerShell scripts.
5. Shared run configs under `.run/` (no machine-specific JDK path):
   - **MimicDemoApplication** — Spring Boot; working directory `$PROJECT_DIR$/backend`
   - **Frontend Vite** — `npm run dev` in `frontend/`

## One-time local bootstrap

From `mimic_midterm_demo`:

```powershell
# 1) Python env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# 2) Node deps
Set-Location frontend; npm install; Set-Location ..

# 3) Artifacts for the Java/Vue demo
.\scripts\bootstrap-artifacts.ps1
```

`bootstrap-artifacts.ps1` copies `artifacts/summary.example.json` → `artifacts/summary.json` when summary is missing. The example file has **aggregate metrics only** (empty `demo_samples`). Coefficient JSON under `artifacts/export/` is enough for online inference; empty demo cases make the teaching predictor use feature medians.

### Optional: rebuild artifacts from MIMIC (credentialed)

Place your PhysioNet MIMIC-IV **3.1** tree outside the repo (read-only). Copy `.env.example` → `.env` and set:

```text
MIMIC_DATA_ROOT=<your>\physionet.org\files\mimiciv\3.1
DEMO_ARTIFACT_ROOT=./artifacts
```

Then:

```powershell
# PowerShell: load .env into the session if you use one, or set MIMIC_DATA_ROOT explicitly
$env:MIMIC_DATA_ROOT = "D:\data\mimiciv\3.1"
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m ml.scripts.prepare_demo --max-stays 1200
```

This regenerates `summary.json`, `export/*.json`, and gitignored patient-level files (`*.joblib`, `demo_features.csv.gz`). **Do not commit** those patient-level outputs to the public GitHub repo.

## Run backend and frontend

### IntelliJ

1. Ensure artifacts exist (`bootstrap-artifacts.ps1` or prepare step).
2. Run **MimicDemoApplication**, then **Frontend Vite**.
3. Open http://localhost:5173 (API: http://localhost:8080).

### Scripts / terminal

Set `JAVA_HOME` to your IDEA JDK 17 home for this session only (example path shape):

```powershell
$env:JAVA_HOME = "$env:USERPROFILE\.jdks\<your-jdk-17-folder>"
.\scripts\run-backend.ps1
.\scripts\run-frontend.ps1
```

`run-backend.ps1` prefers `backend\mvnw.cmd` when present, otherwise `mvn`.

### Docker (optional)

Requires Docker. Model JSON is mounted from `./artifacts`; raw MIMIC is never copied into images.

```powershell
.\scripts\bootstrap-artifacts.ps1
docker compose up -d --build
```

- Frontend: http://localhost:5173  
- Backend health: http://localhost:8080/api/health  

```powershell
docker compose down
```

## Verification

```powershell
.\scripts\verify.ps1
```

Runs pytest, Vitest, the Vue production build, and Java tests (`mvnw` / `mvn`). Java tests need `JAVA_HOME` pointing at JDK 17.

## Interpretation limits

The bounded cohort is for a fast course presentation, not full-population inference. Readmission means an observed subsequent admission within 30 days. Missingness masking is a synthetic reliability test. External validation, calibration, fairness review, clinical evaluation, and prospective study would be required before any real use.

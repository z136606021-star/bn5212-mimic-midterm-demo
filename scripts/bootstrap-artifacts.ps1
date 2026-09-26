$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

$artifacts = Join-Path (Get-Location) "artifacts"
$example = Join-Path $artifacts "summary.example.json"
$summary = Join-Path $artifacts "summary.json"
$exportDir = Join-Path $artifacts "export"

if (-not (Test-Path $example)) {
  Write-Error "Missing $example — clone may be incomplete."
}

New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

if (-not (Test-Path $summary)) {
  Copy-Item $example $summary
  Write-Host "Created artifacts/summary.json from summary.example.json (aggregate metrics; empty demo_samples)."
} else {
  Write-Host "artifacts/summary.json already present — left unchanged."
}

$required = @("mortality.json", "long_stay.json", "readmission.json")
$missing = @($required | Where-Object { -not (Test-Path (Join-Path $exportDir $_)) })
if ($missing.Count -gt 0) {
  Write-Error ("Missing model contracts in artifacts/export: {0}. Re-clone or run prepare_demo after configuring MIMIC_DATA_ROOT." -f ($missing -join ", "))
}

Write-Host "Artifacts ready for the Java/Vue demo (export/*.json + summary.json)."
Write-Host "Educational demo only — not clinical advice. Do not commit patient-level CSV/joblib outputs."

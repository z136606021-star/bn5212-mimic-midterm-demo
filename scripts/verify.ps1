$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
$env:PYTHONPATH = (Get-Location).Path
& .\.venv\Scripts\python.exe -m pytest -q
Set-Location frontend
npm test
npm run build
if (-not $env:JAVA_HOME -or -not (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
  Write-Error "Set JAVA_HOME to a JDK 17 home before Java tests (e.g. the JDK registered in IntelliJ as SDK name '17')."
}
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Set-Location ..\backend
if (Test-Path ".\mvnw.cmd") {
  .\mvnw.cmd test
} else {
  mvn test
}

$ErrorActionPreference = "Stop"
if (-not $env:JAVA_HOME -or -not (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
  Write-Error "Set JAVA_HOME to a JDK 17 home before running the backend (e.g. the JDK registered in IntelliJ as SDK name '17')."
}
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Set-Location "$PSScriptRoot\..\backend"
if (Test-Path ".\mvnw.cmd") {
  .\mvnw.cmd spring-boot:run
} else {
  mvn spring-boot:run
}

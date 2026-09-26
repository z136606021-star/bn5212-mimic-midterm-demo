# Optional helper: set JAVA_HOME to a JDK 17 before running backend scripts.
# Prefer the JDK registered in IntelliJ (Project Structure → SDKs). Example:
#   $env:JAVA_HOME = "$env:USERPROFILE\.jdks\<your-jdk-17-folder>"
if (-not $env:JAVA_HOME -or -not (Test-Path "$env:JAVA_HOME\bin\java.exe")) {
  Write-Error "Set JAVA_HOME to a JDK 17 home (bin\java.exe must exist). Do not use a removed Adoptium system install."
}
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

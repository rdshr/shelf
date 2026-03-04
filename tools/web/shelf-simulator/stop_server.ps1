$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $scriptDir ".run\server.pid"

if (-not (Test-Path $pidFile)) {
  Write-Host "No PID file found. Server may already be stopped."
  exit 0
}

$pidText = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $pidText -or -not ($pidText -match "^\d+$")) {
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  Write-Host "Invalid PID file removed."
  exit 0
}

$pid = [int]$pidText
$proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
if ($proc) {
  Stop-Process -Id $pid -Force
  Write-Host "Stopped server process PID=$pid"
} else {
  Write-Host "Process PID=$pid not found."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue

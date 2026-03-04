param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
$serverScript = Join-Path $scriptDir "server.py"
$runDir = Join-Path $scriptDir ".run"
$pidFile = Join-Path $runDir "server.pid"
$outLog = Join-Path $runDir "server.out.log"
$errLog = Join-Path $runDir "server.err.log"

if (-not (Test-Path $serverScript)) {
  throw "server.py not found: $serverScript"
}

New-Item -ItemType Directory -Path $runDir -Force | Out-Null

function Test-Health([string]$url) {
  try {
    $resp = Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 2
    return $resp.ok -eq $true
  } catch {
    return $false
  }
}

$healthUrl = "http://$BindHost`:$Port/api/health"
$siteUrl = "http://$BindHost`:$Port/"

if (Test-Path $pidFile) {
  $oldPidText = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($oldPidText -and $oldPidText -match "^\d+$") {
    $oldPid = [int]$oldPidText
    $existing = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($existing) {
      if (Test-Health $healthUrl) {
        Write-Host "Server already running (PID=$oldPid): $siteUrl"
        Start-Process $siteUrl
        exit 0
      }
    }
  }
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  throw "python not found in PATH"
}

$proc = Start-Process `
  -FilePath $pythonCmd.Source `
  -ArgumentList @($serverScript, "--host", $BindHost, "--port", "$Port") `
  -WorkingDirectory $repoRoot `
  -RedirectStandardOutput $outLog `
  -RedirectStandardError $errLog `
  -PassThru

$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Milliseconds 300
  if (Test-Health $healthUrl) {
    $healthy = $true
    break
  }
}

if (-not $healthy) {
  if (-not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  }
  throw "Server failed to start. Check logs: $outLog / $errLog"
}

Set-Content -Path $pidFile -Value $proc.Id -Encoding UTF8
Write-Host "Server started (PID=$($proc.Id)): $siteUrl"
Start-Process $siteUrl

#!/usr/bin/env pwsh
# Sync a public knowledge-vault repo to a local cache and print its path.
# PowerShell twin of sync-vault.sh, for Windows shells where bash is absent.
#
# Usage: pwsh -File sync-vault.ps1 <owner/repo>
#        powershell -ExecutionPolicy Bypass -File sync-vault.ps1 <owner/repo>

param([Parameter(Mandatory = $true)][string]$Repo)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$name = $Repo.Split('/')[-1]
$base = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$dest = Join-Path (Join-Path $base '.cache') (Join-Path 'claude-vaults' $name)
$url = "https://github.com/$Repo.git"

# Never prompt for credentials; abort a stalled transfer instead of hanging.
$env:GIT_TERMINAL_PROMPT = '0'
$env:GIT_ASKPASS = ''
$gitOpts = @(
  '-c', 'credential.helper=',
  '-c', 'core.askPass=',
  '-c', 'http.lowSpeedLimit=1000',
  '-c', 'http.lowSpeedTime=20'
)

function Invoke-GitQuiet {
  param([string[]]$GitArgs)
  & git @gitOpts @GitArgs 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

# A cache is usable only if it is a valid git repo AND looks like a vault.
function Test-CacheOk {
  if (-not (Test-Path (Join-Path $dest '.git'))) { return $false }
  if (-not (Invoke-GitQuiet @('-C', $dest, 'rev-parse', '--git-dir'))) { return $false }
  return (Test-Path (Join-Path $dest (Join-Path 'meta' 'index.md')))
}

function Invoke-FreshClone {
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue }
  $parent = Split-Path $dest -Parent
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  return (Invoke-GitQuiet @('clone', '--depth', '1', '-q', $url, $dest))
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "git is not installed or not on PATH. Install Git, then retry."
  exit 1
}

$status = ''
if ((Test-Path $dest) -and -not (Test-CacheOk)) {
  if (Invoke-FreshClone) {
    $status = 'repaired'
  }
  else {
    Write-Error "local copy at $dest is unusable and re-cloning failed. Check you are online, then delete $dest and retry."
    exit 1
  }
}
elseif (-not (Test-Path $dest)) {
  if (Invoke-FreshClone) {
    $status = 'cloned'
  }
  else {
    Write-Error "could not clone $url . Check the repo name and that you are online."
    exit 1
  }
}
else {
  if ((Invoke-GitQuiet @('-C', $dest, 'fetch', '--depth', '1', '-q', 'origin', 'HEAD')) -and
      (Invoke-GitQuiet @('-C', $dest, 'reset', '--hard', '-q', 'FETCH_HEAD'))) {
    $status = 'updated'
  }
  else {
    $status = 'offline (using cached copy)'
  }
}

$commit = (& git -C $dest log -1 --format='%h %cd - %s' --date=short 2>$null | Select-Object -First 1)
if (-not $commit) { $commit = 'unknown' }

# Count only the four content zones (01-… 04-…): excludes raw/, meta/, .git and CI files.
$zones = @(Get-ChildItem -Path $dest -Directory -Filter '0*' -ErrorAction SilentlyContinue)
$pages = @($zones | ForEach-Object {
    Get-ChildItem -Path $_.FullName -Filter '*.md' -Recurse -File -Force -ErrorAction SilentlyContinue
  }).Count

Write-Output "VAULT_PATH=$dest"
Write-Output "STATUS=$status"
Write-Output "LATEST=$commit"
Write-Output "PAGES=$pages"

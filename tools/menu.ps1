<#
The menu behind start.cmd: create a seed, start, check and stop a session, open the guide. Nothing to type but a
number, so nobody needs to know PowerShell. Seeds go to output\seeds; tools\start_stream.ps1 does the starting,
tools\preflight.py the checking.
#>
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$AP = Join-Path $Repo "Archipelago"
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Seeds = Join-Path $Repo "output\seeds"
$SessionFile = Join-Path $Repo "output\session.txt"  # written by tools\start_stream.ps1
$Port = 38281
$Host.UI.RawUI.WindowTitle = "TMNT x A Link to the Past"

function Ask([string]$Question) {
  return (Read-Host "$Question [Y/n]") -notmatch "^[nN]"
}

function Pause-Menu {
  Write-Host ""
  [void](Read-Host "Press Enter for the menu")
}

function All-Seeds {
  @(Get-ChildItem $Seeds -Filter "AP_*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
}

function Session-Running {
  [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) -or
    [bool](Get-Process EmuHawk -ErrorAction SilentlyContinue)
}

function Create-Seed {
  New-Item -ItemType Directory -Force $Seeds | Out-Null
  Write-Host "Making a seed from the player files in players\ (about a minute)..."
  Push-Location $AP
  try {
    & $Python -W ignore Generate.py --player_files_path (Join-Path $Repo "players") --outputpath $Seeds
    $code = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  if ($code) { Write-Host "Making the seed failed (see above)." -ForegroundColor Red; return }
  $seed = (All-Seeds)[0]
  Write-Host ""
  Write-Host "New seed: $($seed.Name)" -ForegroundColor Green
  if (Ask "Start a session with it now?") { Start-Session $seed }
}

function Choose-Seed {
  $all = All-Seeds
  if ($all.Count -eq 0) {
    if (Ask "There is no seed yet. Create one now?") { Create-Seed }
    return $null
  }
  if ($all.Count -eq 1) { return $all[0] }
  Write-Host "Seeds, newest first:"
  $shown = [Math]::Min($all.Count, 9)
  for ($i = 0; $i -lt $shown; $i++) {
    Write-Host ("  {0}  {1}  (made {2:yyyy-MM-dd HH:mm})" -f ($i + 1), $all[$i].Name, $all[$i].LastWriteTime)
  }
  $pick = Read-Host "Which one? [Enter = 1, the newest]"
  if (-not $pick) { return $all[0] }
  if ($pick -match '^\d$' -and [int]$pick -ge 1 -and [int]$pick -le $shown) { return $all[[int]$pick - 1] }
  Write-Host "No seed number $pick."
  return $null
}

function Start-Session($Seed) {
  if (Session-Running) {
    Write-Host "A session is already running."
    if (-not (Ask "Stop it and start again?")) { return }
    Stop-Session
  }
  if (-not $Seed) { $Seed = Choose-Seed }
  if (-not $Seed) { return }
  Write-Host ""
  Write-Host "Starting $($Seed.Name). Windows open one after another; leave them be until it says done." -ForegroundColor Yellow
  & (Join-Path $PSScriptRoot "start_stream.ps1") -Seed $Seed.FullName
  Write-Host ""
  Write-Host "Done starting. Checking everything in 20 seconds, once the games have connected..." -ForegroundColor Yellow
  Start-Sleep 20
  Check-All
}

function Check-All {
  & $Python (Join-Path $PSScriptRoot "preflight.py") --port $Port
}

function Stop-Session {
  Write-Host "Stopping the session..."
  # BizHawk first and gently: it writes A Link to the Past's save when it closes.
  $games = @(Get-Process EmuHawk -ErrorAction SilentlyContinue)
  foreach ($game in $games) { [void]$game.CloseMainWindow() }
  foreach ($game in $games) {
    if (-not $game.WaitForExit(15000)) { Write-Host "  BizHawk did not close; forcing it"; $game.Kill() }
  }
  if ($games.Count) { Write-Host "  BizHawk closed ($($games.Count))" }
  # One PopTracker at a time, as each writes the settings file when it closes (start_stream.ps1 repairs that file).
  $trackers = @(Get-Process poptracker -ErrorAction SilentlyContinue)
  foreach ($tracker in $trackers) {
    [void]$tracker.CloseMainWindow()
    if (-not $tracker.WaitForExit(5000)) { $tracker.Kill() }
  }
  if ($trackers.Count) { Write-Host "  PopTracker closed ($($trackers.Count))" }
  # The server, the two clients and the game swap: Python processes running these scripts with this repo's Python.
  # The venv's python.exe starts the real interpreter as a child, so a process counts when it or its parent runs
  # from this repo.
  $scripts = "MultiServer.py|SNIClient.py|BizHawkClient.py|game_swap.py"
  $pythons = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'")
  $fromRepo = @($pythons | Where-Object { $_.ExecutablePath -like "$Repo\*" } | ForEach-Object { $_.ProcessId })
  $ours = @($pythons | Where-Object {
    $_.CommandLine -match $scripts -and ($fromRepo -contains $_.ProcessId -or $fromRepo -contains $_.ParentProcessId)
  })
  foreach ($process in $ours) { Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue }
  $names = $ours | ForEach-Object { [regex]::Match($_.CommandLine, $scripts).Value } | Sort-Object -Unique
  foreach ($name in $names) { Write-Host "  stopped $name" }
  Get-Process sni -ErrorAction SilentlyContinue | Stop-Process -Force
  Remove-Item $SessionFile -ErrorAction SilentlyContinue
  Write-Host "Stopped." -ForegroundColor Green
}

if (-not (Test-Path $Python)) {
  Write-Host "Not installed yet: double-click install.cmd first." -ForegroundColor Red
  Pause-Menu
  exit 1
}

while ($true) {
  Clear-Host
  Write-Host "TMNT x A Link to the Past" -ForegroundColor Yellow
  Write-Host ""
  if (Session-Running) {
    $running = if (Test-Path $SessionFile) { Split-Path -Leaf (Get-Content $SessionFile -Raw).Trim() } else { "?" }
    Write-Host "  Session: running ($running)" -ForegroundColor Green
  } else {
    Write-Host "  Session: not running"
  }
  $newest = (All-Seeds) | Select-Object -First 1
  Write-Host ("  Newest seed: " + $(if ($newest) { "{0} (made {1:yyyy-MM-dd HH:mm})" -f $newest.Name, $newest.LastWriteTime } else { "none yet" }))
  Write-Host ""
  Write-Host "  1  Create a seed"
  Write-Host "  2  Start a session"
  Write-Host "  3  Check before going live"
  Write-Host "  4  Stop the session"
  Write-Host "  5  Open the guide"
  Write-Host "  Q  Quit (a running session keeps running)"
  Write-Host ""
  $line = Read-Host "Choose"
  if ($null -eq $line) { exit 0 }  # input closed (only when the menu is driven by a script)
  $choice = $line.Trim().ToUpper()
  Write-Host ""
  try {
    switch ($choice) {
      "1" { Create-Seed; Pause-Menu }
      "2" { Start-Session $null; Pause-Menu }
      "3" { Check-All; Pause-Menu }
      "4" { if (Session-Running) { Stop-Session } else { Write-Host "No session is running." }; Pause-Menu }
      "5" { Start-Process (Join-Path $Repo "site\index.html") }
      "Q" { exit 0 }
    }
  } catch {
    Write-Host ""
    Write-Host "Something went wrong: $($_.Exception.Message)" -ForegroundColor Red
    Pause-Menu
  }
}

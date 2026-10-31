<#
Starts everything for an ALttP + TMNT stream seed on this machine, in this order:
  1. MultiServer in its own console window (type /send, /hint etc. there)
  2. SNI (from Archipelago\SNI)
  3. the game swap (tools\game_swap.py) in its own console window: Select+Start or Ctrl+Shift+Space swaps games,
     OBS follows the game in front, and items for the game behind are shown in the game being played
  4. BizHawk with the patched ALttP ROM, SNI's Lua connector and the swap script (lua\alttp_stream.luases)
  5. BizHawk with the patched TMNT ROM, the AP connector, the area select and the swap script
     (lua\tmnt_stream.luases)
  6. SNI Client and BizHawk Client, connected to the server
  7. PopTracker twice: the ALttP pack for the ALttP slot, our TMNT pack (tools/make_poptracker_pack.py) for TMNT
and prints the URL for the go mode panel to paste into OBS.

  powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed output\full\AP_<seed>.zip
  powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed <zip> -NoTracker
  powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed <zip> -NoObsSwitch   (the host switches scenes)

Before BizHawk starts, tools\bizhawk_saves.py turns on BizHawk's autosave, recovers A Link to the Past's save after
a crash and gives every seed its own save. The patched ROMs are made next to the seed's patch files if they are not
there yet. Slot names come from
players\*.yaml (Link, Turtles). Tested 2026-10-31; see docs\stream-tools.md.
#>
param(
  [Parameter(Mandatory = $true)][string]$Seed,
  [int]$Port = 38281,
  [string]$AlttpSlot = "Link",
  [string]$TmntSlot = "Turtles",
  [string]$EmuHawk,     # default: apps\BizHawk-2.11.1 from install.ps1, else Downloads\BizHawk-2.11.1-win-x64
  [string]$PopTracker,  # default: apps\PopTracker-0.36.0 from install.ps1, else Downloads\PopTracker-0.36.0
  [switch]$NoTracker,
  [string]$SwapHotkey = "ctrl+shift+space",  # 'none' for no keyboard swap
  [switch]$NoObsSwitch  # the swap only changes windows; OBS scenes are left to the host
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$AP = Join-Path $Repo "Archipelago"
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
function First-Existing([string[]]$Paths) {
  $found = $Paths | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($found) { $found } else { $Paths[0] }
}
if (-not $EmuHawk) {
  $EmuHawk = First-Existing @((Join-Path $Repo "apps\BizHawk-2.11.1\EmuHawk.exe"),
                              "$env:USERPROFILE\Downloads\BizHawk-2.11.1-win-x64\EmuHawk.exe")
}
if (-not $PopTracker) {
  $PopTracker = First-Existing @((Join-Path $Repo "apps\PopTracker-0.36.0\poptracker.exe"),
                                 "$env:USERPROFILE\Downloads\PopTracker-0.36.0\poptracker.exe")
}
$SeedPath = (Resolve-Path $Seed).Path
$SeedDir = Split-Path -Parent $SeedPath
$Server = "localhost:$Port"

function Need($path, $what) {
  if (-not (Test-Path $path)) { throw "Missing $what at $path (see docs\stream-tools.md)" }
}
Need $Python "the Python venv"
Need $EmuHawk "BizHawk 2.11.1"
Need (Join-Path $AP "SNI\sni.exe") "SNI"
Need (Join-Path $Repo "savestates\area1.State") "the area savestates (lua\tmnt_make_area_states.lua)"
# Universal Tracker hangs on a hidden folder dialog without this folder (it may stay empty).
New-Item -ItemType Directory -Force (Join-Path $AP "Players") | Out-Null

# The patched ROMs: unpack the seed's patch files and patch them once.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($SeedPath)
foreach ($entry in $archive.Entries | Where-Object { $_.Name -match '\.(aplttp|aptmnt)$' }) {
  $target = Join-Path $SeedDir $entry.Name
  if (-not (Test-Path $target)) { [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target) }
}
$archive.Dispose()
$alttpPatch = Get-ChildItem $SeedDir -Filter "*.aplttp" | Select-Object -First 1
$tmntPatch = Get-ChildItem $SeedDir -Filter "*.aptmnt" | Select-Object -First 1
$alttpRom = [System.IO.Path]::ChangeExtension($alttpPatch.FullName, ".sfc")
$tmntRom = [System.IO.Path]::ChangeExtension($tmntPatch.FullName, ".nes")
if (-not (Test-Path $alttpRom) -or -not (Test-Path $tmntRom)) {
  Push-Location $AP
  & $Python -W ignore Patch.py $alttpPatch.FullName $tmntPatch.FullName
  Pop-Location
}
Need $alttpRom "the patched ALttP ROM"
Need $tmntRom "the patched TMNT ROM"
# Fixed file names give the BizHawk windows fixed titles ("alttp-stream [SNES] - BizHawk", "tmnt-stream [NES] -
# BizHawk"), which the OBS scene collection (tools/make_obs_collection.py) captures whatever the seed.
Copy-Item $alttpRom (Join-Path $SeedDir "alttp-stream.sfc") -Force
Copy-Item $tmntRom (Join-Path $SeedDir "tmnt-stream.nes") -Force
$alttpRom = Join-Path $SeedDir "alttp-stream.sfc"
$tmntRom = Join-Path $SeedDir "tmnt-stream.nes"

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
  throw "Port $Port is already in use (an old MultiServer?). Close it or pass -Port."
}
# BizHawk rewrites its config.ini when it closes, and the save files below must not be in use.
if (Get-Process EmuHawk -ErrorAction SilentlyContinue) {
  throw "BizHawk is already running. Close it first (start.cmd -> Stop the session)."
}
# Autosave, crash recovery and one A Link to the Past save per seed (see the script).
& $Python (Join-Path $Repo "tools\bizhawk_saves.py") --bizhawk (Split-Path $EmuHawk) `
  --seed ([IO.Path]::GetFileNameWithoutExtension($SeedPath))
if ($LASTEXITCODE) { throw "tools\bizhawk_saves.py failed." }
New-Item -ItemType Directory -Force (Join-Path $Repo "output") | Out-Null
Set-Content -Path (Join-Path $Repo "output\session.txt") -Value $SeedPath -Encoding utf8  # shown by start.cmd
Write-Host "1/7 MultiServer on $Server"
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("MultiServer.py", "`"$SeedPath`"", "--host", "127.0.0.1", "--port", $Port)
Start-Sleep 6

Write-Host "2/7 SNI"
if (-not (Get-Process sni -ErrorAction SilentlyContinue)) {
  Start-Process (Join-Path $AP "SNI\sni.exe") -WorkingDirectory (Join-Path $AP "SNI")
}

# Before BizHawk: it makes output\swap, where the swap scripts in BizHawk write.
Write-Host "3/7 Game swap (Select+Start or $SwapHotkey)"
$swapArgs = @("-u", "`"$(Join-Path $Repo 'tools\game_swap.py')`"", "--hotkey", $SwapHotkey,
              "--server", "ws://$Server", "--slot", $TmntSlot)
if ($NoObsSwitch) { $swapArgs += "--no-obs" }
Start-Process $Python -WorkingDirectory $Repo -ArgumentList $swapArgs
Start-Sleep 2

Write-Host "4/7 BizHawk: A Link to the Past"
Start-Process $EmuHawk -ArgumentList @("--lua=`"$(Join-Path $Repo 'lua\alttp_stream.luases')`"", "`"$alttpRom`"")

Write-Host "5/7 BizHawk: TMNT"
Start-Process $EmuHawk -ArgumentList @("--lua=`"$(Join-Path $Repo 'lua\tmnt_stream.luases')`"", "`"$tmntRom`"")
Start-Sleep 8

Write-Host "6/7 SNI Client and BizHawk Client"
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("SNIClient.py", "--connect", $Server)
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("BizHawkClient.py", "--connect", $Server)

if (-not $NoTracker) {
  Write-Host "7/7 PopTracker for $AlttpSlot and $TmntSlot (one window each)"
  Need $PopTracker "PopTracker 0.36.0"
  # PopTracker can break its own settings file when it closes; then it asks questions instead of connecting.
  & $Python (Join-Path $Repo "tools\poptracker_config.py")
  Start-Process $PopTracker -ArgumentList @("--load-pack", "ap_alltp", "--pack-variant", "`"Map Tracker - AP`"",
                                            "--ap-host", $Server, "--ap-slot", $AlttpSlot)
  Start-Sleep 3
  Start-Process $PopTracker -ArgumentList @("--load-pack", "tmnt_ap", "--pack-variant", "`"Item Tracker - AP`"",
                                            "--ap-host", $Server, "--ap-slot", $TmntSlot)
}

$panel = "file:///" + ((Join-Path $Repo "tools\obs\go-mode.html") -replace '\\', '/')
Write-Host ""
Write-Host "Go mode panel for OBS (Browser source, local file + this URL):"
Write-Host "  $panel`?server=ws://$Server&alttp=$AlttpSlot&tmnt=$TmntSlot"
Write-Host "Universal Tracker for TMNT: Archipelago Launcher -> Universal Tracker, connect to $Server as $TmntSlot"
if (-not $NoObsSwitch) {
  Write-Host "OBS follows the game in front once its WebSocket server is on (Tools -> WebSocket Server Settings)."
}

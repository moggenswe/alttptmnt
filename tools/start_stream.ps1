<#
Starts everything for an ALttP + TMNT stream seed on this machine, in this order:
  1. MultiServer in its own console window (type /send, /hint etc. there)
  2. SNI (from Archipelago\SNI)
  3. BizHawk with the patched ALttP ROM and SNI's Lua connector
  4. BizHawk with the patched TMNT ROM, the AP connector and the area select (lua\tmnt_stream.luases)
  5. SNI Client and BizHawk Client, connected to the server
  6. PopTracker twice: the ALttP pack for the ALttP slot, our TMNT pack (tools/make_poptracker_pack.py) for TMNT
and prints the URL for the go mode panel to paste into OBS.

  powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed output\full\AP_<seed>.zip
  powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed <zip> -NoTracker

The patched ROMs are made next to the seed's patch files if they are not there yet. Slot names come from
players\*.yaml (Link, Turtles). Tested 2026-10-31; see docs\stream-verktyg.md.
#>
param(
  [Parameter(Mandatory = $true)][string]$Seed,
  [int]$Port = 38281,
  [string]$AlttpSlot = "Link",
  [string]$TmntSlot = "Turtles",
  [string]$EmuHawk,     # default: apps\BizHawk-2.11.1 from install.ps1, else Downloads\BizHawk-2.11.1-win-x64
  [string]$PopTracker,  # default: apps\PopTracker-0.36.0 from install.ps1, else Downloads\PopTracker-0.36.0
  [switch]$NoTracker
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
  if (-not (Test-Path $path)) { throw "Missing $what at $path (see docs\stream-verktyg.md)" }
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
Write-Host "1/6 MultiServer on $Server"
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("MultiServer.py", "`"$SeedPath`"", "--host", "127.0.0.1", "--port", $Port)
Start-Sleep 6

Write-Host "2/6 SNI"
if (-not (Get-Process sni -ErrorAction SilentlyContinue)) {
  Start-Process (Join-Path $AP "SNI\sni.exe") -WorkingDirectory (Join-Path $AP "SNI")
}

Write-Host "3/6 BizHawk: A Link to the Past"
Start-Process $EmuHawk -ArgumentList @("--lua=`"$(Join-Path $AP 'SNI\lua\Connector.lua')`"", "`"$alttpRom`"")

Write-Host "4/6 BizHawk: TMNT"
Start-Process $EmuHawk -ArgumentList @("--lua=`"$(Join-Path $Repo 'lua\tmnt_stream.luases')`"", "`"$tmntRom`"")
Start-Sleep 8

Write-Host "5/6 SNI Client and BizHawk Client"
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("SNIClient.py", "--connect", $Server)
Start-Process $Python -WorkingDirectory $AP -ArgumentList @("BizHawkClient.py", "--connect", $Server)

if (-not $NoTracker) {
  Write-Host "6/6 PopTracker for $AlttpSlot and $TmntSlot (one window each)"
  Need $PopTracker "PopTracker 0.36.0"
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

<#
.SYNOPSIS
  One-time installer for the TMNT x A Link to the Past Archipelago randomizer (Windows 10/11).

.DESCRIPTION
  Asks for your two ROMs, lists what it needs to download and asks before it downloads anything, then
  installs everything else into this folder:
    - Python 3.12 (through uv, in apps\python) and a virtual environment in .venv
    - Archipelago 0.6.8 from source, its requirements, and the TMNT world linked in
    - BizHawk 2.11.1, SNI v0.0.103, PopTracker 0.36.0 with the ALttP pack and our TMNT pack (in apps\)
    - the Visual C++ 2015-2022 runtime BizHawk needs, if Windows lacks it (asks for admin rights)
    - Universal Tracker (optional tracker for TMNT)
    - the six TMNT area savestates (made in the BizHawk installed here)
    - the OBS scene collection (copied into OBS if it is not running)
  Every download is pinned to a version and checked against a SHA-256 sum. Running it again skips what is
  already there, so it is also the way to repair an install.

  Double-click install.cmd, or:
    powershell -ExecutionPolicy Bypass -File install.ps1
    powershell -ExecutionPolicy Bypass -File install.ps1 -AlttpRom D:\roms\zelda.sfc -TmntRom D:\roms\tmnt.nes -Yes

.PARAMETER AlttpRom
  A Link to the Past, Japan 1.0 (.sfc or .smc; a 512-byte copier header is removed).
.PARAMETER TmntRom
  Teenage Mutant Ninja Turtles, NES USA (.nes).
.PARAMETER Yes
  Do not ask questions (needs both ROM parameters): downloads what is missing and copies the OBS collection
  into OBS.
.PARAMETER Cache
  Folder for the downloaded archives (kept, so a repair needs no new downloads).
#>
param(
  [string]$AlttpRom,
  [string]$TmntRom,
  [switch]$Yes,
  [string]$Cache = (Join-Path $PSScriptRoot ".cache\downloads"),
  [switch]$SkipStates,
  [switch]$SkipObs
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Invoke-WebRequest is many times faster without the progress bar
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Repo = $PSScriptRoot
$Apps = Join-Path $Repo "apps"
$AP = Join-Path $Repo "Archipelago"
$Venv = Join-Path $Repo ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$PackagesDone = Join-Path $Venv "tmnt-packages-installed"   # written once ModuleUpdate.py has succeeded
# Python, uv's and pip's caches stay in this folder: no python.exe in ~\.local\bin, nothing in the registry.
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Apps "python"
$env:UV_CACHE_DIR = Join-Path $Repo ".cache\uv"
$env:PIP_CACHE_DIR = Join-Path $Repo ".cache\pip"

$ALTTP_MD5 = "03a63945398191337e896e5771f77173"    # Zelda no Densetsu: Kamigami no Triforce (Japan) 1.0, no header
$TMNT_MD5 = "5e24ccd733d15e42d847274e7add0a76"     # Teenage Mutant Ninja Turtles (USA), clean iNES header
$ALTTP_NAME = "Zelda no Densetsu - Kamigami no Triforce (Japan).sfc"
$TMNT_NAME = "Teenage Mutant Ninja Turtles (USA).nes"

# Pinned downloads (checked 2026-10-31). Archipelago's tag archive is made by GitHub on the fly and is not
# byte-stable, so it is checked by the version in its source instead of a hash. Microsoft's runtime installer
# always points at the newest build, so it is checked by its Microsoft signature instead. Mb is the download size.
$Downloads = [ordered]@{
  uv         = @{ Name = "uv 0.12.24 (installs Python)"; Mb = 15
                  File = "uv-0.12.24-x86_64-pc-windows-msvc.zip"
                  Url = "https://github.com/astral-sh/uv/releases/download/0.12.24/uv-x86_64-pc-windows-msvc.zip"
                  Sha256 = "7c38608c8a18ee137d748a1773053b07ec8f3a30fab49aebaa6f4e4efeceb019" }
  archipelago = @{ Name = "Archipelago 0.6.8 (source)"; Mb = 22
                  File = "Archipelago-0.6.8.zip"
                  Url = "https://github.com/ArchipelagoMW/Archipelago/archive/refs/tags/0.6.8.zip"; Sha256 = $null }
  sni        = @{ Name = "SNI v0.0.103"; Mb = 13
                  File = "sni-v0.0.103-windows-amd64.zip"
                  Url = "https://github.com/alttpo/sni/releases/download/v0.0.103/sni-v0.0.103-windows-amd64.zip"
                  Sha256 = "4c0885769518c8b6ed7db038a29fdbdaf28b64c3b54689a5b2e0d6dd33074f87" }
  bizhawk    = @{ Name = "BizHawk 2.11.1"; Mb = 93
                  File = "BizHawk-2.11.1-win-x64.zip"
                  Url = "https://github.com/TASEmulators/BizHawk/releases/download/2.11.1/BizHawk-2.11.1-win-x64.zip"
                  Sha256 = "dd7cbd5e205b09c5bce6afabc4f8aa525acc0bbeb9753b198a8db3fe6a5e5717" }
  vcredist   = @{ Name = "Visual C++ 2015-2022 runtime, x64 (for BizHawk; asks for admin rights)"; Mb = 25
                  File = "vc_redist.x64.exe"; Url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                  Sha256 = $null; Signer = "O=Microsoft Corporation" }
  poptracker = @{ Name = "PopTracker 0.36.0"; Mb = 7
                  File = "poptracker_0-36-0_win64.zip"
                  Url = "https://github.com/black-sliver/PopTracker/releases/download/v0.36.0/poptracker_0-36-0_win64.zip"
                  Sha256 = "18113909ac6008386b477b7bead6d9b8cf6809aa679667e6c0fd23efb63db127" }
  alttppack  = @{ Name = "ALttP PopTracker pack v0.5.1"; Mb = 30
                  File = "alttp-ap-tracker-v0.5.1.zip"
                  Url = "https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases/download/v0.5.1/alttp-ap-tracker-v0.5.1.zip"
                  Sha256 = "0fec704050d51db22703576e821b82f26bc162d3b3f942db38048f037c3eca66" }
  tracker    = @{ Name = "Universal Tracker v0.3.8"; Mb = 1
                  File = "tracker.apworld"
                  Url = "https://github.com/FarisTheAncient/Archipelago/releases/download/Tracker_v0.3.8/tracker.apworld"
                  Sha256 = "2661cac9e4e337ab260f514c068724e15532d0500dcbc48616b0a26d6ac5b466" }
}
$Steps = 13
$script:Step = 0

function Step([string]$Text) {
  $script:Step++
  Write-Host ""
  Write-Host ("[{0}/{1}] {2}" -f $script:Step, $Steps, $Text) -ForegroundColor Green
}
function Info([string]$Text) { Write-Host "      $Text" }
function Fail([string]$Text) { Write-Host ""; Write-Host "ERROR: $Text" -ForegroundColor Red; exit 1 }

function Get-Md5([byte[]]$Bytes) {
  $md5 = [System.Security.Cryptography.MD5]::Create()
  return ([BitConverter]::ToString($md5.ComputeHash($Bytes)) -replace "-", "").ToLower()
}

function Get-Download([string]$Key) {
  $item = $Downloads[$Key]
  New-Item -ItemType Directory -Force $Cache | Out-Null
  $path = Join-Path $Cache $item.File
  if (-not (Test-Path $path)) {
    Info "downloading $($item.File)"
    Invoke-WebRequest -Uri $item.Url -OutFile "$path.part" -UseBasicParsing
    Move-Item "$path.part" $path -Force
  }
  if ($item.Sha256) {
    $hash = (Get-FileHash $path -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $item.Sha256) {
      Remove-Item $path -Force
      Fail "$($item.File) does not match its pinned SHA-256 (got $hash). Run the installer again."
    }
  }
  if ($item.Signer) {
    $signature = Get-AuthenticodeSignature $path
    if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notmatch [regex]::Escape($item.Signer)) {
      Remove-Item $path -Force
      Fail "$($item.File) is not signed by $($item.Signer) ($($signature.Status)). Run the installer again."
    }
  }
  return $path
}

function Is-Cached([string]$Key) { Test-Path (Join-Path $Cache $Downloads[$Key].File) }

function Has-VcRuntime {
  foreach ($key in @("HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                     "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")) {
    $runtime = Get-ItemProperty $key -ErrorAction SilentlyContinue
    if ($runtime -and $runtime.Installed -eq 1) { return $true }
  }
  return $false
}

function Expand-Fresh([string]$Zip, [string]$Destination) {
  $temp = "$Destination.unpacking"
  if (Test-Path $temp) { Remove-Item $temp -Recurse -Force }
  Expand-Archive -Path $Zip -DestinationPath $temp
  # Archives with a single top folder: use what is inside it.
  $children = @(Get-ChildItem $temp)
  $source = if ($children.Count -eq 1 -and $children[0].PSIsContainer) { $children[0].FullName } else { $temp }
  Move-Item $source $Destination
  if (Test-Path $temp) { Remove-Item $temp -Recurse -Force }
}

function Ask-Rom([string]$Current, [string]$Title, [string]$Filter) {
  if ($Current) { return $Current }
  if ($Yes) { Fail "$Title is needed (pass it as a parameter with -Yes)." }
  Write-Host "      Choose $Title in the file dialog (it may open behind this window)..."
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.OpenFileDialog
  $dialog.Title = $Title
  $dialog.Filter = $Filter
  if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dialog.FileName }
  $typed = Read-Host "      Or type the full path"
  if (-not $typed) { Fail "No file given for $Title." }
  return $typed.Trim('"')
}

function Confirm([string]$Question) {
  if ($Yes) { return $true }
  return (Read-Host "      $Question [Y/n]") -notmatch "^[nN]"
}

Write-Host "TMNT x A Link to the Past - installer" -ForegroundColor Yellow
Write-Host "Installs into $Repo"
# Archipelago's Python packages have deep paths; past Windows' 260-character limit pip fails half-way
# (WinError 206, seen 2026-10-31 from a 125-character folder). Stop before anything is downloaded.
$longPaths = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -ErrorAction SilentlyContinue).LongPathsEnabled
if ($Repo.Length -gt 80 -and $longPaths -ne 1) {
  Fail "This folder's path is too long for Windows ($($Repo.Length) characters). Move the folder to a short path such as C:\tmntalttp and run install.cmd there."
}

# --- 1. ROMs ---------------------------------------------------------------------------------------------
Step "Your ROMs"
$AlttpRom = Ask-Rom $AlttpRom "A Link to the Past (Japan 1.0) ROM" "SNES ROM (*.sfc;*.smc)|*.sfc;*.smc|All files|*.*"
if (-not (Test-Path $AlttpRom)) { Fail "Not found: $AlttpRom" }
$alttp = [IO.File]::ReadAllBytes((Resolve-Path $AlttpRom))
if ($alttp.Length -eq 1048576 + 512) {
  $stripped = New-Object byte[] 1048576
  [Array]::Copy($alttp, 512, $stripped, 0, 1048576)
  $alttp = $stripped
  Info "removed the 512-byte copier header"
}
if ((Get-Md5 $alttp) -ne $ALTTP_MD5) {
  Fail "That A Link to the Past ROM is not the Japan 1.0 version (md5 $(Get-Md5 $alttp), want $ALTTP_MD5)."
}
Info "A Link to the Past: OK (Japan 1.0)"

$TmntRom = Ask-Rom $TmntRom "Teenage Mutant Ninja Turtles (NES, USA) ROM" "NES ROM (*.nes)|*.nes|All files|*.*"
if (-not (Test-Path $TmntRom)) { Fail "Not found: $TmntRom" }
$tmnt = [IO.File]::ReadAllBytes((Resolve-Path $TmntRom))
if ((Get-Md5 $tmnt) -ne $TMNT_MD5) {
  Fail "That TMNT ROM is not the NES USA version with a clean header (md5 $(Get-Md5 $tmnt), want $TMNT_MD5)."
}
Info "Teenage Mutant Ninja Turtles: OK (NES, USA)"

# --- 2. What needs downloading -----------------------------------------------------------------------------
Step "What needs downloading"
# BizHawk needs .NET Framework 4.8 (part of Windows 10 1903 and later, and of Windows 11).
$net = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" -ErrorAction SilentlyContinue
if (-not $net -or $net.Release -lt 528040) {
  Fail ("BizHawk needs .NET Framework 4.8, which this Windows lacks. Install it from " +
        "https://dotnet.microsoft.com/download/dotnet-framework/net48 and run the installer again.")
}
$uv = Join-Path $Apps "uv\uv.exe"
$bizhawk = Join-Path $Apps "BizHawk-2.11.1"
$poptracker = Join-Path $Apps "PopTracker-0.36.0"
$hasPython = (Test-Path $Python) -or (Test-Path (Join-Path $Apps "python\cpython-3.12*"))
$wanted = @(
  @{ Key = "uv"; Needed = -not (Test-Path $uv) }
  @{ Name = "Python 3.12 (through uv)"; Mb = 30; From = "github.com"; Needed = -not $hasPython }
  @{ Key = "archipelago"; Needed = -not (Test-Path (Join-Path $AP "Generate.py")) }
  @{ Name = "Archipelago's Python packages"; Mb = 80; From = "pypi.org"; Needed = -not (Test-Path $PackagesDone) }
  @{ Key = "sni"; Needed = -not (Test-Path (Join-Path $AP "SNI\sni.exe")) }
  @{ Key = "bizhawk"; Needed = -not (Test-Path (Join-Path $bizhawk "EmuHawk.exe")) }
  @{ Key = "vcredist"; Needed = -not (Has-VcRuntime) }
  @{ Key = "poptracker"; Needed = -not (Test-Path (Join-Path $poptracker "poptracker.exe")) }
  @{ Key = "alttppack"; Needed = $true }
  @{ Key = "tracker"; Needed = $true }
)
$toFetch = @(foreach ($w in $wanted) {
  if (-not $w.Needed) { continue }
  if ($w.Key) {
    if (Is-Cached $w.Key) { continue }
    $d = $Downloads[$w.Key]
    @{ Name = $d.Name; Mb = $d.Mb; From = ([Uri]$d.Url).Host }
  } else {
    $w
  }
})
if ($toFetch.Count -eq 0) {
  Info "nothing; everything is installed or already in $Cache"
} else {
  foreach ($f in $toFetch) { Info ("- {0}: about {1} MB from {2}" -f $f.Name, $f.Mb, $f.From) }
  Info ("about {0} MB in all" -f ($toFetch | ForEach-Object { $_.Mb } | Measure-Object -Sum).Sum)
  if (-not (Confirm "Can I download these?")) {
    Write-Host ""
    Write-Host "Nothing was downloaded or installed. Run the installer again when you want to go on."
    exit 0
  }
}

# --- 3. uv and Python ------------------------------------------------------------------------------------
Step "Python 3.12 (through uv)"
if (-not (Test-Path $uv)) { Expand-Fresh (Get-Download "uv") (Join-Path $Apps "uv") }
if (-not (Test-Path $Python)) {
  & $uv python install 3.12 --no-bin --no-registry
  if ($LASTEXITCODE) { Fail "uv could not install Python 3.12." }
  & $uv venv --seed --python 3.12 $Venv
  if ($LASTEXITCODE) { Fail "uv could not create the virtual environment." }
}
Info (& $Python --version)

# --- 4. Archipelago ---------------------------------------------------------------------------------------
Step "Archipelago 0.6.8 (source)"
if (-not (Test-Path (Join-Path $AP "Generate.py"))) { Expand-Fresh (Get-Download "archipelago") $AP }
$version = Select-String -Path (Join-Path $AP "Utils.py") -Pattern '__version__ = "([^"]+)"' | Select-Object -First 1
if (-not $version -or $version.Matches[0].Groups[1].Value -ne "0.6.8") { Fail "Archipelago\ is not version 0.6.8." }
Info "Archipelago 0.6.8 in $AP"

# --- 5. Requirements ---------------------------------------------------------------------------------------
Step "Archipelago's Python packages (takes a few minutes the first time)"
Push-Location $AP
& $Python ModuleUpdate.py --yes
$code = $LASTEXITCODE
Pop-Location
if ($code) { Fail "ModuleUpdate.py failed (exit $code)." }
Set-Content -Path $PackagesDone -Value "Archipelago 0.6.8" -Encoding ascii

# --- 6. TMNT world, ROMs in place --------------------------------------------------------------------------
Step "TMNT world and ROM files"
$link = Join-Path $AP "worlds\tmnt"
if (-not (Test-Path $link)) {
  New-Item -ItemType Junction -Path $link -Target (Join-Path $Repo "apworld\tmnt") | Out-Null
  Info "linked Archipelago\worlds\tmnt -> apworld\tmnt"
}
New-Item -ItemType Directory -Force (Join-Path $Repo "roms") | Out-Null
[IO.File]::WriteAllBytes((Join-Path $AP $ALTTP_NAME), $alttp)
[IO.File]::WriteAllBytes((Join-Path $AP $TMNT_NAME), $tmnt)
[IO.File]::WriteAllBytes((Join-Path $Repo "roms\$TMNT_NAME"), $tmnt)
Info "ROMs copied (they stay out of git)"

# --- 7. SNI -------------------------------------------------------------------------------------------------
Step "SNI v0.0.103"
if (-not (Test-Path (Join-Path $AP "SNI\sni.exe"))) { Expand-Fresh (Get-Download "sni") (Join-Path $AP "SNI") }
Info "SNI in Archipelago\SNI"

# --- 8. BizHawk ---------------------------------------------------------------------------------------------
Step "BizHawk 2.11.1"
if (-not (Test-Path (Join-Path $bizhawk "EmuHawk.exe"))) {
  Expand-Fresh (Get-Download "bizhawk") $bizhawk
  Get-ChildItem $bizhawk -Recurse | Unblock-File
}
Info "BizHawk in $bizhawk"
if (Has-VcRuntime) {
  Info "Visual C++ runtime: already in Windows"
} else {
  Info "installing the Visual C++ runtime (answer Yes in the Windows admin prompt)..."
  $setup = Start-Process (Get-Download "vcredist") -ArgumentList "/install", "/passive", "/norestart" -Verb RunAs -Wait -PassThru
  # 3010: installed, Windows wants a restart; 1638: a newer build is already there.
  if (@(0, 3010, 1638) -notcontains $setup.ExitCode) { Fail "The Visual C++ runtime did not install (exit $($setup.ExitCode))." }
  if ($setup.ExitCode -eq 3010) { Info "installed; restart Windows before you start BizHawk" } else { Info "installed" }
}

# --- 9. PopTracker and packs --------------------------------------------------------------------------------
Step "PopTracker 0.36.0, the ALttP pack and the TMNT pack"
if (-not (Test-Path (Join-Path $poptracker "poptracker.exe"))) {
  Expand-Fresh (Get-Download "poptracker") $poptracker
  Get-ChildItem $poptracker -Recurse | Unblock-File
}
$packs = Join-Path $poptracker "packs"
New-Item -ItemType Directory -Force $packs | Out-Null
Copy-Item (Get-Download "alttppack") $packs -Force
& $Python -W ignore (Join-Path $Repo "tools\make_poptracker_pack.py") --install --packs-dir $packs
if ($LASTEXITCODE) { Fail "Building the TMNT PopTracker pack failed." }
# Software rendering so OBS window capture sees PopTracker; no first-start questions.
$config = Join-Path $env:APPDATA "PopTracker\PopTracker.json"
New-Item -ItemType Directory -Force (Split-Path $config) | Out-Null
$settings = if (Test-Path $config) { Get-Content $config -Raw | ConvertFrom-Json } else { New-Object PSObject }
foreach ($pair in @(@("software_renderer", $true), @("check_for_updates", $false), @("add_emo_packs", $false))) {
  $settings | Add-Member -NotePropertyName $pair[0] -NotePropertyValue $pair[1] -Force
}
[IO.File]::WriteAllText($config, ($settings | ConvertTo-Json))
Info "PopTracker set to software rendering (needed for OBS capture)"

# --- 10. Universal Tracker -----------------------------------------------------------------------------------
Step "Universal Tracker v0.3.8"
New-Item -ItemType Directory -Force (Join-Path $AP "custom_worlds"), (Join-Path $AP "Players") | Out-Null
Copy-Item (Get-Download "tracker") (Join-Path $AP "custom_worlds\tracker.apworld") -Force
Info "tracker.apworld in Archipelago\custom_worlds (Archipelago\Players must exist; it does)"

# --- 11. Area savestates ------------------------------------------------------------------------------------
Step "TMNT area savestates"
$states = 1..6 | ForEach-Object { Join-Path $Repo "savestates\area$_.State" }
if ($SkipStates) {
  Info "skipped (-SkipStates)"
} elseif (@($states | Where-Object { -not (Test-Path $_) }).Count -eq 0) {
  Info "already there"
} else {
  Info "BizHawk opens for about half a minute and closes by itself..."
  $env:TMNT_EXIT_WHEN_DONE = "1"
  $proc = Start-Process (Join-Path $bizhawk "EmuHawk.exe") -PassThru -ArgumentList @(
    "--lua=`"$(Join-Path $Repo 'lua\tmnt_make_area_states.lua')`"", "`"$(Join-Path $Repo "roms\$TMNT_NAME")`"")
  if (-not $proc.WaitForExit(240000)) { $proc.Kill(); Fail "BizHawk did not finish the savestates in 4 minutes." }
  Remove-Item Env:\TMNT_EXIT_WHEN_DONE
  $missing = @($states | Where-Object { -not (Test-Path $_) })
  if ($missing.Count) { Fail "Savestates missing: $($missing -join ', ')" }
  Info "savestates\area1.State ... area6.State made"
}

# --- 12. OBS ------------------------------------------------------------------------------------------------
Step "OBS scene collection"
& $Python (Join-Path $Repo "tools\make_obs_collection.py")
$collection = Join-Path $Repo "tools\obs\tmnt-alttp-scenes.json"
$obsScenes = Join-Path $env:APPDATA "obs-studio\basic\scenes"
if ($SkipObs) {
  Info "skipped (-SkipObs); import $collection in OBS by hand"
} elseif (Get-Process obs64 -ErrorAction SilentlyContinue) {
  Info "OBS is running: import $collection under Scene Collection -> Import"
} elseif ((Test-Path $obsScenes) -and (Confirm "Add the 'TMNT x ALttP' scene collection to OBS?")) {
  Copy-Item $collection (Join-Path $obsScenes "TMNT_x_ALttP.json") -Force
  Info "added; pick 'TMNT x ALttP' under Scene Collection in OBS"
} else {
  Info "import $collection in OBS under Scene Collection -> Import"
}

# --- 13. Check ----------------------------------------------------------------------------------------------
Step "Checking the install"
Push-Location $AP
# unittest reports on stderr, which Windows PowerShell 5.1 would turn into errors; let cmd merge the streams.
$testOutput = cmd /c "`"$Python`" -W ignore -m unittest discover -s worlds\tmnt\test -t . 2>&1"
$testCode = $LASTEXITCODE
Pop-Location
$testOutput | Select-String -Pattern "^(Ran|OK|FAILED)" | ForEach-Object { Info $_.Line }
if ($testCode) { Fail "The TMNT tests failed." }
$testOutput = cmd /c "`"$Python`" -W ignore -m unittest discover -s `"$(Join-Path $Repo 'tools')`" -p test_*.py 2>&1"
$testCode = $LASTEXITCODE
$testOutput | Select-String -Pattern "^(Ran|OK|FAILED)" | ForEach-Object { Info "game swap: $($_.Line)" }
if ($testCode) { Fail "The game swap tests failed." }
& $Python (Join-Path $Repo "tools\gen_many.py") --count 3 --players (Join-Path $Repo "players") --ap $AP
if ($LASTEXITCODE) { Fail "Generating test seeds failed." }

Write-Host ""
Write-Host "Installed." -ForegroundColor Yellow
Write-Host "Next: double-click start.cmd (in $Repo) to create a seed and start a session."
Write-Host "Guide: $Repo\site\index.html"

# packaging/msix/build_msix.ps1 — turns dist\JARVIS (the PyInstaller build) into a
# Microsoft Store package. Run by .github/workflows/msix.yml on a Windows runner.
param([string]$Version = "1.0.0")
$ErrorActionPreference = "Stop"

$root   = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$cfg    = Get-Content (Join-Path $PSScriptRoot "store.json") -Raw | ConvertFrom-Json
$build  = Join-Path $root "dist\JARVIS"
if (-not (Test-Path (Join-Path $build "JARVIS.exe"))) { throw "dist\JARVIS\JARVIS.exe not found - run PyInstaller first." }

# MSIX versions have four numbers. The Store keeps the last one for itself, so it must be 0.
if ($Version -match '^v?(\d+)\.(\d+)\.(\d+)') { $ver = "$($Matches[1]).$($Matches[2]).$($Matches[3]).0" } else { $ver = "1.0.0.0" }
Write-Host "Package version: $ver"

$layout = Join-Path $root "dist\msix_layout"
if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
Copy-Item $build $layout -Recurse
# python-docx ships its *source* template unzipped, including files named [Content_Types].xml
# and _rels\.rels. Those names are reserved inside a package and makeappx fails on them
# (error 0x8007007b). The app only ever opens the zipped docx\templates\default.docx,
# so the unzipped copy is safe to drop.
$docxSrc = Join-Path $layout "docx\templates\default-docx-template"
if (Test-Path -LiteralPath $docxSrc) { Remove-Item -LiteralPath $docxSrc -Recurse -Force; Write-Host "Removed docx\templates\default-docx-template" }

# Same protection for anything else that uses a reserved packaging name.
Get-ChildItem -LiteralPath $layout -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '[Content_Types].xml' -or $_.Name -eq '.rels' -or ($_.PSIsContainer -and $_.Name -eq '_rels') } |
    Sort-Object { $_.FullName.Length } -Descending |
    ForEach-Object {
        Write-Host ("Removing reserved name: " + $_.FullName.Substring($layout.Length))
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

# Report (do not delete) any other file name makeappx could dislike, so a future failure is easy to trace.
Get-ChildItem -LiteralPath $layout -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '[\[\]{}#%^`~;$&!@+]' -or $_.Name.EndsWith('.') -or $_.Name.EndsWith(' ') } |
    ForEach-Object { Write-Host ("WARNING unusual file name: " + $_.FullName.Substring($layout.Length)) }

New-Item (Join-Path $layout "Assets") -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot "Assets\*") (Join-Path $layout "Assets")

$esc = { param($t) [System.Security.SecurityElement]::Escape([string]$t) }
$xml = Get-Content (Join-Path $PSScriptRoot "AppxManifest.template.xml") -Raw
$xml = $xml.Replace("__IDENTITY_NAME__", (& $esc $cfg.identityName)).
            Replace("__PUBLISHER_DISPLAY_NAME__", (& $esc $cfg.publisherDisplayName)).
            Replace("__PUBLISHER__", (& $esc $cfg.publisher)).
            Replace("__DISPLAY_NAME__", (& $esc $cfg.displayName)).
            Replace("__DESCRIPTION__", (& $esc $cfg.description)).
            Replace("__VERSION__", $ver)
if ($xml -match "__[A-Z_]+__") { throw "Manifest still has an unfilled placeholder: $($Matches[0])" }
[System.IO.File]::WriteAllText((Join-Path $layout "AppxManifest.xml"), $xml, (New-Object System.Text.UTF8Encoding($false)))

# makeappx.exe ships with the Windows SDK that is preinstalled on GitHub's Windows runners.
$makeappx = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter makeappx.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "\\x64\\" } | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $makeappx) { throw "makeappx.exe (Windows SDK) not found on this machine." }

$out = Join-Path $root "dist\MarkLIV-Store.msix"
if (Test-Path $out) { Remove-Item $out -Force }
# makeappx prints one line per file (hundreds of them). Keep the log readable: show only problems and the tail.
$log  = & $makeappx.FullName pack /d $layout /p $out /o 2>&1
$code = $LASTEXITCODE
$log | Where-Object { $_ -match 'error|warning|fail' } | ForEach-Object { Write-Host $_ }
$log | Select-Object -Last 6 | ForEach-Object { Write-Host $_ }
if ($code -ne 0) { throw "makeappx failed with exit code $code" }
Write-Host "Built $out ($([math]::Round((Get-Item $out).Length / 1MB, 1)) MB)"

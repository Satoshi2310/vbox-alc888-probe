[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,
    [int]$Jobs = 2
)

$ErrorActionPreference = 'Stop'
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path

function Resolve-Directory([string]$EnvironmentValue, [string]$DefaultPath, [string]$Name) {
    $candidate = if ([string]::IsNullOrWhiteSpace($EnvironmentValue)) { $DefaultPath } else { $EnvironmentValue }
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        throw "$Name not found at '$candidate'. Set the corresponding environment variable on the self-hosted runner."
    }
    return (Resolve-Path -LiteralPath $candidate).Path
}

$vcRoot = Resolve-Directory $env:VBOX_VC2010 `
    'C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC' 'Visual Studio 2010 VC'
$sdkRoot = Resolve-Directory $env:VBOX_WINSDK71 `
    'C:\Program Files\Microsoft SDKs\Windows\v7.1' 'Windows SDK 7.1'
$wdkRoot = Resolve-Directory $env:VBOX_WDK71 `
    'C:\WinDDK\7600.16385.1' 'Windows WDK 7.1'

if (-not (Test-Path (Join-Path $vcRoot 'bin\cl.exe'))) {
    throw "cl.exe not found under $vcRoot. Install the VS2010 C++ compiler and SP1 updates."
}
if (-not (Test-Path (Join-Path $sdkRoot 'Include\windows.h'))) {
    throw "Windows SDK headers not found under $sdkRoot."
}
if (-not (Test-Path (Join-Path $wdkRoot 'bin\setenv.bat'))) {
    Write-Warning "Expected WDK setenv.bat not found at the conventional path. Configure may still succeed if your WDK installation differs."
}

$kBuildRoot = if (-not [string]::IsNullOrWhiteSpace($env:KBUILD_PATH)) {
    (Resolve-Path -LiteralPath $env:KBUILD_PATH).Path
} else {
    Join-Path $SourceRoot 'kBuild'
}
if (-not (Test-Path -LiteralPath (Join-Path $kBuildRoot 'footer.kmk') -PathType Leaf)) {
    throw "kBuild root is not valid: $kBuildRoot (footer.kmk missing). Set KBUILD_PATH."
}

$kmkCommand = $null
if (-not [string]::IsNullOrWhiteSpace($env:KMK_EXE)) {
    if (-not (Test-Path -LiteralPath $env:KMK_EXE -PathType Leaf)) {
        throw "KMK_EXE points to a missing file: $env:KMK_EXE"
    }
    $kmkCommand = (Resolve-Path -LiteralPath $env:KMK_EXE).Path
} else {
    $command = Get-Command 'kmk.exe' -ErrorAction SilentlyContinue
    if (-not $command) { $command = Get-Command 'kmk' -ErrorAction SilentlyContinue }
    if (-not $command) { throw 'kmk.exe is not available. Install/configure the kBuild toolchain and set KMK_EXE.' }
    $kmkCommand = $command.Source
}

$configure = Join-Path $SourceRoot 'configure.vbs'
if (-not (Test-Path -LiteralPath $configure -PathType Leaf)) {
    throw "configure.vbs not found in source root $SourceRoot"
}

Write-Host "Configuring VirtualBox source: $SourceRoot"
Write-Host "VC2010: $vcRoot"
Write-Host "SDK71:  $sdkRoot"
Write-Host "WDK71:  $wdkRoot"
Write-Host "kmk:    $kmkCommand"

$configArgs = @(
    '//nologo',
    $configure,
    '--target-arch=amd64',
    "--with-kBuild=$kBuildRoot",
    "--with-vc=$vcRoot",
    "--with-sdk=$sdkRoot",
    "--with-ddk=$wdkRoot",
    '--disable-SDL'
)
& "$env:WINDIR\System32\cscript.exe" @configArgs
if ($LASTEXITCODE -ne 0) { throw "configure.vbs failed with exit code $LASTEXITCODE" }

$envBat = Join-Path $SourceRoot 'env.bat'
if (-not (Test-Path -LiteralPath $envBat -PathType Leaf)) {
    throw "configure.vbs did not generate env.bat at $envBat"
}

$jobs = [Math]::Max(1, $Jobs)
$cmdLine = 'call "{0}" && "{1}" -j{2} VBoxDD' -f $envBat, $kmkCommand, $jobs
Write-Host "Building VBoxDD with $jobs job(s)..."
& $env:ComSpec /d /s /c $cmdLine
if ($LASTEXITCODE -ne 0) { throw "kmk VBoxDD failed with exit code $LASTEXITCODE" }

$expected = Join-Path $SourceRoot 'out\win.amd64\release\bin\VBoxDD.dll'
if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
    $matches = Get-ChildItem -LiteralPath (Join-Path $SourceRoot 'out') -Filter 'VBoxDD.dll' -Recurse -File -ErrorAction SilentlyContinue
    if ($matches.Count -ne 1) {
        throw "Build finished but could not uniquely locate VBoxDD.dll under $(Join-Path $SourceRoot 'out')"
    }
    $expected = $matches[0].FullName
}

$artifactDir = Join-Path $env:GITHUB_WORKSPACE 'artifacts'
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
Copy-Item -LiteralPath $expected -Destination (Join-Path $artifactDir 'VBoxDD.dll') -Force
Write-Host "Artifact staged: $(Join-Path $artifactDir 'VBoxDD.dll')"

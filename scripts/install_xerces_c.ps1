
$ErrorActionPreference = "Stop"

$XERCES_MAJOR = 3
$XERCES_MINOR = 2
$XERCES_PATCH = 3

$XERCES_VERSION = "$XERCES_MAJOR.$XERCES_MINOR.$XERCES_PATCH"
$XSD_BUILD_AREA = "$env:TEMP/build_xerces_c"
$INSTALL_PREFIX = "$env:TEMP/xerces_c"

if (-not (Test-Path $XSD_BUILD_AREA)) { New-Item -ItemType Directory -Path $XSD_BUILD_AREA | Out-Null }
Set-Location $XSD_BUILD_AREA

Write-Host "Download Xerces-C..."
Invoke-WebRequest -Uri "https://github.com/apache/xerces-c/archive/v${XERCES_VERSION}.tar.gz" -OutFile "xerces-c-${XERCES_VERSION}.tar.gz"

Write-Host "Extract Xerces-C..."
tar xzf "xerces-c-${XERCES_VERSION}.tar.gz"
Set-Location "xerces-c-${XERCES_VERSION}"

Write-Host "Configure Xerces-C..."
if (-not (Test-Path "build")) { New-Item -ItemType Directory -Path "build" | Out-Null }
Set-Location "build"
cmake -G "Visual Studio 17 2022" -A x64 -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" ..

Write-Host "Build Xerces-C..."
cmake --build . --config Release --target install

Write-Host "Xerces-C installed to: $INSTALL_PREFIX"

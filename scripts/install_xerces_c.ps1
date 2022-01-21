
$ErrorActionPreference="Stop"

$XERCES_MAJOR=3
$XERCES_MINOR=2
$XERCES_PATCH=3

$XERCES_VERSION="$XERCES_MAJOR.$XERCES_MINOR.$XERCES_PATCH"
$XSD_BUILD_AREA="$env:TEMP/build_xerces_c"
$INSTALL_PREFIX="$env:TEMP/xerces_c"

echo "Create Xerces-C build area..."
mkdir -p ${XSD_BUILD_AREA} -ea 0
cd ${XSD_BUILD_AREA}

echo "Download Xerces-C..."
Invoke-WebRequest -Uri "https://github.com/apache/xerces-c/archive/v${XERCES_VERSION}.tar.gz" -OutFile "xerces-c-${XERCES_VERSION}.tar.gz"

echo "Extract Xerces-C..."
tar xzf xerces-c-${XERCES_VERSION}.tar.gz
cd xerces-c-${XERCES_VERSION}

echo "Configure Xerces-C..."
mkdir build -ea 0
cd build
cmake -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" ..

echo "Build Xerces-C..."
cmake --build . --config Release --target install

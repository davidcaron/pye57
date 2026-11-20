#!/bin/bash

set -e

XERCES_MAJOR=3
XERCES_MINOR=2
XERCES_PATCH=5

XERCES_VERSION=${XERCES_MAJOR}.${XERCES_MINOR}.${XERCES_PATCH}
# SHA-256 of the GitHub tag archive below; update together with the version.
XERCES_SHA256=4042f6f11c9eba745dc0e5f8035d98b442097ee4efc69e4853410e4737a987f8
XSD_BUILD_AREA=/tmp/build_xerces_c

if command -v nproc >/dev/null 2>&1; then
    JOBS=$(nproc)
else
    JOBS=$(sysctl -n hw.ncpu)
fi

echo "Create Xerces-C build area..."
mkdir -p ${XSD_BUILD_AREA}
cd ${XSD_BUILD_AREA}

echo "Download Xerces-C..."
curl -fsSL https://github.com/apache/xerces-c/archive/v${XERCES_VERSION}.tar.gz --output xerces-c-${XERCES_VERSION}.tar.gz
echo "Verify Xerces-C checksum..."
if command -v sha256sum >/dev/null 2>&1; then
    echo "${XERCES_SHA256}  xerces-c-${XERCES_VERSION}.tar.gz" | sha256sum -c -
else
    echo "${XERCES_SHA256}  xerces-c-${XERCES_VERSION}.tar.gz" | shasum -a 256 -c -
fi
echo "Extract Xerces-C..."
tar xzf xerces-c-${XERCES_VERSION}.tar.gz
cd xerces-c-${XERCES_VERSION}

# Check the operating system and install dependencies accordingly
if [[ "$(uname)" == "Darwin" ]]; then
    echo "Installing dependencies on macOS..."
    brew install autoconf automake libtool
    echo "Generate configure script using autoreconf..."
    autoreconf -i
    echo "Configure Xerces-C for macOS..."
    ./configure --prefix=/usr/local --enable-static
    echo "Build Xerces-C..."
    make -j"${JOBS}"
    echo "Install Xerces-C..."
    sudo make install
else
    echo "Installing dependencies on Linux..."
    ./reconf
    ./configure
    echo "Build Xerces-C..."
    make -j"${JOBS}"
    echo "Install Xerces-C..."
    make install
fi

echo "Clean up Xerces-C..."
cd /
rm -rf ${XSD_BUILD_AREA}

echo "Xerces-C installed successfully."



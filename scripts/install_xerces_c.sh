#!/bin/bash

set -e

XERCES_MAJOR=3
XERCES_MINOR=2
XERCES_PATCH=3

XERCES_VERSION=${XERCES_MAJOR}.${XERCES_MINOR}.${XERCES_PATCH}
XSD_BUILD_AREA=/tmp/build_xerces_c

echo "Create Xerces-C build area..."
mkdir -p ${XSD_BUILD_AREA}
cd ${XSD_BUILD_AREA}

echo "Download Xerces-C..."
curl -L https://github.com/apache/xerces-c/archive/v${XERCES_VERSION}.tar.gz --output xerces-c-${XERCES_VERSION}.tar.gz
echo "Extract Xerces-C..."
tar xzf xerces-c-${XERCES_VERSION}.tar.gz
cd  xerces-c-${XERCES_VERSION}
echo "Configure Xerces-C..."
./reconf
./configure
echo "Build Xerces-C..."
make
echo "Install Xerces-C..."
make install

echo "Clean up Xerces-C..."
cd /
rm -rf ${XSD_BUILD_AREA}

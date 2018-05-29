#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
import platform
import subprocess

import setuptools
from setuptools.command.build_ext import build_ext
from setuptools import find_packages, setup, Extension

NAME = 'pye57'
DESCRIPTION = 'Python .e57 files reader/writer'
URL = 'https://www.github.com/davidcaron/pye57'
EMAIL = 'dcaron05@gmail.com'
AUTHOR = 'David Caron'
REQUIRES_PYTHON = '>=3.5.*'
VERSION = None

PYTHON_HOME = os.path.split(sys.executable)[0]
INCLUDE = os.path.join(PYTHON_HOME, r"Library", "include")
LIB_DIR = os.path.join(PYTHON_HOME, r"Library", "lib")

REQUIRED = [
    "numpy",
    "pyquaternion"
]

REQUIRED_FOR_TESTS = [
    "pytest"
]

DEBUG = False
if "--debug" in sys.argv:
    sys.argv.remove("--debug")
    DEBUG = True

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION

REVISION_ID = "pye57-" + about['__version__']


class get_pybind_include(object):
    """Helper class to determine the pybind11 include path
    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


extra_link_args = []

if DEBUG:
    extra_link_args.append("/DEBUG")

libraries = []
library_dirs = [LIB_DIR]
if platform.system() == "Windows":
    libraries.append("xerces-c_3")
else:
    libraries.append("xerces-c")

ext_modules = [
    Extension(
        'pye57.libe57',
        ['pye57/libe57_wrapper.cpp',
         'libE57Format/src/CheckedFile.cpp',
         'libE57Format/src/Decoder.cpp',
         'libE57Format/src/E57Foundation.cpp',
         'libE57Format/src/E57FoundationImpl.cpp',
         'libE57Format/src/E57XmlParser.cpp',
         'libE57Format/src/Encoder.cpp',
         ],
        include_dirs=[
            'libE57Format/include',
            'libE57Format/src',
            'libE57Format/contrib/CRCpp/inc',
            INCLUDE,
            get_pybind_include(),
            get_pybind_include(user=True)
        ],
        libraries=libraries,
        library_dirs=library_dirs,
        language='c++'
    ),
]


# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.
    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    if sys.platform == 'darwin':
        c_opts['unix'] += ['-DMACOS', '-stdlib=libc++', '-mmacosx-version-min=10.7', '-std=c++1y']
    elif sys.platform == 'linux':
        c_opts['unix'] += ['-DLINUX']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append('-DREVISION_ID="%s"' % REVISION_ID)
            opts.append(cpp_flag(self.compiler))
            opts.append('-DCRCPP_USE_CPP11')
            opts.append('-DCRCPP_BRANCHLESS')
            opts.append('-Wno-unused-variable')
            if has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
            opts.append('/DREVISION_ID=\\"%s\\"' % REVISION_ID)
            opts.append('/DWIN32')
            opts.append('/DWINDOWS')
            if DEBUG:
                opts.append('/FS')
        for ext in self.extensions:
            ext.extra_compile_args = opts
        self.debug = DEBUG
        build_ext.build_extensions(self)


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    ext_modules=ext_modules,
    install_requires=REQUIRED,
    setup_requires=["pytest-runner"],
    tests_require=REQUIRED_FOR_TESTS,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    cmdclass={
        'build_ext': BuildExt,
    },
)

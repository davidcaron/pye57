import os
import platform
import shutil
import sys
from pathlib import Path

# Available at setup time due to pyproject.toml
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

HERE = Path(__file__).parent

about = {}
with open(HERE / "src" / "pye57" / "__version__.py") as f:
    exec(f.read(), about)
version = about["__version__"]

libE57_cpp = sorted(map(str, (HERE / "libE57Format" / "src").glob("*.cpp")))

libraries = []
library_dirs = []
include_dirs = [
    "libE57Format/include",
    "libE57Format/src",
    "libE57Format/extern/CRCpp/inc",
]
package_data = []

if platform.system() == "Windows":
    libraries.append("xerces-c_3")

    # using conda
    conda_library_dir = Path(sys.executable).parent / "Library"
    if conda_library_dir.exists():
        library_dirs.append(str(conda_library_dir / "lib"))
        include_dirs.append(str(conda_library_dir / "include"))

    # using cibuildwheel
    xerces_dir = Path(os.environ["TEMP"]) / "xerces_c"
    if xerces_dir.exists():
        library_dirs.append(str(xerces_dir / "lib"))
        include_dirs.append(str(xerces_dir / "include"))
        # include xerces-c dll in the package
        shutil.copy2(xerces_dir / "bin" / "xerces-c_3_2.dll", HERE / "src" / "pye57")
        package_data.append("xerces-c_3_2.dll")

else:
    libraries.append("xerces-c")

ext_modules = [
    Pybind11Extension(
        "pye57.libe57",
        ["src/pye57/libe57_wrapper.cpp"] + libE57_cpp,
        define_macros=[("E57_DLL", "")],
        include_dirs=include_dirs,
        libraries=libraries,
        library_dirs=library_dirs,
        language="c++",
    ),
]

export_header_path = HERE / "libE57Format" / "include" / "E57Export.h"


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = []
        revision_id = "pye57-" + version
        if ct == "unix":
            opts.append(f'-DVERSION_INFO="{version}"')
            opts.append(f'-DREVISION_ID="{revision_id}"')
            opts.append("-DCRCPP_USE_CPP11")
            opts.append("-DCRCPP_BRANCHLESS")
            opts.append("-Wno-unused-variable")
        elif ct == "msvc":
            opts.append(f'/DVERSION_INFO="{version}"')
            opts.append(rf'/DREVISION_ID="\"{revision_id}\""')
            opts.append("/DCRCPP_USE_CPP11")
            opts.append("/DCRCPP_BRANCHLESS")
            opts.append("/DWINDOWS")
        for ext in self.extensions:
            ext.extra_compile_args = opts

        export_header_path.touch()
        try:
            super().build_extensions()
        finally:
            export_header_path.unlink()


with open(HERE / "README.md") as f:
    long_description = "\n" + f.read()

setup(
    name="pye57",
    version=version,
    author="David Caron",
    author_email="dcaron05@gmail.com",
    url="https://www.github.com/davidcaron/pye57",
    description="Python .e57 files reader/writer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["numpy", "pyquaternion"],
    ext_modules=ext_modules,
    packages=["pye57"],
    package_dir={"": "src"},
    # include_package_data=True,
    package_data={"pye57": package_data},
    extras_require={"test": "pytest"},
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    cmdclass={"build_ext": BuildExt},
    zip_safe=False,
    python_requires=">=3.8",
)

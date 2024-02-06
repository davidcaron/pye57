# pye57

[![PyPI](https://img.shields.io/pypi/v/pye57.svg)](https://pypi.org/project/pye57)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pye57.svg)](https://pypi.org/project/pye57)
![GitHub](https://img.shields.io/github/actions/workflow/status/davidcaron/pye57/build.yml?branch=master)

Python wrapper of [LibE57Format](https://github.com/asmaloney/libE57Format) to read and write .e57 point cloud files

## Example usage

```python
import numpy as np
import pye57

e57 = pye57.E57("e57_file.e57")

# read scan at index 0
data = e57.read_scan(0)

# 'data' is a dictionary with the point types as keys
assert isinstance(data["cartesianX"], np.ndarray)
assert isinstance(data["cartesianY"], np.ndarray)
assert isinstance(data["cartesianZ"], np.ndarray)

# other attributes can be read using:
data = e57.read_scan(0, intensity=True, colors=True, row_column=True)
assert isinstance(data["cartesianX"], np.ndarray)
assert isinstance(data["cartesianY"], np.ndarray)
assert isinstance(data["cartesianZ"], np.ndarray)
assert isinstance(data["intensity"], np.ndarray)
assert isinstance(data["colorRed"], np.ndarray)
assert isinstance(data["colorGreen"], np.ndarray)
assert isinstance(data["colorBlue"], np.ndarray)
assert isinstance(data["rowIndex"], np.ndarray)
assert isinstance(data["columnIndex"], np.ndarray)

# the 'read_scan' method filters points using the 'cartesianInvalidState' field
# if you want to get everything as raw, untransformed data, use:
data_raw = e57.read_scan_raw(0)

# writing is also possible, but only using raw data for now
e57_write = pye57.E57("e57_file_write.e57", mode='w')
e57_write.write_scan_raw(data_raw)
# you can specify a header to copy information from
e57_write.write_scan_raw(data_raw, scan_header=e57.get_header(0))

# the ScanHeader object wraps most of the scan information:
header = e57.get_header(0)
print(header.point_count)
print(header.rotation_matrix)
print(header.translation)

# all the header information can be printed using:
for line in header.pretty_print():
    print(line)

# the scan position can be accessed with:
position_scan_0 = e57.scan_position(0)

# the binding is very close to the E57Foundation API
# you can modify the nodes easily from python
imf = e57.image_file
root = imf.root()
data3d = root["data3D"]
scan_0 = data3d[0]
translation_x = scan_0["pose"]["translation"]["x"]
```

## Installation

If you're on linux or Windows, a wheel should be available.

`python -m pip install pye57`

## Building from source

### Cloning the repository and required submodules

Clone a new repository along with the required submodules

`git clone https://github.com/davidcaron/pye57.git --recursive`

If the repository has already been previously cloned, but without the --recursive flag

```
cd pye57 # go to the cloned repository
git submodule init # this will initialise the submodules in the repository
git submodule update # this will update the submodules in the repository
```

### Dependencies on Linux

Install libxerces-c-dev first.

`sudo apt install libxerces-c-dev`

### Dependencies on Windows

To get xerces-c, you can either build from source or if you're using conda:

`conda install -y xerces-c`

### Run `pip install` from the repo source

```
cd pye57
python -m pip install .
```

### Uninstalling

Use pip again

```
python -m pip uninstall pye57
```

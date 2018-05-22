import uuid
import os

from typing import Dict

import numpy as np

from pye57.__version__ import __version__
from pye57 import libe57
from pye57 import ScanHeader

POINT_TYPES = {
    "cartesianX": "d",
    "cartesianY": "d",
    "cartesianZ": "d",
    "intensity": "f",
    "colorRed": "B",
    "colorGreen": "B",
    "colorBlue": "B",
    "rowIndex": "H",
    "columnIndex": "H",
    "cartesianInvalidState": "b",
}


class E57:
    def __init__(self, path, mode="r"):
        if mode not in "rw":
            raise ValueError("Only 'r' and 'w' modes are supported")
        self.path = path
        try:
            self.image_file = libe57.ImageFile(path, mode)
            if mode == "w":
                self.write_default_header()
        except Exception as e:
            try:
                self.image_file.close()
                os.remove(path)
            except (AttributeError, WindowsError, PermissionError):
                pass
            raise e

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.image_file.close()

    @property
    def root(self):
        return self.image_file.root()

    @property
    def data3d(self):
        return self.root["data3D"]

    def get_header(self, index):
        return ScanHeader(self.data3d[index])

    def write_default_header(self):
        imf = self.image_file
        imf.extensionsAdd("", libe57.E57_V1_0_URI)
        self.root.set("formatName", libe57.StringNode(imf, "ASTM E57 3D Imaging Data File"))
        self.root.set("guid", libe57.StringNode(imf, str(uuid.uuid4())))
        self.root.set("versionMajor", libe57.IntegerNode(imf, libe57.E57_FORMAT_MAJOR))
        self.root.set("versionMinor", libe57.IntegerNode(imf, libe57.E57_FORMAT_MINOR))
        self.root.set("e57LibraryVersion", libe57.StringNode(imf, libe57.E57_LIBRARY_ID))
        self.root.set("coordinateMetadata", libe57.StringNode(imf, ""))
        creation_date_time = libe57.StructureNode(imf)
        creation_date_time.set("dateTimeValue", libe57.FloatNode(imf, 0.0))
        creation_date_time.set("isAtomicClockReferenced", libe57.IntegerNode(imf, 0))
        self.root.set("creationDateTime", creation_date_time)
        self.root.set("data3D", libe57.VectorNode(imf, True))
        self.root.set("images2D", libe57.VectorNode(imf, True))

    def make_buffer(self, field_name, capacity, do_conversion=True, do_scaling=True):

        if field_name not in POINT_TYPES:
            raise ValueError("Unknown field name: %s" % field_name)
        np_array = np.empty(capacity, POINT_TYPES[field_name])
        buffer = libe57.SourceDestBuffer(self.image_file,
                                         field_name,
                                         np_array,
                                         capacity,
                                         do_conversion,
                                         do_scaling)
        return np_array, buffer

    def make_buffers(self, field_names, capacity, do_conversion=True, do_scaling=True):
        data = {}
        buffers = libe57.VectorSourceDestBuffer()
        for field in field_names:
            d, b = self.make_buffer(field, capacity, do_conversion=do_conversion, do_scaling=do_scaling)
            data[field] = d
            buffers.append(b)
        return data, buffers

    def read_scan_raw(self, index) -> Dict:
        header = self.get_header(index)
        data = {}
        buffers = libe57.VectorSourceDestBuffer()
        for field in header.point_fields:
            np_array, buffer = self.make_buffer(field, header.point_count)
            data[field] = np_array
            buffers.append(buffer)

        header.points.reader(buffers).read()

        return data

    def read_scan(self, index, intensity=False, colors=False, row_column=False, transform=True) -> np.array:
        header = self.get_header(index)
        n_points = header.point_count

        fields = ["cartesianX", "cartesianY", "cartesianZ"]
        if intensity:
            fields.append("intensity")
        if colors:
            raise NotImplementedError
        if row_column:
            fields.append("rowIndex")
            fields.append("columnIndex")
        fields.append("cartesianInvalidState")

        data, buffers = self.make_buffers(fields, n_points)
        data_reader = header.points.reader(buffers)
        data_reader.read()

        valid = data["cartesianInvalidState"].astype("?")

        xyz = np.array([data["cartesianX"][valid], data["cartesianY"][valid], data["cartesianZ"][valid]])

        del valid, data
        if transform:
            rot, trans = header.rotation_matrix, header.translation
            xyz = np.dot(rot, xyz) + trans.reshape(3, 1)
        return xyz.T

    def write_scan_raw(self, data: Dict, name=None):
        if name is None:
            name = "Scan %s" % len(self.data3d)
        scan_node = libe57.StructureNode(self.image_file)
        scan_node.set("guid", libe57.StringNode(self.image_file, str(uuid.uuid4())))
        scan_node.set("name", libe57.StringNode(self.image_file, name))
        scan_node.set("description", libe57.StringNode(self.image_file, "pye57 v%s" % __version__))

        n_points = data["cartesianX"].shape[0]

        organized = "rowIndex" in data and "columnIndex" in data
        if organized:
            raise NotImplementedError
        else:
            ibox = libe57.StructureNode(self.image_file)
            ibox.set("rowMinimum", libe57.IntegerNode(self.image_file, 0))
            ibox.set("rowMaximum", libe57.IntegerNode(self.image_file, n_points - 1))
            ibox.set("columnMinimum", libe57.IntegerNode(self.image_file, 0))
            ibox.set("columnMaximum", libe57.IntegerNode(self.image_file, 0))
            ibox.set("returnMinimum", libe57.IntegerNode(self.image_file, 0))
            ibox.set("returnMaximum", libe57.IntegerNode(self.image_file, 0))
            scan_node.set("indexBounds", ibox)

        if "intensity" in data:
            intbox = libe57.StructureNode(self.image_file)
            intbox.set("intensityMinimum", libe57.FloatNode(self.image_file, np.min(data["intensity"])))
            intbox.set("intensityMaximum", libe57.FloatNode(self.image_file, np.max(data["intensity"])))
            scan_node.set("intensityLimits", intbox)

        color = all(c in data for c in ["colorRed", "colorGreen", "colorBlue"])
        if color:
            colorbox = libe57.StructureNode(self.image_file)
            colorbox.set("colorRedMinimum", libe57.IntegerNode(self.image_file, 0))
            colorbox.set("colorRedMaximum", libe57.IntegerNode(self.image_file, 255))
            colorbox.set("colorGreenMinimum", libe57.IntegerNode(self.image_file, 0))
            colorbox.set("colorGreenMaximum", libe57.IntegerNode(self.image_file, 255))
            colorbox.set("colorBlueMinimum", libe57.IntegerNode(self.image_file, 0))
            colorbox.set("colorBlueMaximum", libe57.IntegerNode(self.image_file, 255))
            scan_node.set("colorLimits", colorbox)

        bbox_node = libe57.StructureNode(self.image_file)
        bbox_node.set("xMinimum", libe57.FloatNode(self.image_file, np.min(data["cartesianX"])))
        bbox_node.set("xMaximum", libe57.FloatNode(self.image_file, np.max(data["cartesianX"])))
        bbox_node.set("yMinimum", libe57.FloatNode(self.image_file, np.min(data["cartesianY"])))
        bbox_node.set("yMaximum", libe57.FloatNode(self.image_file, np.max(data["cartesianY"])))
        bbox_node.set("zMinimum", libe57.FloatNode(self.image_file, np.min(data["cartesianZ"])))
        bbox_node.set("zMaximum", libe57.FloatNode(self.image_file, np.max(data["cartesianZ"])))
        scan_node.set("cartesianBounds", bbox_node)

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
        header.points.reader(buffers).read()

        valid = data["cartesianInvalidState"].astype("?")

        xyz = np.array([data["cartesianX"][valid], data["cartesianY"][valid], data["cartesianZ"][valid]])

        del valid, data
        if transform:
            rot, trans = header.rotation_matrix, header.translation
            xyz = np.dot(rot, xyz) + trans.reshape(3, 1)
        return xyz.T

    def write_scan_raw(self, data: Dict, name=None, rotation=None, translation=None):
        if name is None:
            name = "Scan %s" % len(self.data3d)

        scan_node = libe57.StructureNode(self.image_file)
        scan_node.set("guid", libe57.StringNode(self.image_file, str(uuid.uuid4())))
        scan_node.set("name", libe57.StringNode(self.image_file, name))
        scan_node.set("description", libe57.StringNode(self.image_file, "pye57 v%s" % __version__))

        n_points = data["cartesianX"].shape[0]

        ibox = libe57.StructureNode(self.image_file)
        if "rowIndex" in data and "columnIndex" in data:
            min_row = np.min(data["rowIndex"])
            max_row = np.max(data["rowIndex"])
            min_col = np.min(data["columnIndex"])
            max_col = np.max(data["columnIndex"])
            ibox.set("rowMinimum", libe57.IntegerNode(self.image_file, min_row))
            ibox.set("rowMaximum", libe57.IntegerNode(self.image_file, max_row))
            ibox.set("columnMinimum", libe57.IntegerNode(self.image_file, min_col))
            ibox.set("columnMaximum", libe57.IntegerNode(self.image_file, max_col))
        else:
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
        cartesian_xyz = ["cartesianX", "cartesianY", "cartesianZ"]
        bb_min = np.array([np.min(data[c]) for c in cartesian_xyz])
        bb_max = np.array([np.max(data[c]) for c in cartesian_xyz])
        bbox_node.set("xMinimum", libe57.FloatNode(self.image_file, bb_min[0]))
        bbox_node.set("xMaximum", libe57.FloatNode(self.image_file, bb_max[0]))
        bbox_node.set("yMinimum", libe57.FloatNode(self.image_file, bb_min[1]))
        bbox_node.set("yMaximum", libe57.FloatNode(self.image_file, bb_max[1]))
        bbox_node.set("zMinimum", libe57.FloatNode(self.image_file, bb_min[2]))
        bbox_node.set("zMaximum", libe57.FloatNode(self.image_file, bb_max[2]))
        scan_node.set("cartesianBounds", bbox_node)

        if rotation is not None and translation is not None:
            pose_node = libe57.StructureNode(self.image_file)
            scan_node.set("pose", pose_node)
            rotation_node = libe57.StructureNode(self.image_file)
            rotation_node.set("w", libe57.FloatNode(self.image_file, rotation[0]))
            rotation_node.set("x", libe57.FloatNode(self.image_file, rotation[1]))
            rotation_node.set("y", libe57.FloatNode(self.image_file, rotation[2]))
            rotation_node.set("z", libe57.FloatNode(self.image_file, rotation[3]))
            pose_node.set("rotation", rotation_node)
            translation_node = libe57.StructureNode(self.image_file)
            translation_node.set("x", libe57.FloatNode(self.image_file, translation[0]))
            translation_node.set("y", libe57.FloatNode(self.image_file, translation[1]))
            translation_node.set("z", libe57.FloatNode(self.image_file, translation[2]))
            pose_node.set("translation", translation_node)

        # # todo: start end times
        # is_atomic_clock_referenced = False
        # start = "date_time"
        # end = "date_time"
        # acquisition_start = libe57.StructureNode(self.image_file)
        # scan_node.set("acquisitionStart", acquisition_start)
        # acquisition_start.set("dateTimeValue", libe57.FloatNode(self.image_file, start))
        # acquisition_start.set("isAtomicClockReferenced", libe57.IntegerNode(self.image_file, is_atomic_clock_referenced))
        # acquisition_end = libe57.StructureNode(self.image_file)
        # scan_node.set("acquisitionEnd", acquisition_end)
        # acquisition_end.set("dateTimeValue", libe57.FloatNode(self.image_file, end))
        # acquisition_end.set("isAtomicClockReferenced", libe57.IntegerNode(self.image_file, is_atomic_clock_referenced))

        points_prototype = libe57.StructureNode(self.image_file)

        is_scaled = False
        precision = libe57.E57_DOUBLE if is_scaled else libe57.E57_SINGLE

        center = (bb_max + bb_min) / 2

        chunk_size = 5_000_000

        x_node = libe57.FloatNode(self.image_file, center[0], precision, bb_min[0], bb_max[0])
        y_node = libe57.FloatNode(self.image_file, center[1], precision, bb_min[1], bb_max[1])
        z_node = libe57.FloatNode(self.image_file, center[2], precision, bb_min[2], bb_max[2])
        points_prototype.set("cartesianX", x_node)
        points_prototype.set("cartesianY", y_node)
        points_prototype.set("cartesianZ", z_node)

        field_names = ["cartesianX", "cartesianY", "cartesianZ"]

        if "intensity" in data:
            intensity_min = np.min(data["intensity"])
            intensity_max = np.max(data["intensity"])
            intensity_node = libe57.FloatNode(self.image_file, intensity_min, precision, intensity_min, intensity_max)
            points_prototype.set("intensity", intensity_node)
            field_names.append("intensity")

        if all(color in data for color in ["colorRed", "colorGreen", "colorBlue"]):
            points_prototype.set("colorRed", libe57.IntegerNode(self.image_file, 0, 0, 255))
            points_prototype.set("colorGreen", libe57.IntegerNode(self.image_file, 0, 0, 255))
            points_prototype.set("colorBlue", libe57.IntegerNode(self.image_file, 0, 0, 255))
            field_names.append("colorRed")
            field_names.append("colorGreen")
            field_names.append("colorBlue")

        if "rowIndex" in data and "columnIndex" in data:
            min_row = np.min(data["rowIndex"])
            max_row = np.max(data["rowIndex"])
            min_col = np.min(data["columnIndex"])
            max_col = np.max(data["columnIndex"])
            points_prototype.set("rowIndex", libe57.IntegerNode(self.image_file, 0, min_row, max_row))
            field_names.append("rowIndex")
            points_prototype.set("columnIndex", libe57.IntegerNode(self.image_file, 0, min_col, max_col))
            field_names.append("columnIndex")

        if "cartesianInvalidState" in data:
            min_state = np.min(data["cartesianInvalidState"])
            max_state = np.max(data["cartesianInvalidState"])
            points_prototype.set("cartesianInvalidState", libe57.IntegerNode(self.image_file, 0, min_state, max_state))
            field_names.append("cartesianInvalidState")

        # other fields
        # // "sphericalRange"
        # // "sphericalAzimuth"
        # // "sphericalElevation"
        # // "timeStamp"
        # // "sphericalInvalidState"
        # // "isColorInvalid"
        # // "isIntensityInvalid"
        # // "isTimeStampInvalid"

        arrays, buffers = self.make_buffers(field_names, chunk_size)

        codecs = libe57.VectorNode(self.image_file, True)
        points = libe57.CompressedVectorNode(self.image_file, points_prototype, codecs)
        scan_node.set("points", points)

        self.data3d.append(scan_node)

        writer = points.writer(buffers)

        current_index = 0
        while current_index != n_points:
            current_chunk = min(n_points - current_index, chunk_size)

            for type_ in POINT_TYPES:
                if type_ in arrays:
                    arrays[type_][:current_chunk] = data[type_][current_index:current_index + current_chunk]

            writer.write(current_chunk)

            current_index += current_chunk

        writer.close()

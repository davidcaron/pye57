import numpy as np

from pye57 import libe57
from pye57 import ScanHeader


class E57:
    def __init__(self, path, mode="r"):
        if mode not in "rw":
            raise ValueError("Only 'r' and 'w' modes are supported")
        self.image_file = libe57.ImageFile(path, mode)

    @property
    def root(self):
        return self.image_file.root()

    @property
    def data3d(self):
        return self.root["data3D"]

    def get_header(self, index):
        return ScanHeader(self.data3d[index])

    def make_buffer(self, field_name, capacity, do_conversion=True, do_scaling=True):
        types = {
            "cartesianX": "d",
            "cartesianY": "d",
            "cartesianZ": "d",
            "intensity": "f",
            "rowIndex": "H",
            "columnIndex": "H",
            "cartesianInvalidState": "b",
        }
        if field_name not in types:
            raise ValueError("Unknown field name: %s" % field_name)
        np_array = np.empty(capacity, types[field_name])
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

    def read_scan_raw(self, index):
        header = self.get_header(index)
        data = {}
        buffers = libe57.VectorSourceDestBuffer()
        for field in header.point_fields:
            np_array, buffer = self.make_buffer(field, header.point_count)
            data[field] = np_array
            buffers.append(buffer)

        header.points.reader(buffers).read()

        return data

    def read_scan(self, index, intensity=False, colors=False, row_column=False, transform=True):
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
            rot, trans = header.rotation, header.translation
            xyz = np.dot(rot, xyz) + trans.reshape(3, 1)
        return xyz.T

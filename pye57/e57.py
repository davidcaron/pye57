import numpy as np

from pye57 import libe57
from pye57 import ScanHeader


class E57:
    def __init__(self, path, mode="r"):
        self.image_file = libe57.ImageFile(path, mode)

    @property
    def root(self):
        return self.image_file.root()

    @property
    def data3d(self):
        return self.root["data3D"]

    def get_header(self, index):
        return ScanHeader(self.data3d[index])

    def make_buffer(self,
                    field_name,
                    capacity,
                    do_conversion=True,
                    do_scaling=True):
        types = {
            "cartesianX": "d",
            "cartesianY": "d",
            "cartesianZ": "d",
            "intensity": "f",
            "rowIndex": "H",
            "columnIndex": "H",
            "cartesianInvalidState": "?",
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

    def read_scan(self, index, intensity=False, color=False, row_column=False, transform=True):
        header = self.get_header(index)
        n_points = header.point_count
        buffers = libe57.VectorSourceDestBuffer()
        x, b_x = self.make_buffer("cartesianX", n_points)
        y, b_y = self.make_buffer("cartesianY", n_points)
        z, b_z = self.make_buffer("cartesianZ", n_points)
        is_valid, b_is_valid = self.make_buffer("cartesianInvalidState", n_points)
        buffers.append(b_x)
        buffers.append(b_y)
        buffers.append(b_z)
        buffers.append(b_is_valid)
        data_reader = header.points.reader(buffers)
        data_reader.read()

        xyz = np.array([x[is_valid], y[is_valid], z[is_valid]])
        del x, y, z
        if transform:
            rot, trans = header.rotation, header.translation
            xyz = np.dot(rot, xyz) + trans.reshape(3, 1)
        return xyz.T

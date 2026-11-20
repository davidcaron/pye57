from typing import Dict, List, Optional

import numpy as np
from pyquaternion import Quaternion

from pye57 import libe57
from pye57.scan_header import ScanHeader
from pye57.utils import convert_spherical_to_cartesian, get_fields


class ScanRawReader:
    """Streams raw point data from a single E57 scan in chunks.

    Wraps a libE57 CompressedVectorReader so that very large scans can be read
    without allocating arrays for every point at once.
    """

    def __init__(
        self,
        scan_node,
        image_file,
        points_per_chunk: int,
        ignore_unsupported_fields: bool = False,
        fields: Optional[List[str]] = None,
    ):
        _check_points_per_chunk(points_per_chunk)
        self._scan_node = scan_node
        self._image_file = image_file
        self._points_per_chunk = points_per_chunk
        self._ignore_unsupported_fields = ignore_unsupported_fields
        self._fields = fields
        self._reader = None
        self._closed = False

    @property
    def is_open(self) -> bool:
        return not self._closed and self._reader is not None and self._reader.isOpen()

    def read(self) -> Optional[Dict]:
        """Read the next chunk of points, or return None when the scan is exhausted."""
        chunk = self._next_chunk()
        if chunk is None:
            return None
        return {field: arr.copy() for field, arr in chunk.items()}

    def _next_chunk(self) -> Optional[Dict]:
        # Returns views into the reader's buffers, which the next read overwrites.
        if self._closed:
            raise ValueError("read() called on a closed ScanRawReader")
        if self._reader is None:
            self._open_reader()
        n = self._reader.read()
        if n == 0:
            self.close()
            return None
        return {field: arr[:n] for field, arr in self._data.items()}

    def _open_reader(self):
        from pye57.e57 import SUPPORTED_POINT_FIELDS

        points_node = self._scan_node["points"]

        if self._fields is None:
            point_fields = get_fields(libe57.StructureNode(points_node.prototype()))
            supported = []
            unsupported = []
            for field in point_fields:
                if field in SUPPORTED_POINT_FIELDS:
                    supported.append(field)
                else:
                    unsupported.append(field)
            if unsupported and not self._ignore_unsupported_fields:
                raise ValueError(
                    "Unsupported point fields: %s.\n"
                    "Consider using 'ignore_unsupported_fields' to skip them." % unsupported
                )
        else:
            for field in self._fields:
                if field not in SUPPORTED_POINT_FIELDS:
                    raise ValueError("Unsupported point field: %s" % field)
            supported = self._fields

        self._data = {}
        buffers = libe57.VectorSourceDestBuffer()
        for field in supported:
            arr = np.empty(self._points_per_chunk, SUPPORTED_POINT_FIELDS[field])
            buffers.append(libe57.SourceDestBuffer(
                self._image_file, field, arr, self._points_per_chunk, True, True
            ))
            self._data[field] = arr

        self._reader = points_node.reader(buffers)

    def close(self) -> None:
        if self._reader is not None and self._reader.isOpen():
            self._reader.close()
        self._closed = True

    def __enter__(self) -> "ScanRawReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __iter__(self) -> "ScanRawReader":
        return self

    def __next__(self) -> Dict:
        chunk = self.read()
        if chunk is None:
            raise StopIteration
        return chunk


class ScanReader:
    """Streams transformed point data from a single E57 scan in chunks.

    Mirrors the semantics of `E57.read_scan`, but yields
    one chunk at a time so very large scans can be processed without loading
    every point into memory at once.
    """
    
    def __init__(
        self,
        scan_node,
        image_file,
        points_per_chunk: int,
        *,
        intensity: bool = False,
        colors: bool = False,
        row_column: bool = False,
        transform: bool = True,
        ignore_missing_fields: bool = False,
    ):
        from pye57.e57 import (
            COORDINATE_SYSTEMS,
            SUPPORTED_CARTESIAN_POINT_FIELDS,
            SUPPORTED_SPHERICAL_POINT_FIELDS,
        )

        _check_points_per_chunk(points_per_chunk)
        header = ScanHeader(scan_node)
        coordinate_system = header.get_coordinate_system(COORDINATE_SYSTEMS)
        if coordinate_system is COORDINATE_SYSTEMS.CARTESIAN:
            self._is_spherical = False
            valid_field = "cartesianInvalidState"
            fields = list(SUPPORTED_CARTESIAN_POINT_FIELDS.keys())
        else:
            self._is_spherical = True
            valid_field = "sphericalInvalidState"
            fields = list(SUPPORTED_SPHERICAL_POINT_FIELDS.keys())
        if intensity:
            fields.append("intensity")
        if colors:
            fields.append("colorRed")
            fields.append("colorGreen")
            fields.append("colorBlue")
        if row_column:
            fields.append("rowIndex")
            fields.append("columnIndex")
        fields.append(valid_field)

        for field in fields[:]:
            if field not in header.point_fields:
                if ignore_missing_fields:
                    fields.remove(field)
                else:
                    raise ValueError(
                        "Requested to read a field (%s) which is absent from the e57 file. "
                        "Consider using 'ignore_missing_fields' to skip it." % field
                    )

        self._valid_field = valid_field if valid_field in fields else None
        self._transform = transform
        if transform and header.has_pose():
            self._rotation_matrix = Quaternion(header.rotation).rotation_matrix
            self._translation = header.translation
        else:
            self._rotation_matrix = None
            self._translation = None

        self._raw = ScanRawReader(scan_node, image_file, points_per_chunk, fields=fields)

    @property
    def is_open(self) -> bool:
        return self._raw.is_open

    def read(self) -> Optional[Dict]:
        """Read the next chunk of points, or return None when the scan is exhausted."""
        data = self._raw._next_chunk()
        if data is None:
            return None

        # Both branches copy out of the raw reader's buffers, which the next read reuses.
        if self._valid_field is not None:
            valid = ~data.pop(self._valid_field).astype("?")
            data = {field: arr[valid] for field, arr in data.items()}
        else:
            data = {field: arr.copy() for field, arr in data.items()}

        if self._transform:
            if self._is_spherical:
                rae = np.array([
                    data["sphericalRange"],
                    data["sphericalAzimuth"],
                    data["sphericalElevation"],
                ]).T
                xyz = convert_spherical_to_cartesian(rae)
            else:
                xyz = np.array([
                    data["cartesianX"],
                    data["cartesianY"],
                    data["cartesianZ"],
                ]).T
            if self._rotation_matrix is not None:
                xyz = (np.dot(self._rotation_matrix, xyz.T) + self._translation.reshape(3, 1)).T
            data["cartesianX"] = xyz[:, 0]
            data["cartesianY"] = xyz[:, 1]
            data["cartesianZ"] = xyz[:, 2]

        return data

    # Chunks from read() are already independent of the reader's buffers.
    _next_chunk = read

    def close(self) -> None:
        self._raw.close()

    def __enter__(self) -> "ScanReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __iter__(self) -> "ScanReader":
        return self

    def __next__(self) -> Dict:
        chunk = self.read()
        if chunk is None:
            raise StopIteration
        return chunk


def concatenate_chunks(chunks: List[Dict]) -> Dict:
    """Concatenate a list of chunks (as yielded by `ScanRawReader` or `ScanReader`)
    into a single dict-of-arrays - the same structure returned by `E57.read_scan_raw`
    or `E57.read_scan`.

    Returns an empty dict if `chunks` is empty.
    """
    if not chunks:
        return {}
    return {field: np.concatenate([c[field] for c in chunks]) for field in chunks[0]}


def _read_all_chunks(reader, point_count: int) -> Dict:
    """Read every chunk from `reader` into one array per field, then close it.

    The arrays are allocated once for `point_count` points and each chunk is copied
    straight into place, so peak memory is the result plus a single chunk. If fewer
    points come back (invalid points filtered out by `ScanReader`), the arrays are
    trimmed to the number actually read.
    """
    data = {}
    offset = 0
    with reader:
        while True:
            chunk = reader._next_chunk()
            if chunk is None:
                break
            n = 0
            for field, arr in chunk.items():
                if field not in data:
                    data[field] = np.empty(point_count, arr.dtype)
                n = len(arr)
                data[field][offset:offset + n] = arr
            offset += n
    if offset < point_count:
        for field in data:
            data[field] = data[field][:offset].copy()
    return data


def _check_points_per_chunk(points_per_chunk) -> None:
    if (
        not isinstance(points_per_chunk, (int, np.integer))
        or isinstance(points_per_chunk, bool)
        or points_per_chunk < 1
    ):
        raise ValueError("points_per_chunk must be a positive integer, got %r" % (points_per_chunk,))

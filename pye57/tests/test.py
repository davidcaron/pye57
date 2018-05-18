import pytest
import os
import time

import numpy as np

import pye57
from pye57 import libe57
from pye57.utils import get_fields


def test_hi():
    assert libe57.__doc__


def test_data(*args):
    return os.path.join("test_data", *args)


def delete_retry(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except WindowsError:
        time.sleep(0.1)
        if os.path.exists(path):
            os.remove(path)


@pytest.fixture
def e57_path():
    return test_data("test.e57")


@pytest.fixture
def temp_e57_write(request):
    path = test_data("test_write.e57")
    request.addfinalizer(lambda: delete_retry(path))
    return path


@pytest.fixture
def image_and_points(e57_path):
    f = libe57.ImageFile(e57_path, mode="r")
    scan_0 = libe57.StructureNode(libe57.VectorNode(f.root().get("/data3D")).get(0))
    points = libe57.CompressedVectorNode(scan_0.get("points"))
    return f, points


def test_open_imagefile(e57_path):
    f = libe57.ImageFile(e57_path, mode="r")
    assert f.isOpen()
    f.close()


def test_open_imagefile_write(temp_e57_write):
    f = libe57.ImageFile(temp_e57_write, mode="w")
    assert f.isOpen()
    f.close()


def test_e57_mode_error(temp_e57_write):
    with pytest.raises(ValueError):
        f = pye57.E57(temp_e57_write, mode="pasta")


def test_get_structure_names(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    root = f.root()
    names = []
    for id_ in range(root.childCount()):
        names.append(root.get(id_).pathName())
    assert names == ['/formatName', '/guid', '/versionMajor', '/versionMinor', '/e57LibraryVersion',
                     '/coordinateMetadata', '/creationDateTime', '/data3D', '/images2D']


def test_get_data3d_nodes(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    root = f.root()
    node = root.get("data3D")
    data3d = libe57.VectorNode(node)
    scan_count = data3d.childCount()
    assert scan_count == 4
    for scan_id in range(scan_count):
        assert isinstance(data3d.get(scan_id), libe57.Node)


def test_get_read_data3d(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    scan_0 = libe57.StructureNode(libe57.VectorNode(f.root().get("/data3D")).get(0))
    points = libe57.CompressedVectorNode(scan_0.get("points"))
    assert points.childCount() == 281300


def test_source_dest_buffers(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    capacity = 1000
    types = list("bBhHlLq?fd")
    sizes = [1, 1, 2, 2, 4, 4, 8, 1, 4, 8]
    buffers = libe57.VectorSourceDestBuffer()
    for t in types:
        data = np.zeros(capacity, t)
        sdb = libe57.SourceDestBuffer(f, "something", data, capacity, True, True)
        buffers.append(sdb)

    for t, sdb, size, in zip(types, buffers, sizes):
        assert sdb.pathName() == "something"
        assert sdb.capacity() == capacity
        assert sdb.stride() == size
        assert sdb.doScaling()
        assert sdb.doConversion()


def test_source_dest_buffers_raises(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    capacity = 1000
    data = np.zeros(capacity, "i")
    with pytest.raises(ValueError):
        libe57.SourceDestBuffer(f, "something", data, capacity, True, True)


def test_read_points_x(image_and_points):
    imf, points = image_and_points
    bufs = libe57.VectorSourceDestBuffer()
    capacity = 10000
    X = np.zeros(capacity, "f")
    bufs.append(libe57.SourceDestBuffer(imf, "cartesianX", X, capacity, True, True))
    data_reader = points.reader(bufs)
    size = data_reader.read()
    assert size == capacity
    assert not np.all(np.zeros(capacity, "f") == X)


def test_index_out_of_range(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    with pytest.raises(IndexError):
        scan = f.root()["data3D"][-1]
    with pytest.raises(IndexError):
        scan = f.root()["data3D"][5]
    scan_0 = f.root()["data3D"][0]
    with pytest.raises(IndexError):
        r = scan_0["pose"]["rotation"][-1]
    with pytest.raises(IndexError):
        r = scan_0["pose"]["rotation"][5]


def test_read_header(e57_path):
    f = libe57.ImageFile(e57_path, "r")
    data3d = f.root()["data3D"]
    headers = pye57.ScanHeader.from_data3d(data3d)
    fields = ['cartesianX', 'cartesianY', 'cartesianZ', 'intensity', 'rowIndex', 'columnIndex', 'cartesianInvalidState']
    for header in headers:
        assert fields == header.point_fields
    assert headers[0].pretty_print()
    scan_0_rot = [[-0.4443, 0.8958, 0.],
                  [-0.8958, -0.4443, 0.],
                  [0., 0., 1.]]
    assert np.allclose(scan_0_rot, headers[0].rotation, atol=1e-3)
    scan_0_tra = [301336.23199, 5042597.23676, 15.46649]
    assert np.allclose(scan_0_tra, headers[0].translation)


def test_read_xyz(e57_path):
    e57 = pye57.E57(e57_path)
    xyz = e57.read_scan(0)
    assert np.any(xyz)


def test_read_raw(e57_path):
    e57 = pye57.E57(e57_path)
    header = e57.get_header(0)
    fields = header.point_fields
    data = e57.read_scan_raw(0)
    assert sorted(fields) == sorted(data.keys())
    assert np.any(data["cartesianX"])
    assert len(data["cartesianX"]) == header.point_count


def test_constants():
    assert libe57.CHECKSUM_POLICY_SPARSE == 25

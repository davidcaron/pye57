import pytest
import os
import time

import numpy as np

import pye57
from pye57 import libe57
from pye57.utils import get_node, copy_node

try:
    from exceptions import WindowsError
except ImportError:
    class WindowsError(OSError):
        pass


def test_hi():
    assert libe57.__doc__


def sample_data(*args):
    here = os.path.split(__file__)[0]
    return os.path.join(here, "test_data", *args)


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
    return sample_data("test.e57")


@pytest.fixture
def e57_spherical_path():
    return sample_data("testSpherical.e57")


@pytest.fixture
def e57_with_data_and_images_path():
    # From http://www.libe57.org/data.html
    return sample_data("pumpAVisualReferenceImage.e57")

@pytest.fixture
def e57_with_normals_path():
    # created using Python's open3d and CloudCompare
    return sample_data("testWithNormals.e57")

@pytest.fixture
def temp_e57_write(request):
    path = sample_data("test_write.e57")
    request.addfinalizer(lambda: delete_retry(path))
    return path


@pytest.fixture
def image_and_points(e57_path):
    f = libe57.ImageFile(e57_path, mode="r")
    scan_0 = libe57.StructureNode(libe57.VectorNode(f.root().get("/data3D")).get(0))
    points = libe57.CompressedVectorNode(scan_0.get("points"))
    return f, points


def test_constants():
    assert libe57.CHECKSUM_POLICY_NONE == 0
    assert libe57.CHECKSUM_POLICY_SPARSE == 25
    assert libe57.CHECKSUM_POLICY_HALF == 50
    assert libe57.CHECKSUM_POLICY_ALL == 100
    assert libe57.E57_INT8_MIN == -128
    assert libe57.E57_INT8_MAX == 127
    assert libe57.E57_INT16_MIN == -32768
    assert libe57.E57_INT16_MAX == 32767
    assert libe57.E57_INT32_MIN == -2147483647 - 1
    assert libe57.E57_INT32_MAX == 2147483647
    assert libe57.E57_INT64_MIN == -9223372036854775807 - 1
    assert libe57.E57_INT64_MAX == 9223372036854775807
    assert libe57.E57_UINT8_MIN == 0
    assert libe57.E57_UINT8_MAX == 255
    assert libe57.E57_UINT16_MIN == 0
    assert libe57.E57_UINT16_MAX == 65535
    assert libe57.E57_UINT32_MIN == 0
    assert libe57.E57_UINT32_MAX == 4294967295
    assert libe57.E57_UINT64_MIN == 0
    assert libe57.E57_UINT64_MAX == 18446744073709551615


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


def test_unsupported_point_field(temp_e57_write):
    with pye57.E57(temp_e57_write, mode="w") as f:
        with pytest.raises(ValueError):
            data = {"cartesianX": np.random.rand(10),
                    "bananas": np.random.rand(10)}
            f.write_scan_raw(data)


def test_ignore_unsupported_fields(e57_with_normals_path):
    e57 = pye57.E57(e57_with_normals_path)
    with pytest.raises(ValueError):
        e57.read_scan_raw(0)
    e57.read_scan_raw(0, ignore_unsupported_fields=True)


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
    assert np.allclose(scan_0_rot, headers[0].rotation_matrix, atol=1e-3)
    scan_0_tra = [301336.23199, 5042597.23676, 15.46649]
    assert np.allclose(scan_0_tra, headers[0].translation)


def test_read_xyz(e57_path):
    e57 = pye57.E57(e57_path)
    xyz = e57.read_scan(0)
    assert np.any(xyz)


def test_read_header_spherical(e57_spherical_path):
    f = libe57.ImageFile(e57_spherical_path, "r")
    data3d = f.root()["data3D"]
    headers = pye57.ScanHeader.from_data3d(data3d)
    fields = ['sphericalRange', 'sphericalAzimuth', 'sphericalElevation', 'intensity', 'colorRed', 'colorGreen', 'colorBlue', 'sphericalInvalidState']
    for header in headers:
        assert fields == header.point_fields
    assert headers[0].pretty_print()


def test_read_xyz_spherical(e57_spherical_path):
    e57 = pye57.E57(e57_spherical_path)
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


def test_read_write_single_scan(e57_path, temp_e57_write):
    e57 = pye57.E57(e57_path)
    header_source = e57.get_header(0)
    with pye57.E57(temp_e57_write, mode="w") as e57_write:
        raw_data_0 = e57.read_scan_raw(0)
        e57_write.write_scan_raw(raw_data_0, rotation=header_source.rotation, translation=header_source.translation)
    scan_0 = pye57.E57(e57_path).read_scan_raw(0)
    written = pye57.E57(temp_e57_write)
    header = written.get_header(0)
    assert np.allclose(header.rotation, header_source.rotation)
    assert np.allclose(header.translation, header_source.translation)
    scan_0_written = written.read_scan_raw(0)
    fields = "cartesianX cartesianY cartesianZ intensity rowIndex columnIndex cartesianInvalidState".split()
    for field in fields:
        assert np.allclose(scan_0[field], scan_0_written[field])

    scan_0 = e57.read_scan(0)
    scan_0_written = written.read_scan(0)
    for field in scan_0:
        assert np.allclose(scan_0[field], scan_0_written[field])


def test_copy_file(e57_path, temp_e57_write):
    e57 = pye57.E57(e57_path)
    with pye57.E57(temp_e57_write, mode="w") as f:
        for scan_id in range(e57.scan_count):
            header = e57.get_header(scan_id)
            data = e57.read_scan_raw(scan_id)
            f.write_scan_raw(data, scan_header=header)
            header_written = f.get_header(scan_id)
            assert header_written.guid
            assert header_written.temperature == header_written.temperature
            assert header_written.relativeHumidity == header_written.relativeHumidity
            assert header_written.atmosphericPressure == header_written.atmosphericPressure
            assert header_written.rowMinimum == header.rowMinimum
            assert header_written.rowMaximum == header.rowMaximum
            assert header_written.columnMinimum == header.columnMinimum
            assert header_written.columnMaximum == header.columnMaximum
            assert header_written.returnMinimum == header.returnMinimum
            assert header_written.returnMaximum == header.returnMaximum
            assert header_written.intensityMinimum == header.intensityMinimum
            assert header_written.intensityMaximum == header.intensityMaximum
            assert header_written.xMinimum == header.xMinimum
            assert header_written.xMaximum == header.xMaximum
            assert header_written.yMinimum == header.yMinimum
            assert header_written.yMaximum == header.yMaximum
            assert header_written.zMinimum == header.zMinimum
            assert header_written.zMaximum == header.zMaximum
            assert np.allclose(header_written.rotation, header.rotation)
            assert np.allclose(header_written.translation, header.translation)
            assert header_written.acquisitionStart_dateTimeValue == header.acquisitionStart_dateTimeValue
            assert header_written.acquisitionStart_isAtomicClockReferenced == header.acquisitionStart_isAtomicClockReferenced
            assert header_written.acquisitionEnd_dateTimeValue == header.acquisitionEnd_dateTimeValue
            assert header_written.acquisitionEnd_isAtomicClockReferenced == header.acquisitionEnd_isAtomicClockReferenced
            # todo: point groups
            # header.pointGroupingSchemes["groupingByLine"]["idElementName"].value()
            # header.pointGroupingSchemes["groupingByLine"]["groups"]

        assert f.scan_count == e57.scan_count


def test_read_color_absent(e57_path):
    e57 = pye57.E57(e57_path)
    with pytest.raises(ValueError):
        data = e57.read_scan(0, colors=True)


def test_scan_position(e57_path):
    e57 = pye57.E57(e57_path)
    assert np.allclose(e57.scan_position(3), np.array([[3.01323456e+05, 5.04260184e+06, 1.56040279e+01]]))


BUFFER_TYPES = {
    libe57.FloatNode: 'd',
    libe57.IntegerNode: 'l',
    libe57.ScaledIntegerNode: 'd'
}


def make_buffer(node: libe57.Node, capacity: int):
    node_type = type(node)
    if node_type not in BUFFER_TYPES:
        raise ValueError("Unsupported field type!")

    buffer_type = BUFFER_TYPES[node_type]

    np_array = np.empty(capacity, buffer_type)
    buffer = libe57.SourceDestBuffer(
        node.destImageFile(), node.elementName(), np_array, capacity, True, True)
    return np_array, buffer


def make_buffers(node: libe57.StructureNode, capacity: int):
    data = {}
    buffers = libe57.VectorSourceDestBuffer()
    for i in range(node.childCount()):
        field = get_node(node, i)
        d, b = make_buffer(field, capacity)
        data[field.elementName()] = d
        buffers.append(b)
    return data, buffers


def copy_compressed_vector_data(in_node: libe57.Node, out_node: libe57.Node):
    chunk_size = 100000

    in_prototype = libe57.StructureNode(in_node.prototype())
    out_prototype = libe57.StructureNode(out_node.prototype())

    in_data, in_buffers = make_buffers(in_prototype, chunk_size)
    out_data, out_buffers = make_buffers(out_prototype, chunk_size)

    in_reader = in_node.reader(in_buffers)
    out_writer = out_node.writer(out_buffers)

    n_points = in_node.childCount()
    current_index = 0
    while current_index != n_points:
        current_chunk = min(n_points - current_index, chunk_size)

        in_reader.read()
        for field in in_data:
            out_data[field][:current_chunk] = in_data[field][:current_chunk]

        out_writer.write(current_chunk)

        current_index += current_chunk

    in_reader.close()
    out_writer.close()


def copy_blob_data(in_node, out_node):
    chunk_size = 100000

    byte_count = in_node.byteCount()
    blob_buffer = np.empty(chunk_size, np.ubyte)
    current_index = 0
    while current_index != byte_count:
        current_chunk = min(byte_count - current_index, chunk_size)

        in_node.read(blob_buffer, current_index, current_chunk)
        out_node.write(blob_buffer, current_index, current_chunk)

        current_index += current_chunk


def test_clone_e57(e57_with_data_and_images_path, temp_e57_write):

    in_image = libe57.ImageFile(e57_with_data_and_images_path, "r")
    out_image = libe57.ImageFile(temp_e57_write, "w")

    for i in range(in_image.extensionsCount()):
        out_image.extensionsAdd(
            in_image.extensionsPrefix(i),
            in_image.extensionsUri(i)
        )
    
    in_root = in_image.root()
    out_root = out_image.root()

    compressed_node_pairs = []
    for i in range(in_root.childCount()):
        in_child = get_node(in_root, i)
        in_child_name = in_child.elementName()
        out_child, out_child_compressed_node_pairs, out_child_blob_node_pairs = copy_node(in_child, out_image)

        out_root.set(in_child_name, out_child)
        compressed_node_pairs.extend(out_child_compressed_node_pairs)
    
    for compressed_node_pair in compressed_node_pairs:
        copy_compressed_vector_data(compressed_node_pair['in'], compressed_node_pair['out'])

    for blob_node_pair in out_child_blob_node_pairs:
        copy_blob_data(blob_node_pair['in'], blob_node_pair['out'])

    in_image.close()
    out_image.close()


def test_write_e57_with_rowindex_and_columnindex_omiting_low_values(temp_e57_write):

    with pye57.E57(temp_e57_write, mode='w') as e57:
        # set some test points with missing row and column 0 (so np.min of it in write_scan_raw is larger than 0)
        data_raw = {}
        data_raw["cartesianX"] = np.array([0, 1, 2, 3]).astype(float)
        data_raw["cartesianY"] = np.array([0, 1, 2, 3]).astype(float)
        data_raw["cartesianZ"] = np.array([0, 1, 2, 3]).astype(float)
        data_raw["rowIndex"] = np.array([1, 1, 2, 3])
        data_raw["columnIndex"] = np.array([1, 1, 2, 3])

        try:
            # the next line will throw without the suggested fix
            e57.write_scan_raw(data_raw, name='test_output_with_row_and_column')
        except pye57.libe57.E57Exception as ex:
            print(ex)
            assert False
    
    assert os.path.isfile(temp_e57_write)

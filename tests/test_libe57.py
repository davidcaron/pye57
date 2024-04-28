import pytest
import numpy
from pye57 import libe57, E57
from pye57.e57 import SUPPORTED_POINT_FIELDS
from pye57.utils import get_node

from .test_main import sample_data

BUFFER_TYPES = {
    libe57.FloatNode: 'd',
    libe57.IntegerNode: 'l',
    libe57.ScaledIntegerNode: 'd'
}

def make_buffer(node_field, capacity):
    node_field_type = type(node_field)
    if node_field_type not in BUFFER_TYPES:
        raise ValueError("Unsupported field type!")
    
    buffer_type = BUFFER_TYPES[node_field_type]

    np_array = numpy.empty(capacity, buffer_type)
    buffer = libe57.SourceDestBuffer(
        node_field.destImageFile(), node_field.elementName(), np_array, capacity, True, True)
    return np_array, buffer

def make_buffers(node: libe57.StructureNode, capacity):
    data = {}
    buffers = libe57.VectorSourceDestBuffer()
    for i in range(0, node.childCount()):
        field = get_node(node, i)
        d, b = make_buffer(field, capacity)
        data[field.elementName()] = d
        buffers.append(b)
    return data, buffers

def copy_compressed_vector_data(in_node, out_node):
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
    blob_buffer = numpy.empty(chunk_size, numpy.ubyte)
    current_index = 0
    while current_index != byte_count:
        current_chunk = min(byte_count - current_index, chunk_size)

        in_node.read(blob_buffer, current_index, current_chunk)
        out_node.write(blob_buffer, current_index, current_chunk)

        current_index += current_chunk

def copy_node(node, dest_image):
    compressed_node_pairs = []
    blob_node_pairs = []

    out_node = None
    # 'Element' Types
    if (isinstance(node, libe57.FloatNode)):
        out_node = libe57.FloatNode(
            dest_image,
            value=node.value(),
            precision=node.precision(),
            minimum=node.minimum(),
            maximum=node.maximum())

    elif (isinstance(node, libe57.IntegerNode)):
        out_node = libe57.IntegerNode(
            dest_image,
            value=node.value(),
            minimum=node.minimum(),
            maximum=node.maximum())

    elif (isinstance(node, libe57.ScaledIntegerNode)):
        out_node = libe57.ScaledIntegerNode(
            dest_image,
            node.rawValue(),
            minimum=node.minimum(),
            maximum=node.maximum(),
            scale=node.scale(),
            offset=node.offset())

    elif (isinstance(node, libe57.StringNode)):
        out_node = libe57.StringNode(
            dest_image,
            node.value())

    # 'Container' Types
    elif (isinstance(node, libe57.CompressedVectorNode)):
        in_prototype = libe57.StructureNode(node.prototype())
        out_prototype, _, _  = copy_node(in_prototype, dest_image)
        out_codecs, _, _ = copy_node(node.codecs(), dest_image)

        out_node = libe57.CompressedVectorNode(dest_image, out_prototype, out_codecs)

        compressed_node_pairs.append({ 'in': node, 'out': out_node })

    elif isinstance(node, libe57.StructureNode):
        out_node = libe57.StructureNode(dest_image)
        for i in range(0, node.childCount()):
            in_child = get_node(node, i)
            in_child_name = in_child.elementName()
            out_child, out_child_compressed_node_pairs, out_child_blob_node_pairs = copy_node(in_child, dest_image)

            out_node.set(in_child_name, out_child)
            compressed_node_pairs.extend(out_child_compressed_node_pairs)
            blob_node_pairs.extend(out_child_blob_node_pairs)

    elif isinstance(node, libe57.VectorNode):
        out_node = libe57.VectorNode(dest_image, allowHeteroChildren=node.allowHeteroChildren())
        for i in range(0, node.childCount()):
            in_child = get_node(node, i)
            in_child_name = f'{i}'
            out_child, out_child_compressed_node_pairs, out_child_blob_node_pairs = copy_node(in_child, dest_image)

            out_node.append(out_child)
            compressed_node_pairs.extend(out_child_compressed_node_pairs)
            blob_node_pairs.extend(out_child_blob_node_pairs)

    if (isinstance(node, libe57.BlobNode)):
        out_node = libe57.BlobNode(dest_image, node.byteCount())
        blob_node_pairs.append({ 'in': node, 'out': out_node })

    return out_node, compressed_node_pairs, blob_node_pairs

@pytest.fixture
def e57_path():
    # From http://www.libe57.org/data.html
    return sample_data("pumpAVisualReferenceImage.e57")

@pytest.fixture
def temp_e57_write(request):
    path = sample_data("test_write.e57")
    request.addfinalizer(lambda: delete_retry(path))
    return path

def test_clone_e57(e57_path, temp_e57_write):

    in_image = libe57.ImageFile(e57_path, "r")
    out_image = libe57.ImageFile(temp_e57_write, "w")

    for i in range(0, in_image.extensionsCount()):
        out_image.extensionsAdd(
            in_image.extensionsPrefix(i),
            in_image.extensionsUri(i)
        )
    
    in_root = in_image.root()
    out_root = out_image.root()

    compressed_node_pairs = []
    for i in range(0, in_root.childCount()):
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

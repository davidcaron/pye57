from pye57 import libe57
from pye57.libe57 import NodeType


def get_fields(node):
    return [node.get(id_).elementName() for id_ in range(node.childCount())]


def get_node(node, name):
    cast = {
        NodeType.E57_BLOB: libe57.BlobNode,
        NodeType.E57_COMPRESSED_VECTOR: libe57.CompressedVectorNode,
        NodeType.E57_FLOAT: libe57.FloatNode,
        NodeType.E57_INTEGER: libe57.IntegerNode,
        NodeType.E57_SCALED_INTEGER: libe57.ScaledIntegerNode,
        NodeType.E57_STRING: libe57.StringNode,
        NodeType.E57_STRUCTURE: libe57.StructureNode,
        NodeType.E57_VECTOR: libe57.VectorNode
    }
    n = node.get(name)
    return cast[n.type()](n)

from typing import Type

from pye57 import libe57
from pye57.libe57 import NodeType

import numpy as np

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

def convert_spherical_to_cartesian(rae: Type[np.ndarray])-> Type[np.ndarray]:
    """
    Converts spherical(rae) to cartesian(xyz), where rae = range, azimuth(theta), 
    elevation(phi). 
    
    Reference for formula: http://www.libe57.org/bestCoordinates.html (Note: the 
    formula is different from the one online, so please one at the above reference)
    """
    return np.concatenate((
            rae[:, :1] * np.cos(rae[:, 2:3]) * np.cos(rae[:, 1:2]),
            rae[:, :1] * np.cos(rae[:, 2:3]) * np.sin(rae[:, 1:2]),
            rae[:, :1] * np.sin(rae[:, 2:3])
        ), axis=1)
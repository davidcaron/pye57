import numpy as np
from pyquaternion import Quaternion

from pye57 import libe57
from pye57.utils import get_fields, get_node


class ScanHeader:
    def __init__(self, scan_node):
        self.node = scan_node
        points = libe57.CompressedVectorNode(self.node.get("points"))
        self.point_fields = get_fields(libe57.StructureNode(points.prototype()))
        self.scan_fields = get_fields(self.node)

    @classmethod
    def from_data3d(cls, data3d):
        return [cls(scan) for scan in data3d]

    def _assert_pose(self):
        if not self.node.isDefined("pose"):
            raise ValueError("Scan header doesn't contain a pose")

    @property
    def points(self):
        return self.node["points"]

    @property
    def point_count(self):
        return self.points.childCount()

    @property
    def rotation_matrix(self) -> np.array:
        self._assert_pose()
        q = Quaternion([e.value() for e in self.node["pose"]["rotation"]])
        return q.rotation_matrix

    @property
    def rotation(self) -> np.array:
        self._assert_pose()
        q = Quaternion([e.value() for e in self.node["pose"]["rotation"]])
        return q.elements

    @property
    def translation(self):
        self._assert_pose()
        return np.array([e.value() for e in self.node["pose"]["translation"]])

    def pretty_print(self, node=None, indent=""):
        if node is None:
            node = self.node
        lines = []
        for field in get_fields(node):
            child_node = node[field]
            value = ""
            if hasattr(child_node, "value"):
                value = ": %s" % child_node.value()
            lines.append(indent + str(child_node) + value)
            if isinstance(child_node, libe57.StructureNode):
                lines += self.pretty_print(child_node, indent + "    ")
        return lines

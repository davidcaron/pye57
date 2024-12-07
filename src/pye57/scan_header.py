import numpy as np
from pyquaternion import Quaternion

from pye57 import libe57
from pye57.utils import get_fields, get_node

class ScanHeader:
    """Provides summary statistics for an individual lidar scan in an E57 file.

    Including the number of points, bounds and pose of the scan.
    """
    def __init__(self, scan_node):
        self.node = scan_node
        points = self.node["points"]
        self.point_fields = get_fields(libe57.StructureNode(points.prototype()))
        self.scan_fields = get_fields(self.node)

    @classmethod
    def from_data3d(cls, data3d):
        return [cls(scan) for scan in data3d]

    def has_pose(self):
        return self.node.isDefined("pose")

    @property
    def point_count(self):
        return self.points.childCount()

    @property
    def rotation_matrix(self) -> np.array:
        if "rotation" in self.node["pose"]:
            rot = np.array([[e.value() for e in row] for row in self.node["pose"]["rotation"]])
        else:
            rot = np.eye(3)
        return rot

    @property
    def rotation(self) -> np.array:
        if "rotation" in self.node["pose"]:
            rot = np.array([[e.value() for e in row] for row in self.node["pose"]["rotation"]])
        else:
            rot = np.eye(3)
        return rot.flatten()

    @property
    def translation(self):
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

    def __getitem__(self, item):
        return self.node[item]
    
    def get_coordinate_system(self, COORDINATE_SYSTEMS):
        if all(x in self.point_fields for x in COORDINATE_SYSTEMS.CARTESIAN.value):
            coordinate_system = COORDINATE_SYSTEMS.CARTESIAN
        elif all(x in self.point_fields for x in COORDINATE_SYSTEMS.SPHERICAL.value):
            coordinate_system = COORDINATE_SYSTEMS.SPHERICAL
        else:
            raise Exception(f"Scans coordinate system not supported, unsupported point field {self.point_fields}")
        return coordinate_system            

    @property
    def guid(self):
        return self["guid"].value()

    @property
    def temperature(self):
        try:
            return self["temperature"].value()
        except:
            return None

    @property
    def relativeHumidity(self):
        try:
            return self["relativeHumidity"].value()
        except:
            return None

    @property
    def atmosphericPressure(self):
        try:
            return self["atmosphericPressure"].value()
        except:
            return None

    @property
    def indexBounds(self):
        try:
            return self["indexBounds"]
        except:
            return None

    @property
    def rowMinimum(self):
        try:
            return self.indexBounds["rowMinimum"].value()
        except:
            return None

    @property
    def rowMaximum(self):
        try:
            return self.indexBounds["rowMaximum"].value()
        except:
            return None

    @property
    def columnMinimum(self):
        try:
            return self.indexBounds["columnMinimum"].value()
        except:
            return None

    @property
    def columnMaximum(self):
        try:
            return self.indexBounds["columnMaximum"].value()
        except:
            return None

    @property
    def returnMinimum(self):
        try:
            return self.indexBounds["returnMinimum"].value()
        except:
            return None

    @property
    def returnMaximum(self):
        try:
            return self.indexBounds["returnMaximum"].value()
        except:
            return None

    @property
    def intensityLimits(self):
        try:
            return self["intensityLimits"]
        except:
            return None

    @property
    def intensityMinimum(self):
        try:
            return self.intensityLimits["intensityMinimum"].value()
        except:
            return None

    @property
    def intensityMaximum(self):
        try:
            return self.intensityLimits["intensityMaximum"].value()
        except:
            return None

    @property
    def cartesianBounds(self):
        try:
            return self["cartesianBounds"]
        except:
            return None

    @property
    def xMinimum(self):
        try:
            return self.cartesianBounds["xMinimum"].value()
        except:
            return None

    @property
    def xMaximum(self):
        try:
            return self.cartesianBounds["xMaximum"].value()
        except:
            return None

    @property
    def yMinimum(self):
        try:
            return self.cartesianBounds["yMinimum"].value()
        except:
            return None

    @property
    def yMaximum(self):
        try:
            return self.cartesianBounds["yMaximum"].value()
        except:
            return None

    @property
    def zMinimum(self):
        try:
            return self.cartesianBounds["zMinimum"].value()
        except:
            return None

    @property
    def zMaximum(self):
        try:
            return self.cartesianBounds["zMaximum"].value()
        except:
            return None

    @property
    def sphericalBounds(self):
        try:
            return self["sphericalBounds"]
        except:
            return None

    @property
    def rangeMinimum(self):
        try:
            return self.sphericalBounds["rangeMinimum"].value()
        except:
            return None

    @property
    def rangeMaximum(self):
        try:
            return self.sphericalBounds["rangeMaximum"].value()
        except:
            return None

    @property
    def elevationMinimum(self):
        try:
            return self.sphericalBounds["elevationMinimum"].value()
        except:
            return None
    
    @property
    def elevationMaximum(self):
        try:
            return self.sphericalBounds["elevationMaximum"].value()
        except:
            return None
    
    @property
    def azimuthStart(self):
        try:
            return self.sphericalBounds["azimuthStart"].value()
        except:
            return None
    
    @property
    def azimuthEnd(self):
        try:
            return self.sphericalBounds["azimuthEnd"].value()
        except:
            return None
    
    @property
    def pose(self):
        try:
            return self["pose"]
        except:
            return None

    @property
    def acquisitionStart(self):
        try:
            return self["acquisitionStart"]
        except:
            return None

    @property
    def acquisitionStart_dateTimeValue(self):
        try:
            return self.acquisitionStart["dateTimeValue"].value()
        except:
            return None

    @property
    def acquisitionStart_isAtomicClockReferenced(self):
        try:
            return self.acquisitionStart["isAtomicClockReferenced"].value()
        except:
            return None

    @property
    def acquisitionEnd(self):
        try:
            return self["acquisitionEnd"]
        except:
            return None

    @property
    def acquisitionEnd_dateTimeValue(self):
        try:
            return self.acquisitionEnd["dateTimeValue"].value()
        except:
            return None

    @property
    def acquisitionEnd_isAtomicClockReferenced(self):
        try:
            return self.acquisitionEnd["isAtomicClockReferenced"].value()
        except:
            return None

    @property
    def pointGroupingSchemes(self):
        try:
            return self["pointGroupingSchemes"]
        except:
            return None

    @property
    def points(self):
        try:
            return self["points"]
        except:
            return None

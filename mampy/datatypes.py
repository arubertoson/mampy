"""
"""
import sys
import maya.api.OpenMaya as api


__all__ = ['get_line_line_intersection', 'BoundingBox', 'Point2D', 'Line3D']


EPS = sys.float_info.epsilon


def get_line_line_intersection(line1, line2):
    """
    Get the shortest line between two lines in 3D.
    ported from http://paulbourke.net/geometry/pointlineplane/
    """
    P1, P2 = line1
    P3, P4 = line2

    p13 = P1 - P3
    p43 = P4 - P3
    if (abs(p43.x) < EPS and abs(p43.y) < EPS and abs(p43.z) < EPS):
        return False

    p21 = P2 - P1
    if (abs(p21.x) < EPS and abs(p21.y) < EPS and abs(p21.z) < EPS):
        return False

    d1343 = p13.x * p43.x + p13.y * p43.y + p13.z * p43.z
    d4321 = p43.x * p21.x + p43.y * p21.y + p43.z * p21.z
    d1321 = p13.x * p21.x + p13.y * p21.y + p13.z * p21.z
    d4343 = p43.x * p43.x + p43.y * p43.y + p43.z * p43.z
    d2121 = p21.x * p21.x + p21.y * p21.y + p21.z * p21.z

    denom = d2121 * d4343 - d4321 * d4321
    if abs(denom) < EPS:
        return False
    numer = d1343 * d4321 - d1321 * d4343

    mua = numer / denom
    mub = (d1343 + d4321 * mua) / d4343

    pa = (P1.x + mua * p21.x), (P1.y + mua * p21.y), (P1.z + mua * p21.z)
    pb = (P3.x + mub * p43.x), (P3.y + mub * p43.y), (P3.z + mub * p43.z)
    return Line3D(api.MPoint(pa), api.MPoint(pb))


class BoundingBox(api.MBoundingBox):

    def __init__(self, *args, **kwargs):
        super(BoundingBox, self).__init__(*args, **kwargs)

        self.boxtype = '3D'

    @property
    def center(self):
        bbox = super(BoundingBox, self).center
        if self.boxtype == '2D':
            return Point2D(bbox)
        return bbox

    @property
    def max(self):
        bbox = super(BoundingBox, self).max
        if self.boxtype == '2D':
            return Point2D(bbox)
        return bbox

    @property
    def min(self):
        bbox = super(BoundingBox, self).min
        if self.boxtype == '2D':
            return Point2D(bbox)
        return bbox


class Point2D(api.MPoint):

    def __init__(self, *args, **kwargs):
        super(Point2D, self).__init__(*args, **kwargs)

    def __str__(self):
        return '({}, {})'.format(self.u, self.v)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.u, self.v)

    def __iter__(self):
        return iter(self.x, self.y)

    @property
    def u(self):
        return self.x

    @property
    def v(self):
        return self.y


class Line3D(object):

    def __init__(self, point1, point2):
        self.p1 = point1
        self.p2 = point2
        self._vec1 = api.MVector(point1)
        self._vec2 = api.MVector(point2)
        self._vec = None

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.p1, self.p2)

    def __str__(self):
        return '({}, {})'.format(self.p1, self.p2)

    def __iter__(self):
        return iter([self.p1, self.p2])

    @property
    def vector(self):
        if self._vec is None:
            self._vec = self._vec2 - self._vec1
        return self._vec

    def sum(self):
        return self._vec1 + self._vec2

    def length(self):
        return self._vec.length()

    def angle(self, other):
        return self._vec.angle(other)

    def shortest_line_to_other(self, other):
        return get_line_line_intersection(self, other)

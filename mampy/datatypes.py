
import maya.api.OpenMaya as api


__all__ = ['BoundingBox', 'Point2D']


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

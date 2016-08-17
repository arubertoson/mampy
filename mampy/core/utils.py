

import maya.api.OpenMaya as api


def get_average_vert_normal(normals, *args):
    vec = api.MVector()
    for v in args:
        vec += normals[v]
    return vec / len(args)


class IndexDict(dict):
    """
    Container object for points bound by dictionary
    """
    def __str__(self):
        return '{}'.format(list(self))

    def __iter__(self):
        return self.itervalues()

    def __contains__(self, key):
        return key in self.values()

    def has_index(self, index):
        return index in self.keys()

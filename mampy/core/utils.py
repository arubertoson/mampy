"""
"""
import itertools


def get_average_vert_normal(normals, *args):
    try:
        cls = normals[0].__class__
    except KeyError:
        cls = next(iter(normals)).__class__

    object = cls()
    args = args[0] if len(args) == 1 else args
    for v in args:
        object += normals[v]
    return object / len(args)


class IndicesDict(dict):
    """
    Container object for points bound by dictionary
    """
    def __iter__(self):
        return iter(set(itertools.chain(*self.itervalues())))

    def __contains__(self, key):
        return key in iter(self)

    def has_index(self, index):
        return index in self.keys()


class ObjectDict(IndicesDict):
    def __iter__(self):
        return self.itervalues()

"""
Tests for mampy.core.cache module
"""

from mampy.core import cache


class BoundingBoxStub(object):
    pass


class NormalsStub(object):
    pass


class MeshStub(object):
    pass


class Indexed(object):
    pass


WORLD, OBJECT = xrange(2)


class ComponentMock(object):

    @cache.cached_property
    def indexed(self):
        return Indexed()

    @cache.memoize_property
    def mesh(self):
        return MeshStub()

    @mesh.setter
    def mesh(self, value):
        """
        """

    @cache.memoize
    def points(self, space):
        return list(xrange(10))

    @cache.memoize
    def boundingbox(self, space):
        return BoundingBoxStub()

    @cache.memoize
    def normals(self, space):
        return NormalsStub()

    @cache.invalidate_instance_cache
    def update(self):
        pass


class ListMock(object):

    @cache.cache_MList_object
    def __getitem__(self, key):
        return ComponentMock()

    @cache.cache_MList_object(action=cache.COPY)
    def copy(self):
        return self.__class__()

    @cache.cache_MList_object(action=cache.POP)
    def pop(self, key):
        pass

    @cache.invalidate_instance_cache
    def clear(self):
        pass


def test_cache_list_object_cache_result():
    lmock = ListMock()
    lmock[0]
    assert hasattr(lmock, '_cache')
    assert 0 in lmock._cache


def test_cache_list_object_pop_result_from_cache():
    lmock = ListMock()
    lmock[0]
    lmock.pop(0)
    assert 0 not in lmock._cache


def test_cache_list_object_copy_to_new_instance():
    lmock = ListMock()
    lmock[0]
    copy_lmock = lmock.copy()
    assert hasattr(copy_lmock, '_cache')
    assert 0 in copy_lmock._cache


def test_memoize_cache_caching_results():
    cmock = ComponentMock()
    points = cmock.points(space=WORLD)
    objects = cmock.points(space=OBJECT)

    assert hasattr(cmock.points, '_cache')
    assert cmock.points(space=WORLD) is points
    assert cmock.points(space=OBJECT) is objects


def test_cached_property_caching_result():
    cmock = ComponentMock()
    indexed = cmock.indexed
    assert indexed is cmock.indexed
    assert cmock.__dict__['indexed'] is indexed


def test_memoize_property_caching_result():
    cmock = ComponentMock()
    mesh = cmock.mesh
    assert cmock.mesh is mesh


def test_memoize_property_set_value():
    cmock = ComponentMock()
    cmock.mesh = 'Mesh'
    assert cmock.mesh == 'Mesh'


def test_invalidate_instance_cache_on_object_instance():
    lmock = ListMock()
    for i in xrange(10):
        lmock[i]
    assert len(lmock._cache) == 10
    lmock.clear()
    assert not lmock._cache


def test_invalidate_instance_cache_on_object_methods_caches():
    cmock = ComponentMock()

    methods = [cmock.normals, cmock.points, cmock.boundingbox]
    for each in [WORLD, OBJECT]:
        for method in methods:
            method(space=each)

    mesh = cmock.mesh
    assert cmock.mesh
    for method in methods:
        assert method._cache

    cmock.update()
    for method in methods:
        assert not method._cache
    assert not cmock._cache

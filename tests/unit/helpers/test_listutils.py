"""
Test for mampy.helpers.listutils
"""
import copy

from mampy.helpers import listutils as u


class ObjectList(object):

    def __init__(self):
        self._elements = range(100)

    @u.cache_object
    def __getitem__(self, key):
        return self._elements[key]

    @u.cache_copy
    def __copy__(self):
        return self.__class__()

    @u.cache_clear_objects
    def extend(self, other):
        self._elements.extend(other)

    @u.cache_pop_object
    def pop(self, item):
        return self._elements.pop(item)


def test_cache_object_listutils_cache_return_object_from_index():
    mlist = ObjectList()
    assert mlist[2] == mlist[2]
    assert mlist.__cache


def test_cache_pop_object_listutils_cache_pop_item_from_cache():
    mlist = ObjectList()
    init_cache = mlist[10]
    value = mlist.pop(10)
    assert value == init_cache
    assert value not in mlist.__cache


def test_cache_clear_objects_listutils_clear_chache():
    mlist = ObjectList()
    cached = [mlist[i] for i in xrange(10, 14)]
    assert all(i in mlist.__cache for i in cached)

    mlist.extend(list(xrange(10)))
    assert not mlist.__cache


def test_cache_copy_listutils_copy_cache_atttribute_to_other():
    mlist = ObjectList()
    assert mlist[2] == mlist[2]
    result = copy.copy(mlist)
    assert mlist.__cache == result.__cache


def test_is_track_order_set_false():
    assert u.is_track_order_set() is False


def test_is_track_order_set_true():
    u.cmds.selectPref(trackSelectionOrder=True)
    assert u.is_track_order_set() is True


def test_need_ordered_selection_set_true():
    assert u.need_ordered_selection_set(
        ['fl', 'flatten', 'os', 'orderedSelection'])


def test_need_ordered_selection_set_true():
    assert not u.need_ordered_selection_set(['some', 'other', 'setting'])


def test_is_component_string_return_true():
    assert u.is_component_string('pCube.f[14]')


def test_is_component_string_return_false():
    assert u.is_component_string('pCube')


def test_is_component_return_true(maya_component):
    with maya_component() as dag:
        assert u.is_component(dag)


def test_is_component_return_false(maya_dagpath):
    with maya_dagpath() as dag:
        assert not u.is_component(dag)


def test_get_mayalist_from_iterable_return_valid_mlist(xcubes):
    mlist = u.get_mayalist_from_iterable(list(xcubes(10)))
    assert mlist.length() == 10


def test_get_component_from_input(xcubes):
    assert isinstance(u.get_component_from_input(list(xcubes).pop()), tuple)

# -*- coding: utf-8 -*-
"""
mampy.core.cache

This module contains the cache funcionality for mampy objects.
"""
import inspect
import functools

(CACHE, POP, COPY) = range(3)


def mlist_object(method=None, action=CACHE):
    """Caches a return object from mampy list objects using index as key.

    Can be called with mode:
        CACHE: cache {index: object}
        POP: remove cached object at index
        CLEAR: clear all cached objects
        COPY: copy cache from one list object to other
    """

    def decorator(method):
        wrapper = _cache_mlist_object(method, action)
        return functools.update_wrapper(wrapper, method)

    if method:
        return decorator(method)
    else:
        return decorator


def _cache_mlist_object(method, action):

    def pop(cache, index):
        cache.pop(index, None)

    def copy(self, *args, **kw):
        result = method(self, *args, **kw)
        result._cache = self._cache
        return result

    def wrapper(self, *args, **kw):
        try:
            cache = self._cache
        except AttributeError:
            cache = self._cache = {}

        if action == POP:
            pop(cache, args[0])
            res = method(self, *args, **kw)
        elif action == COPY:
            res = copy(self, *args, **kw)
        else:
            key = args[0]
            try:
                res = cache[key]
            except KeyError:
                res = cache[key] = method(self, *args, **kw)
            except TypeError:
                res = method(self, *args, **kw)
        return res

    return wrapper


def memoize(func):
    cache = func._cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kw):
        key = (func, args, frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = func(*args, **kw)
        except TypeError:
            res = func(*args, **kw)
        return res

    def clear():
        cache.clear()

    wrapper.clear_cache = clear
    return wrapper


class property(object):
    """cached property acts as a lazy attribute

    The property will replace the underlying attribute access, meaning
    the property will only be called once, after that it has been replaced
    and can't be invalidated.
    """

    def __init__(self, method):
        self.__doc__ = getattr(method, '__doc__')
        self.method = method

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.method.__name__] = self.method(obj)
        return value


class memoize_property(property):
    """Memoize for property to support normal property behaviour

    Can be invalidated
    """

    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):
        self.method = method
        self.cache_name = '_{}'.format(self.method.__name__)

        doc = doc or method.__doc__
        super(memoize_property, self).__init__(
            fget=fget, fset=fset, fdel=fdel, doc=doc)

    def __get__(self, obj, cls):
        if obj is None:
            return self

        cache = self.getcache(obj)
        try:
            result = cache[self.cache_name]
        except KeyError:
            result = cache[self.cache_name] = self.method(obj)
        return result

    def __set__(self, obj, value):
        if obj is None:
            raise AttributeError

        cache = self.getcache(obj)
        cache[self.cache_name] = value

    def getcache(self, obj):
        try:
            result = obj._cache
        except AttributeError:
            result = obj._cache = {}
        return result

    def setter(self, fset):
        return self.__class__(self.method, self.fget, fset, self.fdel,
                              self.__doc__)


def invalidate_instance_cache(method):
    """Invalidates caches on given instance methods or functions

    Inspects method for a _cache attribute, if it can locate one invalidate it.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kw):
        for name, each in inspect.getmembers(self, predicate=inspect.ismethod):
            if '_cache' in each.__dict__:
                each.clear_cache()

        if hasattr(self, '_cache'):
            self._cache.clear()
        return method(self, *args, **kw)

    return wrapper

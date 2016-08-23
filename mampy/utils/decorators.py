"""
"""
try:
    from contextlib import ContextDecorator
except ImportError:
    ContextDecorator = None

import warnings
from functools import wraps
from contextlib import contextmanager

from maya import cmds

import mampy
from .masks import get_active_flags_in_mask, get_active_select_mode


__all__ = ['ContextDecorator', 'object_mode', 'component_mode', 'undoable', 'repeatable',
           'select_keep']


if ContextDecorator is None:
    class ContextDecorator(object):
        "A base class or mixin that enables context managers to work as decorators."

        def refresh_cm(self):
            """Returns the context manager used to actually wrap the call to the
            decorated function.

            The default implementation just returns *self*.

            Overriding this method allows otherwise one-shot context managers
            like _GeneratorContextManager to support use as decorators via
            implicit recreation.

            DEPRECATED: refresh_cm was never added to the standard library's
                        ContextDecorator API
            """
            warnings.warn("refresh_cm was never added to the standard library",
                          DeprecationWarning)
            return self._recreate_cm()

        def _recreate_cm(self):
            """Return a recreated instance of self.

            Allows an otherwise one-shot context manager like
            _GeneratorContextManager to support use as
            a decorator via implicit recreation.

            This is a private interface just for _GeneratorContextManager.
            See issue #11647 for details.
            """
            return self

        def __call__(self, func):
            @wraps(func)
            def inner(*args, **kwds):
                with self._recreate_cm():
                    return func(*args, **kwds)
            return inner


@contextmanager
def object_mode():
    """
    Perform a task in object mode then restores mode to previous.
    """
    try:
        object_mode = cmds.selectMode(q=True, object=True)
        if not object_mode:
            current_mode = get_active_select_mode()
            cmds.selectMode(object=True)

        object_flags = get_active_flags_in_mask(object=True)
        cmds.selectType(allObjects=True)
        yield
    finally:
        cmds.selectType(**{k: True for k in object_flags})
        if not object_mode:
            cmds.selectMode(**{current_mode: True})


@contextmanager
def component_mode():
    """
    Perform a task in component mode then restore to previous mode.
    """
    try:
        component_mode = cmds.selectMode(q=True, component=True)
        if not component_mode:
            current_mode = get_active_select_mode()
            cmds.selectMode(component=True)

        component_flags = get_active_flags_in_mask()
        cmds.selectType(allCoponents=True)
        yield
    finally:
        cmds.selectType(**{k: True for k in component_flags})
        if not component_mode:
            cmds.selectMode(**{current_mode: True})


class undoable(ContextDecorator):
    def __enter__(self):
        cmds.undoInfo(openChunk=True)
        return self

    def __exit__(self, *exc):
        cmds.undoInfo(closeChunk=True)


def repeatable(func):
    """Decorator for making python functions repeatable."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        parameters = ''
        if args:
            parameters = ', '.join([str(i) for i in args])
        if kwargs:
            kwargs_parameters = [
                '='.join([str(key), str(value)])
                for key, value in kwargs.iteritems()
            ]
            parameters += ', '.join(kwargs_parameters)

        cmds.evalDeferred('import {}'.format(func.__module__))
        command = 'python("{}.{}({})")'.format(func.__module__, func.__name__, parameters)
        result = func(*args, **kwargs)
        try:
            cmds.repeatLast(ac=command, acl=func.__name__)
        except RuntimeError:
            pass
        return result
    return wrapper


class select_keep(ContextDecorator):
    """
    Context Decorator that restore selection after call.
    """
    def __enter__(self):
        self.slist = cmds.ls(sl=True)
        self.hlist = cmds.ls(hl=True)

        if self.hlist:
            cmds.hilite(self.hlist, toggle=True)

    def __exit__(self, *args):
        cmds.select(self.slist, r=True)
        if self.hlist:
            cmds.hilite(self.hlist)

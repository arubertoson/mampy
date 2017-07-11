"""
"""
from .history import History
from .varlists import OptionVar, MelGlobals
from .draggerctx import AbstractDraggerCtx
from .masks import get_active_flags_in_mask, get_active_select_mode, SelectionMask
from .dagnode import get_outliner_index, get_object_under_cursor, get_objects_in_view

from .decorators import *

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

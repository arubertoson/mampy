# -*- coding: utf-8 -*-
"""
mampy.core.exception

Exceptions and Warnings for Mampy and scripts utilizing Mampy.
"""
import inspect
from maya import cmds


class MampyException(Exception):

    def __str__(self):
        if not self.args:
            return inspect.getdoc(self)
        return super(MampyException, self).__str__()


class OrderedSelectionsNotSet(MampyException):
    """Ordered selection not set in Maya preferences."""


class ObjectDoesNotExist(MampyException):
    """Could not find wanted object in scene."""


# Warnings


class MampyWarning(Warning):
    """Base warning for Mampy."""


class NothingSelected(MampyWarning):
    """Nothing is selected."""


class InvalidSelection(MampyWarning):
    """An invalid selection was made."""


class InvalidComponentSelection(MampyWarning):
    """Invalid Component object for operation"""


def warning(message, warningtype):
    frameinfo = inspect.getframeinfo(inspect.currentframe())
    cmds.warning('{}: {}, at line {}, in "{}"'.format(
        warningtype.__name__.replace('Warning', ''), message, frameinfo.lineno,
        frameinfo.filename))

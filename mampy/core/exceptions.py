"""
"""
import inspect


class AbstractException(Exception):
    def __str__(self):
        if not self.args:
            return inspect.getdoc(self)
        return super(AbstractException, self).__str__()


class NothingSelected(AbstractException):
    """Nothing is selected."""


class InvalidSelection(AbstractException):
    """An invalid selection was made."""


class InvalidComponentSelection(AbstractException):
    """Invalid Component object for operation"""


class OrderedSelectionsNotSet(AbstractException):
    """Ordered selection not set in Maya preferences."""


class ObjecetDoesNotExist(AbstractException):
    """Could not find wanted object in scene."""

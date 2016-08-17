"""
"""
import logging


logger = logging.getLogger(__name__)


class History(object):
    """
    Stores current jump history
    """
    LIST_LIMIT = 20
    LIST_TRIMMED_SIZE = 15

    def __init__(self):
        self.history_list = []

        self.current_item = 0
        self.key_counter = 0

    def __len__(self):
        return len(self.history_list)

    @property
    def current_element(self):
        return self.history_list[self.current_item]

    def push(self, element):
        """
        Push element into history.
        """
        self.history_list.append(element)
        self.trim_selections()

        logger.debug(self.history_list)

    def jump_back(self):
        """
        Return element behind of active element in history_list.
        """
        if self.current_item == 0:
            self.current_item = -1

        if self.current_item == -len(self.history_list):
            return None
        self.current_item -= 1

    def jump_forward(self):
        """
        Return element in front of active element in history_list.
        """
        if self.history_list == []:
            return None

        # Already at the front
        if self.current_item >= -1:
            return None
        self.current_item += 1

    def trim_selections(self):
        """
        Trim everything too old when reaching list limit.
        """
        if len(self.history_list) > self.LIST_LIMIT:
            del self.history_list[:len(self.history_list) - self.LIST_TRIMMED_SIZE]


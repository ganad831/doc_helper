"""Navigation module for tracking UI navigation state.

This module provides framework-independent navigation state tracking with
history support for back/forward navigation through entities, groups, and fields.
"""

from doc_helper.application.navigation.navigation_entry import NavigationEntry
from doc_helper.application.navigation.navigation_history import NavigationHistory

__all__ = [
    "NavigationEntry",
    "NavigationHistory",
]

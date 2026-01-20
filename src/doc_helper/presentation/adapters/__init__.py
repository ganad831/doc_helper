"""Presentation layer adapters.

Adapters bridge between domain/application layer and PyQt6 UI framework.
"""

from doc_helper.presentation.adapters.history_adapter import HistoryAdapter
from doc_helper.presentation.adapters.qt_translation_adapter import QtTranslationAdapter

__all__ = [
    "HistoryAdapter",
    "QtTranslationAdapter",
]

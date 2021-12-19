#!/usr/bin/env python3

# Standard libraries.
import collections.abc

# External dependencies.
import PySide6.QtGui
import pytest


@pytest.fixture
def q_gui_application(
    pyside6: None,
) -> collections.abc.Iterator[PySide6.QtGui.QGuiApplication]:
    del pyside6
    q_gui_application = PySide6.QtGui.QGuiApplication()
    try:
        yield q_gui_application
    finally:
        q_gui_application.shutdown()

#!/usr/bin/env python3

# Standard libraries.
import collections.abc

# External dependencies.
import PySide6.QtWidgets
import pytest


@pytest.fixture
def q_application(
    pyside6: None,
) -> collections.abc.Iterator[PySide6.QtWidgets.QApplication]:
    del pyside6
    q_application = PySide6.QtWidgets.QApplication()
    try:
        yield q_application
    finally:
        q_application.shutdown()

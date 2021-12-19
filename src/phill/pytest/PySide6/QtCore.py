#!/usr/bin/env python3

# Standard libraries.
import collections.abc
import pathlib

# External dependencies.
import PySide6.QtCore
import pytest

# Internal modules.
import phill.PySide6.QtCore


@pytest.fixture(name="pyside6")
def pyside6_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> collections.abc.Iterator[None]:
    """
    Set up ``PySide2`` to not use user settings.

    Test environments are typically not graphical.
    So the Qt Platform Abstraction used is set to ``offscreen``.

    PySide2 also reads runtime data from ``XDG_RUNTIME_DIR``.
    This is overridden to not use user data.
    """
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    try:
        yield
    finally:
        q_core_application = PySide6.QtCore.QCoreApplication.instance()
        if q_core_application is not None:
            try:
                phill.PySide6.QtCore.process_events()
                phill.PySide6.QtCore.process_deferred_delete_events()
            finally:
                q_core_application.shutdown()


@pytest.fixture
def q_core_application(
    pyside6: None,
) -> collections.abc.Iterator[PySide6.QtCore.QCoreApplication]:
    del pyside6
    q_core_application = PySide6.QtCore.QCoreApplication()
    try:
        yield q_core_application
    finally:
        q_core_application.shutdown()

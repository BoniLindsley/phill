#!/usr/bin/env python3

# External dependencies.
import PySide6.QtGui

# Internal packages.
import phill.PySide6.QtGui


def test_q_icon_from_specified_theme_can_construct_create_icon(
    q_gui_application: PySide6.QtGui.QGuiApplication,
) -> None:
    del q_gui_application
    phill.PySide6.QtGui.q_icon_from_specified_theme("a", "b")


def test_q_icon_from_theme_can_construct_create_icon(
    q_gui_application: PySide6.QtGui.QGuiApplication,
) -> None:
    del q_gui_application
    phill.PySide6.QtGui.q_icon_from_theme("a")

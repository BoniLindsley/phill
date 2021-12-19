#!/usr/bin/env python3

# External dependencies.
import PySide6.QtGui


class TestQGuiApplication:
    def test_cleans_up_q_gui_application(
        self, q_gui_application: PySide6.QtGui.QGuiApplication
    ) -> None:
        del q_gui_application

    def test_another_test_can_create_another_application(
        self, q_gui_application: PySide6.QtGui.QGuiApplication
    ) -> None:
        del q_gui_application

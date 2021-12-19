#!/usr/bin/env python3

# External dependencies.
import PySide6.QtWidgets


class TestQApplication:
    def test_cleans_up_q_gui_application(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application

    def test_another_test_can_create_another_application(
        self, q_application: PySide6.QtWidgets.QApplication
    ) -> None:
        del q_application
